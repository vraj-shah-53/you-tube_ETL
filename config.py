import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Create directories if they do not exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# YouTube Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "data engineering")
try:
    MAX_RESULTS = int(os.getenv("MAX_RESULTS", "50"))
except ValueError:
    MAX_RESULTS = 50

# Database Configuration
# Default to data/youtube_data.db relative to workspace root
DEFAULT_DB_PATH = str(DATA_DIR / "youtube_data.db")
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

# Ensure db directory exists
db_dir = Path(DB_PATH).parent
db_dir.mkdir(parents=True, exist_ok=True)

print(f"[CONFIG] Base Directory: {BASE_DIR}")
print(f"[CONFIG] Database Path: {DB_PATH}")
print(f"[CONFIG] Search Query: '{SEARCH_QUERY}' (Max Results: {MAX_RESULTS})")
if YOUTUBE_API_KEY:
    print("[CONFIG] YouTube API Key: Loaded")
else:
    print("[CONFIG] YouTube API Key: Not found. ETL will run in MOCK mode.")
