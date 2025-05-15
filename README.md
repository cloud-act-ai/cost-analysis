# FinOps360 Cost Analysis Dashboard

A FastAPI application for visualizing and analyzing cloud costs data.

## Features

- Interactive dashboard for cost analysis
- Asynchronous data processing for better performance
- Support for BigQuery data source
- Interactive charts for data visualization
- Responsive design for all device sizes

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd cost-analysis

# Install dependencies (automatically done when running the app)
pip install -r requirements.txt
```

## Running the Application

The application can be run in different modes depending on your needs:

```bash
# Run in production mode
./run.sh

# Run in development mode with auto-reload
./run.sh --dev

# Run on a specific port
./run.sh --port=8081

# Run with sample data (no BigQuery credentials needed)
./run_sample.sh

# Run sample data in development mode
./run_sample.sh --dev

# Display help information
./run.sh --help
```

### Sample Data Mode

The application can operate in two data modes:

1. **BigQuery Mode** - Connects to Google BigQuery to fetch real cost data
   - Requires valid Google Cloud credentials
   - Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable to your service account key

2. **Sample Data Mode** - Uses generated sample data for demonstration
   - No credentials required
   - Perfect for testing and demos
   - Displays a "DEMO MODE" banner at the top of the dashboard

```bash
# Production mode
./run.sh [port] [workers]

# Development mode with auto-reload
./run.sh --dev

# Examples:
./run.sh                    # Run on default port 8080
./run.sh 9000               # Run on port 9000
./run.sh --port=9000        # Same as above
./run.sh --workers=2        # Run with 2 workers
./run.sh --dev              # Run in development mode
```

## API Endpoints

- `/` - Main dashboard
- `/loading` - Loading page with auto-redirect
- `/api/health` - Health check endpoint

## Project Structure

```
cost-analysis/
├── app/                    # Main application package
│   ├── core/               # Core application code
│   │   ├── app.py          # FastAPI application
│   │   ├── dashboard.py    # Dashboard generator
│   │   └── data_access.py  # Data access functions
│   ├── utils/              # Utility modules
│   │   ├── chart/          # Chart generation utilities
│   │   │   ├── config.py   # Chart configuration
│   │   │   └── generator.py # Chart generator
│   │   ├── config_loader.py # Configuration loader
│   │   ├── data_generator.py # Sample data generator
│   │   └── db.py           # Database utilities
│   ├── config/             # Configuration files
│   │   ├── config.yaml     # Main configuration
│   │   └── requirements.txt # Dependencies
│   ├── templates/          # HTML templates
│   │   ├── dashboard_template.html
│   │   ├── error.html
│   │   └── loading.html
│   ├── sql/                # SQL queries
│   ├── static/             # Static assets
│   └── __main__.py         # Entry point
├── docs/                   # Documentation
├── requirements.txt        # Symlink to app/config/requirements.txt
├── config.yaml             # Symlink to app/config/config.yaml
└── run.sh                  # Run script
```

## Configuration

Configuration is managed via `app/config/config.yaml`:

```yaml
# BigQuery settings
bigquery:
  project_id: your-project-id
  dataset: your-dataset
  cost_table: your-cost-table
  avg_table: your-avg-table-name

# Chart settings
charts:
  enabled: true

# Data settings
data:
  day_current_date: "2025-05-03"
  day_previous_date: "2025-05-02"
  # ... other settings
  
# Output settings
output:
  directory: reports
```

## License

[Include license information here]
