# Transaction Risk Analyzer

An asynchronous, scalable data processing pipeline that ingests CSV financial transactions, cleans the data, runs anomaly detection, and utilizes an LLM (Google Gemini) for merchant categorization and risk summarization.

##  Architecture Overview
- **Web Layer:** FastAPI (Handles routing and instant HTTP responses)
- **Message Broker:** Redis (Queues tasks for background processing)
- **Worker Layer:** Celery (Executes heavy CSV parsing and LLM API calls)
- **Database:** PostgreSQL (Stores relational data and strict JSON summaries)

##  Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/samruddhi-t12/transaction_pipeline.git
cd transaction_pipeline
```
2. Configure Environment Variables
You must provide a Google Gemini API Key for the LLM categorization to work.

```Bash
# Copy the template environment file
cp .env.example .env
```
Open the .env file and replace put_your_gemini_api_key_here with your actual Google Gemini API key.

**3. Spin up the Infrastructure**
Build and start all containers in the background:

```Bash
docker compose up -d --build
```
Note: This will expose the FastAPI application on http://localhost:8000.

## API Usage (cURL Commands)
**1. Upload a CSV (Triggers Background Job)**
Replace @your_test_file.csv with the path to a valid transaction CSV.

```Bash
curl -X POST "http://localhost:8000/jobs/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_test_file.csv"
```
Returns a job_id.

**2. Check Job Status**
Replace {job_id} with the ID from the upload step.

```Bash
curl -X GET "http://localhost:8000/jobs/{job_id}/status"
```
**3. Fetch the AI Summary**
Once the status is completed, retrieve the structured JSON summary.

```Bash
curl -X GET "http://localhost:8000/jobs/{job_id}/summary"
```
**4. List and Filter Jobs**
```Bash
# View all jobs
curl -X GET "http://localhost:8000/jobs"

# View only completed jobs
curl -X GET "http://localhost:8000/jobs?status=completed"
```
