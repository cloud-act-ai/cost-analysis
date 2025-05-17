"""
FastAPI application for FinOps360 cost analysis dashboard.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import bigquery

from app.utils.config_loader import load_config
from app.utils.chart.config import are_charts_enabled
from app.core.dashboard import generate_html_report_async
from app.utils.filter_utils import get_filter_defaults_from_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinOps360 Cost Analysis Dashboard",
    description="FastAPI application for cost analysis dashboard",
    version="1.0.0"
)

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR

# Setup templates
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Add static files support for any future static assets
static_dir = APP_DIR / "static"
if not static_dir.exists():
    static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# BigQuery client dependency
def get_bigquery_client():
    """Dependency to get authorized BigQuery client"""
    try:
        # For production, use credentials from GOOGLE_APPLICATION_CREDENTIALS env var
        client = bigquery.Client()
        logger.info(f"Successfully connected to BigQuery with project: {client.project}")
        return client
    except Exception as e:
        # Instead of raising an exception, return a mock client that will trigger fallback to sample data
        logger.warning(f"Using sample data - BigQuery connection error: {e}")
        # Use a mock client that will trigger the sample data fallback
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.project = "sample-data-project"
        return mock_client

# Configuration dependency
def get_config():
    """Dependency to load application configuration"""
    try:
        config = load_config("config.yaml")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to load configuration")

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    client: bigquery.Client = Depends(get_bigquery_client),
    config: Dict[str, Any] = Depends(get_config),
    cto: Optional[str] = None,
    pillar: Optional[str] = None,
    product: Optional[str] = None,
    show_sql: bool = False
):
    """
    Main dashboard endpoint that renders the HTML dashboard asynchronously.
    Applies filter parameters from request and default filters from config.
    """
    # Get default filter values from config if needed
    filter_defaults = get_filter_defaults_from_config()
    
    # Use provided filter values or fall back to defaults if not provided
    cto = cto or filter_defaults.get('default_cto')
    pillar = pillar or filter_defaults.get('default_pillar')
    product = product or filter_defaults.get('default_product')
    try:
        # Log connected project
        logger.info(f"Connected to BigQuery project: {client.project}")
        
        # Set interactive charts flag
        interactive_charts = are_charts_enabled()
        logger.info(f"Interactive charts {'enabled' if interactive_charts else 'disabled'}")
        
        # Get BigQuery connection details from config
        data_config = config.get('bigquery', {})
        project_id = data_config.get('project_id', client.project)
        
        # Always get BigQuery configuration directly from config without defaults
        dataset = data_config.get('dataset', '')
        cost_table = data_config.get('cost_table', '')
        avg_table = data_config.get('avg_table', '')
        
        # Generate in-memory report
        output_dir = Path(config.get('output', {}).get('directory', 'reports'))
        os.makedirs(output_dir, exist_ok=True)
        output_path = output_dir / "finops_dashboard.html"
        
        # Pass filter parameters to the report generator
        await generate_html_report_async(
            client=client,
            project_id=project_id,
            dataset=dataset,
            cost_table=cost_table,
            avg_table=avg_table,
            template_path=str(APP_DIR / "templates" / "dashboard_template.html"),
            output_path=str(output_path),
            use_interactive_charts=interactive_charts,
            filters={
                'cto': cto,
                'pillar': pillar,
                'product': product,
                'show_sql': show_sql
            }
        )
        
        # Read the generated HTML file and return it
        with open(output_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        # Return a proper error page with templating
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "error_message": "An error occurred while generating the dashboard. Please check the logs for details."
            },
            status_code=500
        )

@app.get("/loading", response_class=HTMLResponse)
async def loading(request: Request):
    """Loading page that redirects to dashboard after a delay"""
    return templates.TemplateResponse("loading.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify the API is running"""
    return {"status": "healthy", "service": "finops360-dashboard"}