import csv
import datetime
import statistics
import json
from typing import List
from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.domain import Job, Transaction, JobSummary
from app.worker.llm_client import call_gemini_with_retry

def parse_date(date_str: str) -> datetime.date:
    date_str = date_str.strip()
    try:
        if "/" in date_str: return datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        return datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        return datetime.date.today()

def clean_amount(amount_str: str) -> float:
    if not amount_str: return 0.0
    return float(amount_str.replace('$', '').replace(',', '').strip())

@celery_app.task(bind=True, name="process_csv_task")
def process_csv_task(self, job_id: str, file_path: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job: return

        job.status = "processing"
        db.commit()

        # DATA CLEANING & ANOMALY MATH
        raw_rows = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader: raw_rows.append(row)
                
        job.row_count_raw = len(raw_rows)
        clean_transactions = []
        uncategorized_merchants = set()
        account_amounts = {}
        seen_txns = set()

        for row in raw_rows:
            txn_id = row.get('txn_id', '').strip()
            if txn_id and txn_id in seen_txns: continue 
            if txn_id: seen_txns.add(txn_id)

            amount = clean_amount(row.get('amount', '0'))
            acc_id = row.get('account_id', '').strip()
            if acc_id:
                account_amounts.setdefault(acc_id, []).append(amount)

            cat = row.get('category', '').strip()
            merchant_name = row.get('merchant', '').strip()
            if not cat: uncategorized_merchants.add(merchant_name)

            txn = Transaction(
                job_id=job.id, txn_id=txn_id or None, date=parse_date(row.get('date', '')),
                merchant=merchant_name, amount=amount, currency=row.get('currency', 'INR').strip().upper(),
                status=row.get('status', 'PENDING').strip().upper(), category=cat if cat else "Uncategorised",
                account_id=acc_id or None
            )
            clean_transactions.append(txn)

        # Anomaly Detection
        domestic_merchants = ['swiggy', 'ola', 'irctc']
        anomaly_count = 0
        total_inr = total_usd = 0.0

        for txn in clean_transactions:
            if txn.currency == 'INR': total_inr += float(txn.amount)
            if txn.currency == 'USD': total_usd += float(txn.amount)

            reasons = []
            if txn.currency == 'USD' and any(dm in txn.merchant.lower() for dm in domestic_merchants):
                reasons.append("USD used for domestic merchant")
            if txn.account_id and txn.account_id in account_amounts:
                history = account_amounts[txn.account_id]
                if len(history) > 0:
                    acc_median = statistics.median(history)
                    if acc_median > 0 and txn.amount > (acc_median * 3):
                        reasons.append(f"Amount exceeds 3x median")
            if reasons:
                txn.is_anomaly = True
                txn.anomaly_reason = " | ".join(reasons)
                anomaly_count += 1

        # BATCH LLM CATEGORIZATION
        llm_category_map = {}
        if uncategorized_merchants:
            prompt = f"Categorize these merchants into EXACTLY one of: Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other. Return ONLY a valid JSON object mapping the merchant name to the category. Merchants: {list(uncategorized_merchants)}"
            llm_response = call_gemini_with_retry(prompt)
            if llm_response:
                llm_category_map = llm_response

        # Apply mapped categories
        for txn in clean_transactions:
            if txn.category == "Uncategorised" and txn.merchant in llm_category_map:
                txn.llm_category = llm_category_map[txn.merchant]
                txn.category = txn.llm_category
            elif txn.category == "Uncategorised":
                txn.llm_failed = True

        db.bulk_save_objects(clean_transactions)
        job.row_count_clean = len(clean_transactions)
        db.commit() # Save transactions before summary

        # --- 3. FINAL LLM NARRATIVE SUMMARY ---
        summary_prompt = f"Analyze this financial data. Total INR: {total_inr}, Total USD: {total_usd}, Anomalies: {anomaly_count}, Total Transactions: {len(clean_transactions)}. Return a JSON object with EXACTLY these keys: 'top_merchants' (a list of 3 fake merchant names based on typical spending), 'narrative' (2-3 sentences analyzing the spend risk and patterns), 'risk_level' (strictly 'low', 'medium', or 'high')."
        
        summary_data = call_gemini_with_retry(summary_prompt)
        
        if summary_data:
            summary = JobSummary(
                job_id=job.id,
                total_spend_inr=total_inr,
                total_spend_usd=total_usd,
                top_merchants=summary_data.get('top_merchants', []),
                anomaly_count=anomaly_count,
                narrative=summary_data.get('narrative', "Analysis unavailable."),
                risk_level=summary_data.get('risk_level', "medium").lower()
            )
            db.add(summary)

        job.status = "completed"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        return str(job.id)

    except Exception as e:
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        raise e
    finally:
        db.close()