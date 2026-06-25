from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    #app settings
    PROJECT_NAME:str
    ENVIRONMENT:str
    DEBUG:bool

    #db and redis
    DATABASE_URL:str
    REDIS_URL:str

    #External APIs
    GEMINI_API_KEY:str
    #look for .env in root folder
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")

settings=Settings()


