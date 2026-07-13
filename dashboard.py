import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root directory to path to support imports if running streamlit from pipeline folder
sys.path.append(str(Path(__file__).resolve().parent))
import config
from pipeline.run import run_pipeline
from pipeline.import_real_csv import import_and_load_csv

# Page Configuration
st.set_page_config(
    page_title="YouTube Analytics ETL Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark-themed premium look)
st.markdown("""
    <style>
    .main {
        background-color: #0f1115;
        color: #e6e8ea;
    }
    .stMetric {
        background-color: #1a1d24;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2d3139;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #a0aec0 !important;
        font-weight: 500 !important;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #ff4b4b !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 30px;
        padding: 20px;
        background: linear-gradient(135deg, #1e1e24 0%, #111115 100%);
        border-radius: 12px;
        border: 1px solid #2d3139;
    }
    .header-logo {
        font-size: 3rem;
        margin-right: 20px;
    }
    .header-text h1 {
        margin: 0;
        font-size: 2.2rem;
        color: #ffffff;
    }
    .header-text p {
        margin: 5px 0 0 0;
        color: #a0aec0;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to query DuckDB
def run_query(query: str):
    db_path = config.DB_PATH
    if not Path(db_path).exists():
        return None
    try:
        conn = duckdb.connect(db_path, read_only=True)
        df = conn.execute(query).df()
        conn.close()
        return df
    except Exception as e:
        print(f"[DB] Error querying database: {e}")
        return None


# Top header
st.markdown("""
    <div class="header-container">
        <div class="header-logo">🎥</div>
        <div class="header-text">
            <h1>YouTube Analytics ETL Dashboard</h1>
            <p>Analyzing metrics, engagement rates, and content insights powered by DuckDB & Pandas</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e1/Logo_of_YouTube_%282015-2017%29.svg", width=150)
st.sidebar.header("ETL Orchestrator")

# Check if database exists
db_exists = Path(config.DB_PATH).exists()

if not db_exists:
    st.sidebar.warning("⚠️ Database not found!")
    st.warning("No data found in DuckDB database. Click the button in the sidebar or run `python pipeline/run.py` to trigger the ETL process.")

query_input = st.sidebar.text_input("Search Keyword for ETL", config.SEARCH_QUERY)
max_results_input = st.sidebar.slider("Max Results to Fetch", 5, 50, config.MAX_RESULTS)
mock_mode = st.sidebar.checkbox("Force Mock Mode", value=not bool(config.YOUTUBE_API_KEY))

if st.sidebar.button("🚀 Run ETL Pipeline", use_container_width=True):
    with st.spinner("Executing Extract-Transform-Load Pipeline..."):
        try:
            # Clear old records first so we only show the new search results
            conn = duckdb.connect(config.DB_PATH)
            conn.execute("DROP TABLE IF EXISTS videos")
            conn.execute("DROP TABLE IF EXISTS channels")
            conn.close()
            
            run_pipeline(query=query_input, max_results=max_results_input, force_mock=mock_mode)
            st.sidebar.success("ETL Run Completed!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"ETL Execution failed: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("Offline Dataset Option")
if st.sidebar.button("📥 Load Real Kaggle CSV", use_container_width=True):
    with st.spinner("Downloading and importing Kaggle YouTube dataset..."):
        try:
            # Clear database first so we don't mix different datasets
            conn = duckdb.connect(config.DB_PATH)
            conn.execute("DROP TABLE IF EXISTS videos")
            conn.execute("DROP TABLE IF EXISTS channels")
            conn.close()
            
            import_and_load_csv(1000)
            st.sidebar.success("Import Completed!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Import failed: {e}")



if st.sidebar.button("🗑️ Clear Database", use_container_width=True):
    with st.spinner("Clearing database..."):
        try:
            conn = duckdb.connect(config.DB_PATH)
            conn.execute("DROP TABLE IF EXISTS videos")
            conn.execute("DROP TABLE IF EXISTS channels")
            conn.close()
            st.sidebar.success("Database cleared!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Failed to clear database: {e}")

st.sidebar.markdown("---")

st.sidebar.markdown("""
### Technology Stack
- **Ingestion**: Kaggle CSV / YouTube API
- **Processing**: Pandas DataFrame
- **Warehouse**: DuckDB SQL
- **Orchestrator**: Python Pipeline
- **Visualization**: Streamlit & Plotly
""")

# Dashboard Main Panel Content
if db_exists:
    # 1. Load Data
    df_v = run_query("SELECT * FROM videos")
    df_c = run_query("SELECT * FROM channels")

    if df_v is not None and not df_v.empty:
        # Key Metrics (KPIs)
        total_views = df_v['view_count'].sum()
        avg_likes = df_v['like_count'].mean()
        avg_engagement = df_v['engagement_rate'].mean() * 100 # In percentage
        total_videos = len(df_v)
        unique_channels = df_v['channel_id'].nunique()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Videos Analyzed", f"{total_videos}")
        col2.metric("Total Video Views", f"{total_views:,}")
        col3.metric("Avg. Likes per Video", f"{int(avg_likes):,}")
        col4.metric("Avg. Engagement Rate", f"{avg_engagement:.2f}%")

        st.markdown("### 📈 Visual Insights")

        col_left, col_right = st.columns(2)

        with col_left:
            # Chart 1: Top 10 Videos by View Count
            st.subheader("Top 10 Most Viewed Videos")
            df_top_views = df_v.nlargest(10, 'view_count')
            fig_views = px.bar(
                df_top_views,
                x='view_count',
                y='title',
                orientation='h',
                color='view_count',
                color_continuous_scale='Reds',
                labels={'view_count': 'Views', 'title': 'Video Title'},
                height=400
            )
            fig_views.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#e6e8ea"
            )
            st.plotly_chart(fig_views, use_container_width=True)

        with col_right:
            # Chart 2: Views vs Engagement Rate Scatter Plot
            st.subheader("Engagement Rate vs View Count")
            fig_scatter = px.scatter(
                df_v,
                x='view_count',
                y='engagement_rate',
                size='like_count',
                color='channel_title',
                hover_name='title',
                labels={'view_count': 'Views', 'engagement_rate': 'Engagement Rate (Fraction)'},
                height=400
            )
            fig_scatter.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#e6e8ea"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # Tabbed details section
        st.markdown("### 🔍 Detailed Data Analysis")
        tab_v, tab_c = st.tabs(["🎥 Video Analytics Table", "🎙️ Channel Performance"])

        with tab_v:
            # Video Data Grid
            st.dataframe(
                df_v[[
                    'title', 'channel_title', 'published_at', 
                    'view_count', 'like_count', 'comment_count', 
                    'engagement_rate', 'duration_seconds'
                ]].sort_values(by='view_count', ascending=False),
                column_config={
                    "title": "Video Title",
                    "channel_title": "Channel",
                    "published_at": st.column_config.DatetimeColumn("Published At"),
                    "view_count": st.column_config.NumberColumn("Views", format="%d"),
                    "like_count": st.column_config.NumberColumn("Likes", format="%d"),
                    "comment_count": st.column_config.NumberColumn("Comments", format="%d"),
                    "engagement_rate": st.column_config.NumberColumn("Engagement Rate", format="%.4f"),
                    "duration_seconds": st.column_config.NumberColumn("Duration (Sec)", format="%d"),
                },
                hide_index=True,
                use_container_width=True
            )

        with tab_c:
            if df_c is not None and not df_c.empty:
                # Channel Stats
                fig_channels = px.bar(
                    df_c,
                    x='title',
                    y='subscriber_count',
                    color='video_count',
                    color_continuous_scale='Viridis',
                    labels={'subscriber_count': 'Subscribers', 'title': 'Channel Name', 'video_count': 'Video Count'},
                    title="Channel Subscriber Counts vs Total Uploads"
                )
                fig_channels.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color="#e6e8ea"
                )
                st.plotly_chart(fig_channels, use_container_width=True)

                st.dataframe(
                    df_c[['title', 'subscriber_count', 'video_count', 'view_count', 'published_at']],
                    column_config={
                        "title": "Channel Name",
                        "subscriber_count": st.column_config.NumberColumn("Subscribers", format="%d"),
                        "video_count": st.column_config.NumberColumn("Videos Uploaded", format="%d"),
                        "view_count": st.column_config.NumberColumn("Channel Total Views", format="%d"),
                        "published_at": st.column_config.DatetimeColumn("Channel Created"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No channel detailed information in the database. Ensure you run the ETL.")

    else:
        st.info("No video records exist in the database. Run the ETL pipeline from the sidebar.")

else:
    st.info("The DuckDB database is currently empty. Run the pipeline in the sidebar to extract sample YouTube data.")
