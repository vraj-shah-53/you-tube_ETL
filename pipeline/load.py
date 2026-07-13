import duckdb
import pandas as pd

def get_db_connection(db_path: str):
    """
    Establish connection to the DuckDB database.
    """
    return duckdb.connect(db_path)


def initialize_tables(conn):
    """
    Creates tables in the DuckDB database if they do not exist.
    """
    # 1. Create channels table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            description VARCHAR,
            published_at TIMESTAMP,
            subscriber_count BIGINT,
            video_count INTEGER,
            view_count BIGINT,
            updated_at TIMESTAMP
        )
    """)

    # 2. Create videos table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            description VARCHAR,
            published_at TIMESTAMP,
            channel_id VARCHAR,
            channel_title VARCHAR,
            category_id VARCHAR,
            tags VARCHAR,
            duration_seconds INTEGER,
            view_count BIGINT,
            like_count BIGINT,
            comment_count BIGINT,
            engagement_rate DOUBLE,
            views_per_day DOUBLE,
            days_since_published INTEGER,
            thumbnail_url VARCHAR,
            updated_at TIMESTAMP
        )
    """)
    print("[LOAD] Database tables initialized successfully.")


def upsert_dataframe(conn, df: pd.DataFrame, table_name: str, primary_key: str):
    """
    Loads a Pandas DataFrame into a target DuckDB table using a staging-upsert pattern:
    1. Write dataframe to a temp/staging table.
    2. Delete existing records from the target table where primary key matches staging.
    3. Insert all records from staging into target table.
    This ensures idempotence (running multiple times does not duplicate records).
    """
    if df.empty:
        print(f"[LOAD] Staging empty for table '{table_name}'. Skipping load.")
        return

    # DuckDB can query Pandas variables in local scope directly!
    # Register DataFrame as a temporary view/table
    staging_view_name = f"staging_{table_name}"
    conn.register(staging_view_name, df)

    try:
        # Start a transaction to ensure atomic upsert
        conn.execute("BEGIN TRANSACTION")

        # 1. Delete rows matching staging keys
        delete_query = f"""
            DELETE FROM {table_name} 
            WHERE {primary_key} IN (SELECT {primary_key} FROM {staging_view_name})
        """
        conn.execute(delete_query)

        # 2. Insert new rows from staging
        insert_query = f"""
            INSERT INTO {table_name} 
            SELECT * FROM {staging_view_name}
        """
        conn.execute(insert_query)

        # Commit transaction
        conn.execute("COMMIT")
        print(f"[LOAD] Successfully upserted {len(df)} records into '{table_name}'.")

    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"[LOAD] Error during upsert into '{table_name}': {e}")
        raise e
    finally:
        # Clean up temporary registration
        conn.unregister(staging_view_name)


def load(df_videos: pd.DataFrame, df_channels: pd.DataFrame, db_path: str):
    """
    Main loader function. Connects to database, creates tables, and upserts data.
    """
    print(f"[LOAD] Opening database connection to: {db_path}")
    conn = get_db_connection(db_path)
    
    try:
        initialize_tables(conn)
        
        # Load Channels
        if not df_channels.empty:
            upsert_dataframe(conn, df_channels, "channels", "channel_id")
            
        # Load Videos
        if not df_videos.empty:
            upsert_dataframe(conn, df_videos, "videos", "video_id")
            
    finally:
        conn.close()
        print("[LOAD] Database connection closed.")
