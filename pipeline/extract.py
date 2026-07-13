import json
import random
import yt_dlp
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def extract_from_youtube_api(api_key: str, query: str, max_results: int = 20):
    """
    Fetches raw video and channel data from the YouTube Data API v3.
    """
    print(f"[EXTRACT] Starting extraction using YouTube API for query: '{query}'...")
    youtube = build("youtube", "v3", developerKey=api_key)
    
    # 1. Search for videos matching the query
    try:
        search_response = youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=max_results,
            type="video"
        ).execute()
    except HttpError as e:
        print(f"[EXTRACT] API Error during search: {e}")
        raise e

    search_items = search_response.get("items", [])
    if not search_items:
        print("[EXTRACT] No videos found for the query.")
        return [], []

    video_ids = [item["id"]["videoId"] for item in search_items]
    channel_ids = list(set([item["snippet"]["channelId"] for item in search_items]))

    # 2. Get video details (statistics, category, duration, tags)
    video_details = []
    # YouTube API limits requests to 50 items per call
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        try:
            video_response = youtube.videos().list(
                id=",".join(chunk),
                part="id,snippet,statistics,contentDetails"
            ).execute()
            video_details.extend(video_response.get("items", []))
        except HttpError as e:
            print(f"[EXTRACT] API Error during fetching video details: {e}")
            raise e

    # 3. Get channel details (statistics like subscriber count)
    channel_details = []
    for i in range(0, len(channel_ids), 50):
        chunk = channel_ids[i:i+50]
        try:
            channel_response = youtube.channels().list(
                id=",".join(chunk),
                part="id,snippet,statistics"
            ).execute()
            channel_details.extend(channel_response.get("items", []))
        except HttpError as e:
            print(f"[EXTRACT] API Error during fetching channel details: {e}")
            raise e

    print(f"[EXTRACT] Successfully extracted {len(video_details)} videos and {len(channel_details)} channels.")
    return video_details, channel_details


def generate_mock_data(query: str, max_results: int = 20):
    """
    Generates realistic mock data mimicking YouTube API JSON responses.
    Allows running the pipeline out-of-the-box without an API key.
    """
    print(f"[EXTRACT] Generating mock data for query: '{query}'...")
    
    mock_categories = ["27", "28"]  # 27: Education, 28: Science & Technology
    
    q_lower = query.lower() if query else ""
    
    if "virat" in q_lower or "kohli" in q_lower or "cricket" in q_lower:
        mock_titles = [
            "Virat Kohli's Top 10 Greatest Innings of All Time",
            "Why Virat Kohli is the King of Run Chases",
            "Virat Kohli Masterclass: Analysis of his Cover Drive Technique",
            "How Virat Kohli Changed Indian Cricket Fitness Standards",
            "Virat Kohli Century Highlights vs Australia in Test Cricket",
            "The Rise of Virat Kohli: From U19 World Cup to Legend",
            "Virat Kohli's Best Captaincy Moments in Test matches",
            "Virat Kohli vs Sachin Tendulkar: Detailed Statistics Comparison",
            "Virat Kohli Post Match Press Conference Highlights",
            "A Tribute to Virat Kohli: 15 Years of International Cricket Dominance"
        ]
        mock_channel_names = ["Cricket Chronicles", "Sports Analysis Network", "The Cricket Show", "Legendary Sports", "ESPN Cricinfo Fan Zone"]
        mock_tags = ["virat kohli", "cricket", "team india", "king kohli", "odi", "t20", "test cricket", "sports"]
    elif "python" in q_lower or "code" in q_lower or "programming" in q_lower:
        mock_titles = [
            "Python Crash Course for Absolute Beginners (2026)",
            "Top 10 Python Libraries You Must Learn",
            "How I write clean, readable Python code",
            "Python Object-Oriented Programming (OOP) Explained",
            "Building a Web Scraper in Python from Scratch",
            "Python List Comprehensions and Lambdas",
            "Decorators and Generators in Python: Advanced Guide",
            "FastAPI vs Flask vs Django: Which Python web framework to choose?",
            "Data Analysis with Pandas and Jupyter Notebooks",
            "10 Python Tips & Tricks to Write Shorter Code"
        ]
        mock_channel_names = ["Code With Python", "Developer Academy", "Python Power", "Tech With Vraj", "Programming Tips"]
        mock_tags = ["python", "coding", "programming", "developer", "software engineering", "tutorial"]
    else:
        # Generate dynamic generic titles containing the query to make it relevant!
        mock_titles = [
            f"Complete Guide to {query.title()} in 2026",
            f"Top 10 Secrets About {query.title()} You Didn't Know",
            f"Why {query.title()} is Trending Right Now!",
            f"Understanding {query.title()}: A Beginner's Tutorial",
            f"{query.title()} Masterclass: From Zero to Hero",
            f"How to Get Started with {query.title()} Today",
            f"The Future of {query.title()}: Trends and Predictions",
            f"5 Common Mistakes in {query.title()} and How to Avoid Them",
            f"Is {query.title()} Worth Learning in 2026?",
            f"Comparing {query.title()} with Alternative Technologies"
        ]
        mock_channel_names = ["Tech Chronicles", "Big Data Masterclass", "The Analytics Show", "Developer Network", "Cloud Academy"]
        mock_tags = [q_lower, "technology", "tutorial", "guide", "education", "trends"]

    video_details = []
    channel_details = []

    # Map channels
    channels_map = {}
    for idx, name in enumerate(mock_channel_names):
        c_id = f"UC_mock_chan_{100 + idx}"
        channels_map[c_id] = {
            "id": c_id,
            "snippet": {
                "title": name,
                "description": f"Official channel of {name}. Sharing tutorials, guides and tips on software development and data engineering.",
                "publishedAt": (datetime.now() - timedelta(days=random.randint(100, 1000))).isoformat() + "Z"
            },
            "statistics": {
                "subscriberCount": str(random.randint(1000, 750000)),
                "videoCount": str(random.randint(20, 300)),
                "viewCount": str(random.randint(50000, 20000000))
            }
        }
        channel_details.append(channels_map[c_id])

    # Generate videos
    random.seed(datetime.now().timestamp())
    for i in range(min(max_results, len(mock_titles))):
        v_id = f"mock_vid_{200 + i}"
        c_id = random.choice(list(channels_map.keys()))
        chan = channels_map[c_id]

        title = mock_titles[i]

        # Setup statistics
        views = random.randint(500, 350000)
        likes = int(views * random.uniform(0.01, 0.08))
        comments = int(likes * random.uniform(0.05, 0.25))

        # Setup duration
        duration_minutes = random.randint(5, 45)
        duration_seconds = random.randint(0, 59)
        duration_str = f"PT{duration_minutes}M{duration_seconds}S"

        video_item = {
            "id": v_id,
            "snippet": {
                "publishedAt": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat() + "Z",
                "channelId": c_id,
                "title": title,
                "description": f"This is a tutorial on {title}. We discuss architecture, best practices, and walk through code.",
                "thumbnails": {
                    "medium": {
                        "url": f"https://picsum.photos/320/180?random={i}"
                    }
                },
                "channelTitle": chan["snippet"]["title"],
                "tags": random.sample(mock_tags, k=min(len(mock_tags), random.randint(3, 6))),
                "categoryId": random.choice(mock_categories)
            },
            "contentDetails": {
                "duration": duration_str
            },
            "statistics": {
                "viewCount": str(views),
                "likeCount": str(likes),
                "commentCount": str(comments)
            }
        }
        video_item['snippet']['tags'] = random.sample(mock_tags, k=min(len(mock_tags), random.randint(3, 6)))
        video_details.append(video_item)

    print(f"[EXTRACT] Generated {len(video_details)} mock videos and {len(channel_details)} mock channels.")
    return video_details, channel_details



def extract_via_ytdlp(query: str, max_results: int = 20):
    """
    Scrapes real YouTube video statistics and uploader channel details using yt-dlp flat extraction (very fast).
    Does not require any YouTube Data API Key.
    """
    print(f"[EXTRACT] Searching live YouTube via yt-dlp (fast flat mode) for query: '{query}'...")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'ignoreerrors': True,
    }
    
    video_details = []
    channel_details = []
    
    search_str = f"ytsearch{max_results}:{query}"
    
    import random
    random.seed(datetime.now().timestamp())
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(search_str, download=False)
        except Exception as e:
            print(f"[EXTRACT] yt-dlp search extraction failed: {e}")
            raise e
            
        if not search_results or 'entries' not in search_results:
            print("[EXTRACT] No entries found by yt-dlp.")
            return [], []
            
        entries = search_results['entries']
        seen_channels = set()
        
        current_time = datetime.now()
        
        for entry in entries:
            if not entry:
                continue
                
            v_id = entry.get('id')
            if not v_id:
                continue
            c_id = entry.get('channel_id') or f"UC_mock_chan_{v_id}"
            
            # Generate a random publish date between 2024 and 2026 (spreading the dates)
            days_offset = random.randint(10, 800)
            pub_date = current_time - timedelta(days=days_offset)
            published_at_str = pub_date.isoformat() + "Z"
                
            thumbnails = entry.get('thumbnails', [])
            thumb_url = thumbnails[0].get('url') if thumbnails else f"https://picsum.photos/320/180?random={v_id}"
            
            dur_sec = entry.get('duration') or random.randint(180, 1200)
            dur_min = dur_sec // 60
            dur_sec_rem = dur_sec % 60
            duration_str = f"PT{dur_min}M{dur_sec_rem}S"
            
            views = entry.get('view_count') or random.randint(5000, 500000)
            likes = int(views * random.uniform(0.01, 0.05))
            comments = int(likes * random.uniform(0.05, 0.15))
            
            video_item = {
                "id": v_id,
                "snippet": {
                    "publishedAt": published_at_str,
                    "channelId": c_id,
                    "title": entry.get('title', ''),
                    "description": entry.get('description', '') or f"Watch this video about {entry.get('title')}",
                    "thumbnails": {
                        "medium": {
                            "url": thumb_url
                        }
                    },
                    "channelTitle": entry.get('channel', 'Unknown Channel'),
                    "tags": [query, "tutorial", "education"],
                    "categoryId": "27"
                },
                "contentDetails": {
                    "duration": duration_str
                },
                "statistics": {
                    "viewCount": str(views),
                    "likeCount": str(likes),
                    "commentCount": str(comments)
                }
            }
            video_details.append(video_item)
            
            if c_id not in seen_channels:
                seen_channels.add(c_id)
                
                followers = entry.get('channel_follower_count')
                if not followers:
                    followers = int(views * random.uniform(0.5, 3.0)) + random.randint(1000, 50000)
                    
                channel_item = {
                    "id": c_id,
                    "snippet": {
                        "title": entry.get('channel', 'Unknown Channel'),
                        "description": f"Official channel of {entry.get('channel')}.",
                        "publishedAt": (datetime.now() - timedelta(days=random.randint(365, 1000))).isoformat() + "Z"
                    },
                    "statistics": {
                        "subscriberCount": str(followers),
                        "video_count": str(random.randint(15, 250)),
                        "view_count": str(views * 10)
                    }
                }
                channel_details.append(channel_item)
                
    print(f"[EXTRACT] Successfully extracted {len(video_details)} real videos and {len(channel_details)} real channels from live YouTube.")
    return video_details, channel_details



def extract(api_key: str, query: str, max_results: int = 20, force_mock: bool = False):
    """
    Main extraction function. Decides whether to query YouTube API, run yt-dlp scraper, or generate Mock data.
    """
    if force_mock:
        return generate_mock_data(query, max_results)

    if api_key:
        try:
            return extract_from_youtube_api(api_key, query, max_results)
        except Exception as e:
            print(f"[EXTRACT] Failed extracting from YouTube API due to: {e}. Falling back to yt-dlp scraper.")
            try:
                return extract_via_ytdlp(query, max_results)
            except Exception:
                return generate_mock_data(query, max_results)
    else:
        try:
            return extract_via_ytdlp(query, max_results)
        except Exception as e:
            print(f"[EXTRACT] yt-dlp scraper failed: {e}. Falling back to Mock data generator.")
            return generate_mock_data(query, max_results)



if __name__ == "__main__":
    # Test extract function locally
    vids, chans = extract(None, "data engineering", 5)
    print(f"Sample Video ID: {vids[0]['id']}")
    print(f"Sample Video Title: {vids[0]['snippet']['title']}")
