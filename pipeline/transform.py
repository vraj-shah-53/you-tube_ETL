import re
import pandas as pd
from datetime import datetime, timezone

def parse_iso_duration(duration_str: str) -> int:
    """
    Parses ISO 8601 duration string (e.g., PT15M30S, PT1H20M) and returns total seconds.
    """
    if not duration_str:
        return 0
    
    # Matches PT[H]H[M]M[S]S
    pattern = re.compile(r'PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0
        
    parts = match.groupdict()
    hours = int(parts['hours']) if parts['hours'] else 0
    minutes = int(parts['minutes']) if parts['minutes'] else 0
    seconds = int(parts['seconds']) if parts['seconds'] else 0
    
    return hours * 3600 + minutes * 60 + seconds


def transform_videos(video_items: list) -> pd.DataFrame:
    """
    Cleans, structures, and transforms raw YouTube video items list into a Pandas DataFrame.
    """
    if not video_items:
        print("[TRANSFORM] Warning: No video items to transform.")
        return pd.DataFrame()

    processed_videos = []
    current_time = datetime.now(timezone.utc)

    for item in video_items:
        v_id = item.get("id")
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        # Extract stats safely
        views = int(statistics.get("viewCount", 0))
        likes = int(statistics.get("likeCount", 0))
        comments = int(statistics.get("commentCount", 0))

        # Handle tags (list to comma-separated string)
        tags_list = snippet.get("tags", [])
        tags_str = ", ".join(tags_list) if isinstance(tags_list, list) else ""

        # Parse publication date
        published_at_str = snippet.get("publishedAt")
        published_at = pd.to_datetime(published_at_str, errors='coerce')

        # Feature Engineering: Days since published
        if pd.notnull(published_at):
            days_since_pub = (current_time - published_at.to_pydatetime().astimezone(timezone.utc)).days
            days_since_pub = max(1, days_since_pub)  # Avoid division by zero
        else:
            days_since_pub = 1

        # Feature Engineering: Engagement Rate
        # engagement_rate = (likes + comments) / views
        engagement_rate = round((likes + comments) / views, 4) if views > 0 else 0.0

        # Feature Engineering: Views per day
        views_per_day = round(views / days_since_pub, 2)

        # Parse duration
        duration_raw = content_details.get("duration", "")
        duration_sec = parse_iso_duration(duration_raw)

        video_data = {
            "video_id": v_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "published_at": published_at,
            "channel_id": snippet.get("channelId", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "category_id": snippet.get("categoryId", ""),
            "tags": tags_str,
            "duration_seconds": duration_sec,
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
            "engagement_rate": engagement_rate,
            "views_per_day": views_per_day,
            "days_since_published": days_since_pub,
            "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "updated_at": datetime.now()
        }
        processed_videos.append(video_data)

    df_videos = pd.DataFrame(processed_videos)
    print(f"[TRANSFORM] Transformed {len(df_videos)} video records successfully.")
    return df_videos


def transform_channels(channel_items: list) -> pd.DataFrame:
    """
    Cleans, structures, and transforms raw YouTube channel items list into a Pandas DataFrame.
    """
    if not channel_items:
        print("[TRANSFORM] Warning: No channel items to transform.")
        return pd.DataFrame()

    processed_channels = []

    for item in channel_items:
        c_id = item.get("id")
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        # Parse publication date
        published_at_str = snippet.get("publishedAt")
        published_at = pd.to_datetime(published_at_str, errors='coerce')

        channel_data = {
            "channel_id": c_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "published_at": published_at,
            "subscriber_count": int(statistics.get("subscriberCount", 0)),
            "video_count": int(statistics.get("videoCount", 0)),
            "view_count": int(statistics.get("viewCount", 0)),
            "updated_at": datetime.now()
        }
        processed_channels.append(channel_data)

    df_channels = pd.DataFrame(processed_channels)
    print(f"[TRANSFORM] Transformed {len(df_channels)} channel records successfully.")
    return df_channels


def transform(raw_videos: list, raw_channels: list) -> tuple:
    """
    Main transform step.
    Returns: (df_videos, df_channels)
    """
    df_videos = transform_videos(raw_videos)
    df_channels = transform_channels(raw_channels)
    return df_videos, df_channels
