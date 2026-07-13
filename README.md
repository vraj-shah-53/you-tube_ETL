# YouTube Data Analytics ETL Pipeline

A modern, local-first data engineering project that implements an end-to-end ETL (Extract, Transform, Load) pipeline using the YouTube Data API v3, Python (Pandas), DuckDB, and Streamlit.

This project is built to demonstrate production-grade data engineering concepts:
- **API Extraction** with robust error-handling and a zero-dependency **Mock Data Fallback** (allows the pipeline and dashboard to run out-of-the-box without requiring API credentials).
- **Transformations** utilizing Pandas for data cleaning, timestamp standardization, duration parsing, and engagement metrics engineering.
- **Data Warehousing** inside DuckDB using a transactional **Staging-Upsert (Merge)** pattern to maintain idempotent pipeline runs (no duplicated rows if run multiple times).
- **Visualization** using a Streamlit web application populated with Plotly interactive charts.
- **Infrastructure & Containerization** utilizing Docker & Docker Compose.

---

## 🏗️ Architecture

```mermaid
graph TD
    A[YouTube API / Mock Generator] -->|Extract JSON| B[Python ETL Runner]
    B -->|Transform & Clean - Pandas| C[DataFrame Processing]
    C -->|Idempotent Staging Upsert| D[(DuckDB Storage)]
    D -->|Analytical SQL Queries| E[Streamlit Dashboard]
    E -->|Interactive Charts| F[User Interface]
```

1. **Extract**: Fetch search queries and metadata from YouTube Data API (e.g. video views, likes, comments, category, tag analysis, and channel statistics). Fallback to realistic mock data if API key is missing.
2. **Transform**: 
   - Parse ISO 8601 video durations into absolute seconds.
   - Extract and format timestamps.
   - Feature engineer metrics like `engagement_rate` ((likes + comments) / views) and `views_per_day`.
3. **Load**: Connect to local DuckDB file (`data/youtube_data.db`). Stage and upsert (update if exists, insert if new) records to ensure pipeline repeatability.
4. **Visualize**: Load metrics from the DB directly into Streamlit to render KPIs and Plotly plots.

---

## 📊 Database Schema

The pipeline creates and manages a relational schema in `data/youtube_data.db`:

### `channels`
| Column | Type | Description |
| :--- | :--- | :--- |
| `channel_id` (PK) | VARCHAR | Unique YouTube Channel identifier |
| `title` | VARCHAR | Channel display name |
| `description` | VARCHAR | Channel bio text |
| `published_at` | TIMESTAMP | Creation date of the channel |
| `subscriber_count` | BIGINT | Current total subscribers |
| `video_count` | INTEGER | Number of uploaded videos |
| `view_count` | BIGINT | Lifetime channel video views |
| `updated_at` | TIMESTAMP | Metadata ingestion timestamp |

### `videos`
| Column | Type | Description |
| :--- | :--- | :--- |
| `video_id` (PK) | VARCHAR | Unique YouTube Video identifier |
| `title` | VARCHAR | Video title |
| `description` | VARCHAR | Video description |
| `published_at` | TIMESTAMP | Upload timestamp |
| `channel_id` | VARCHAR | Foreign reference to channel |
| `channel_title` | VARCHAR | Channel name at ingestion |
| `category_id` | VARCHAR | YouTube category grouping |
| `tags` | VARCHAR | Comma-separated video tag list |
| `duration_seconds` | INTEGER | Parsed video duration in seconds |
| `view_count` | BIGINT | Total view count |
| `like_count` | BIGINT | Total likes |
| `comment_count` | BIGINT | Total comments |
| `engagement_rate` | DOUBLE | Calculated engagement ratio |
| `views_per_day` | DOUBLE | Velocity of views since release |
| `days_since_published` | INTEGER | Total age of the video in days |
| `thumbnail_url` | VARCHAR | High-res image link |
| `updated_at` | TIMESTAMP | Pipeline execution timestamp |

---

## 🚀 Getting Started

### Option 1: Local Installation (Recommended)

1. **Clone the Repository**:
   ```bash
   git clone <your-repo-link>
   cd youtube-etl-pipeline
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   *Note: If `YOUTUBE_API_KEY` is left blank, the pipeline will run in mock data generation mode.*

5. **Run the ETL Pipeline**:
   ```bash
   python pipeline/run.py
   ```
   *Additional options:*
   * `--query "Python project"`: Run ETL search with custom keyword.
   * `--max-results 20`: Limit records processed.
   * `--mock`: Run with mock data regardless of `.env` configurations.

6. **Start Streamlit Dashboard**:
   ```bash
   streamlit run dashboard.py
   ```
   Access the dashboard at `http://localhost:8501`.

---

### Option 2: Run via Docker (Zero Configuration)

We provide a Dockerized environment including the volume-mounted database:

1. **Start all services**:
   ```bash
   docker-compose up --build
   ```

2. **Access Streamlit**:
   Open `http://localhost:8501` in your browser.

3. **Re-running pipeline in Docker**:
   Use the **ETL Orchestrator** controls on the Streamlit sidebar inside the browser to configure keyword search and trigger pipeline executions directly!

---

## 🔑 How to get a YouTube API Key (Optional)

To run the pipeline with live real-time data:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Search for the **YouTube Data API v3** in the API Library and click **Enable**.
4. Navigate to **Credentials** tab on the sidebar.
5. Click **Create Credentials** -> **API Key**.
6. Copy the generated key and paste it as `YOUTUBE_API_KEY` in your `.env` file.
