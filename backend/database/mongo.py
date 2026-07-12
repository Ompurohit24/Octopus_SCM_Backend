from pymongo import MongoClient
import os
from dotenv import load_dotenv
from backend.config.settings import settings
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")



client = MongoClient(settings.MONGODB_URI)

db = client[settings.DATABASE_NAME]