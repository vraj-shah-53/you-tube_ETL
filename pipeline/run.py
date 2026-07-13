import argparse
import sys
import time
from pathlib import Path

# Add project root directory to path to support running from anywhere
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from pipeline.extract import extract
from pipeline.transform import transform
from pipeline.load import load

def run_pipeline(query: str = None, max_results: int = None, force_mock: bool = False):
    """
    Orchestrates the ETL Pipeline steps.
    """
    start_time = time.time()
    print("=" * 60)
    print("           YOUTUBE ETL PIPELINE RUN STARTED")
    print("=" * 60)

    # Use defaults if arguments are not supplied
    api_key = "" if force_mock else config.YOUTUBE_API_KEY
    search_query = query if query else config.SEARCH_QUERY
    max_res = max_results if max_results else config.MAX_RESULTS
    db_path = config.DB_PATH

    print(f"[ETL] Target Database: {db_path}")
    print(f"[ETL] Search Query: '{search_query}' (Limit: {max_res})")
    if force_mock:
        print("[ETL] Run mode: Forced MOCK")
    elif api_key:
        print("[ETL] Run mode: YouTube API")
    else:
        print("[ETL] Run mode: MOCK (No API Key found)")

    # 1. EXTRACT
    extract_start = time.time()
    try:
        raw_videos, raw_channels = extract(api_key, search_query, max_res)
    except Exception as e:
        print(f"[ETL] Extraction stage failed: {e}")
        sys.exit(1)
    extract_duration = time.time() - extract_start
    print(f"[ETL] Extraction completed in {extract_duration:.2f} seconds.")

    # 2. TRANSFORM
    transform_start = time.time()
    try:
        df_videos, df_channels = transform(raw_videos, raw_channels)
    except Exception as e:
        print(f"[ETL] Transformation stage failed: {e}")
        sys.exit(1)
    transform_duration = time.time() - transform_start
    print(f"[ETL] Transformation completed in {transform_duration:.2f} seconds.")

    # 3. LOAD
    load_start = time.time()
    try:
        load(df_videos, df_channels, db_path)
    except Exception as e:
        print(f"[ETL] Loading stage failed: {e}")
        sys.exit(1)
    load_duration = time.time() - load_start
    print(f"[ETL] Loading completed in {load_duration:.2f} seconds.")

    total_duration = time.time() - start_time
    print("=" * 60)
    print(f"          ETL PIPELINE RUN COMPLETED SUCCESSFULLY")
    print(f"          Total Time: {total_duration:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Data ETL Pipeline Runner")
    parser.add_argument("--query", type=str, help="Search query to fetch videos for (overrides .env)")
    parser.add_argument("--max-results", type=int, help="Maximum number of videos to fetch (overrides .env)")
    parser.add_argument("--mock", action="store_true", help="Force mock data generation (ignores API Key)")
    
    args = parser.parse_args()
    run_pipeline(
        query=args.query,
        max_results=args.max_results,
        force_mock=args.mock
    )
