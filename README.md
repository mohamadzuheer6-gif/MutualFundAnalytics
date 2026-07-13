# BlueStock Mutual Fund Analytics Platform

An end-to-end financial technology platform to analyze Indian mutual funds. The platform automates data ingestion, cleaning, database loading, ETL synchronization, performance metrics calculation, and provides a multi-page interactive Streamlit analytical dashboard.

🚀 **Live Application Link:** https://bluestock-mf-analytics.streamlit.app/

---

## 🛠️ Technology Stack
- **Dashboard Application**: Streamlit, Plotly (Express & Graph Objects), Scipy, Numpy, Pandas
- **Database Engine**: SQLite3, SQLAlchemy, SQL (DDL Schema and Queries)
- **ETL Pipeline**: Python, Requests (REST API Integration with AMFI)
- **Data Engineering / Analysis**: Jupyter Notebooks, openpyxl, CVXPY (Markowitz Portfolio Optimization)
- **Styling & Theme**: Vanilla CSS (custom card styles, dark navigation layout, Inter typography)

---

## 📂 Project Directory Structure

```
MutualFundAnalytics/
├── data/
│   ├── raw/                  # Original raw CSV files and API caches
│   │   └── live_nav/         # Local API cache directory for fetched daily NAV data
│   ├── processed/            # Cleaned/processed datasets ready for ingestion
│   └── db/
│       └── bluestock_mf.db   # Main SQLite analytical database (~8.4 MB)
├── notebooks/                # Jupyter Notebooks documenting analytical steps
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/                  # Production pipeline and CLI scripts
│   ├── etl_pipeline.py       # Core runner for daily automated ETL pipeline
│   ├── live_nav_fetch.py     # Contacts AMFI API to pull latest daily NAV metrics
│   ├── clean_daily_nav.py    # Standardizes raw API response CSVs
│   ├── update_database.py    # Loads new dates and NAVs and updates runs metadata
│   ├── compute_metrics.py    # Calculates mutual fund CAGR, Volatility, Sharpe, and Drawdowns
│   ├── recommender.py        # CLI Interactive mutual fund recommendation tool
│   └── load_sqlite.py        # Performs the initial database schemas loading
├── sql/
│   └── schema.sql            # Core database schema (DQL, fact tables, dimensions)
    |__ queries.sql   
├── dashboard/
│   └── bluestock_mf.pbix     # PowerBI Dashboard source file
├── reports/
│   ├── Final_Report.pdf             # Streamlined internship report PDF
│   ├── presentation.pptx     # PowerPoint capstone presentation slide deck
│   └── supporting_materials/ # Sub-folder holding analytical CSVs and plots
├── streamlit_app/            # Streamlit multi-page application
│   ├── app.py                # App entry point
│   ├── config.py             # Global DB path and theme variables
│   ├── database.py           # Database connections and date format helpers
│   ├── styles.css            # Global styling overrides
│   ├── theme.py              # Injects custom styles and fonts
│   ├── components/           # Reusable UI components (navbar, sidebar, footer)
│   └── services/             # Core business logic (optimizers, recommenders)
├── docs/                     # Technical summaries, dictionaries, and draft records
├── logs/                     # Log files including automated etl.log
├── .gitignore
├── requirements.txt          # Python library dependencies
└── LICENSE                   # MIT Open-source License
```

---

## 🚀 Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd MutualFundAnalytics
   ```

2. **Initialize Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database** (Optional - Database is pre-loaded):
   To recreate the SQLite database and populate initial cleaned tables from scratch:
   ```bash
   python scripts/load_sqlite.py
   ```

---

## 📈 Running the Streamlit Application

Execute the following command in your terminal from the workspace root directory:
```bash
streamlit run streamlit_app/app.py
```
Open `http://localhost:8501/` in your browser. The sidebar allows you to navigate through:
- **Dashboard**: High-level mutual fund industry overview.
- **NAV Analytics**: Interactive historical pricing charts, moving averages, daily returns, and drawdowns.
- **Performance**: Risk-adjusted bubble plots, CAGR rankings, and Sharpe/Sortino filters.
- **Monte Carlo**: Volatility-based future wealth projections and confidence boundaries.
- **Portfolio Optimizer**: Markowitz Efficient Frontier calculation for asset weights.
- **Fund Recommender**: Multi-horizon weighted scoring recommendation wizard.
- **Admin**: ETL log inspection, cache recomputation triggers, and database schema overview.

---

## 🔄 ETL Pipeline Automation

### 1. Manual ETL Pipeline Run
Run the full ETL pipeline to pull the latest daily NAV information from the AMFI API, standardize the data, insert it into `fact_nav`, and update the UI run timestamp metadata:
```bash
python scripts/etl_pipeline.py
```

### 2. Schedule Daily Automated Runs (Windows Task Scheduler)
The system includes a daily scheduled job named **"Bluestock Daily ETL"**:
- **Triggers**: Daily at **08:00 PM**.
- **Action**:
  - **Program/script**: `python.exe`
  - **Arguments**: `scripts/etl_pipeline.py`
  - **Start in**: `<Absolute path to MutualFundAnalytics>`

This ensures that the mutual fund database remains fully synchronized locally.

> 📝 **Note on Database Synchronization:**  
> I scheduled my local ETL pipeline to run automatically every day at 8:00 PM on my computer. However, this only updates the database file locally on my machine. Since the live website reads the database file hosted on my GitHub repository (and Streamlit Cloud servers reset periodically), I must push the updated local database to GitHub to show the daily 8:00 PM updates on the live website. I have to push it manually every time because my local computer is isolated from the cloud, and the Streamlit Cloud server has no direct access to read files from my local system.
