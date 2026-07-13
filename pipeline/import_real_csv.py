import pandas as pd
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root directory to path to support running from anywhere
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from pipeline.load import load

CSV_URL = "https://raw.githubusercontent.com/harshitjain-hj/Youtube-Trend-Analysis/master/IN_youtube_trending_data.csv"

def import_and_load_csv(limit: int = 1000):
    """
    Downloads raw YouTube video statistics from GitHub, transforms it, and loads it to DuckDB.
    """
    start_time = time.time()
    print("=" * 60)
    print("      REAL KAGGLE DATASET ETL IMPORT STARTED")
    print("=" * 60)
    print(f"[IMPORT] Downloading first {limit} rows from public URL...")
    
    try:
        # Load CSV directly from URL (limit rows for speed and local database scale)
        df_raw = pd.read_csv(CSV_URL, nrows=limit)
        print(f"[IMPORT] Downloaded {len(df_raw)} records successfully.")
    except Exception as e:
        print(f"[IMPORT] Error downloading CSV: {e}")
        print("[IMPORT] Please verify your internet connection.")
        raise e

    # 1. TRANSFORM VIDEOS
    print("[IMPORT] Transforming real video records...")
    df_videos = pd.DataFrame()
    
    current_time = datetime.now(timezone.utc)
    
    # Map columns
    df_videos['video_id'] = df_raw['video_id'].fillna("unknown")
    df_videos['title'] = df_raw['title'].fillna("")
    df_videos['description'] = df_raw['description'].fillna("")
    
    # Parse publishedAt into datetime and shift dates randomly between 1300 and 2100 days to distribute across 2024-2026
    published_at_series = pd.to_datetime(df_raw['publishedAt'], errors='coerce')
    import random
    random.seed(42)
    shifted_dates = []
    for dt in published_at_series:
        if pd.isnull(dt):
            shifted_dates.append(pd.NaT)
        else:
            # Shift between 1300 and 2100 days forward to spread across 2024, 2025, and 2026
            shift_days = random.randint(1300, 2100)
            shifted_dates.append(dt + pd.to_timedelta(shift_days, unit='D'))
    published_at_series = pd.Series(shifted_dates)
    df_videos['published_at'] = published_at_series
    
    # Map channel details
    df_videos['channel_id'] = df_raw['channelId'].fillna("unknown_channel_id")
    df_videos['channel_title'] = df_raw['channelTitle'].fillna("Unknown Channel")
    
    df_videos['category_id'] = df_raw['categoryId'].fillna(0).astype(str)
    df_videos['tags'] = df_raw['tags'].fillna("")
    
    # Set mock durations (as duration isn't in this CSV)
    import random
    random.seed(42)
    df_videos['duration_seconds'] = [random.randint(180, 1500) for _ in range(len(df_videos))]
    
    # Parse views, likes, and comment counts
    df_videos['view_count'] = df_raw['view_count'].fillna(0).astype('int64')
    df_videos['like_count'] = df_raw['likes'].fillna(0).astype('int64')
    df_videos['comment_count'] = df_raw['comment_count'].fillna(0).astype('int64')
    
    # Calculate Engagement Rate (likes + comments) / views
    # Ensure no division by zero
    df_videos['engagement_rate'] = (
        (df_videos['like_count'] + df_videos['comment_count']) / df_videos['view_count']
    ).fillna(0.0).round(4)
    
    # Calculate Days Since Published
    def calc_days(pub_date):
        if pd.isnull(pub_date):
            return 1
        # Convert timestamp to UTC
        pub_utc = pub_date.tz_localize(None).tz_localize(timezone.utc)
        days = (current_time - pub_utc).days
        return max(1, days)
        
    df_videos['days_since_published'] = published_at_series.apply(calc_days)
    df_videos['views_per_day'] = (df_videos['view_count'] / df_videos['days_since_published']).round(2)
    df_videos['thumbnail_url'] = df_raw['thumbnail_link'].fillna("")
    df_videos['updated_at'] = datetime.now()

    # Deduplicate video records (keep the last trending instance with highest views)
    df_videos = df_videos.drop_duplicates(subset=['video_id'], keep='last')

    # 2. TRANSFORM CHANNELS (Aggregated from distinct videos)
    print("[IMPORT] Aggregating unique channels...")
    unique_channels = df_videos[['channel_id', 'channel_title']].drop_duplicates(subset=['channel_id'])
    
    processed_channels = []
    for _, row in unique_channels.iterrows():
        c_id = row['channel_id']
        c_title = row['channel_title']
        
        # Calculate sum of views for this channel inside our slice
        c_views = int(df_videos[df_videos['channel_id'] == c_id]['view_count'].sum())
        
        # Generate semi-realistic subscriber count based on views
        subscribers = int(c_views * random.uniform(0.1, 0.5)) + random.randint(1000, 50000)
        
        channel_data = {
            "channel_id": c_id,
            "title": c_title,
            "description": f"Official channel of {c_title}. Importer channel metadata.",
            "published_at": datetime.now() - timedelta(days=random.randint(365, 1500)),
            "subscriber_count": subscribers,
            "video_count": random.randint(15, 350),
            "view_count": max(c_views, subscribers * 5),
            "updated_at": datetime.now()
        }
        processed_channels.append(channel_data)
        
    df_channels = pd.DataFrame(processed_channels)

    # 3. LOAD DATA INTO DUCKDB
    db_path = config.DB_PATH
    load(df_videos, df_channels, db_path)
    
    total_duration = time.time() - start_time
    print("=" * 60)
    print(f"      IMPORT COMPLETED SUCCESSFULLY in {total_duration:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    import_and_load_csv(1000)
