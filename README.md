# FinOps360 Cost Analysis Tool

A modular Python application for analyzing cloud cost data and generating reports to identify efficiencies and optimization opportunities.

## Features

- **Flexible Analysis Types**: 
  - **Cloud Cost Analysis**: Compare costs across different time periods
    - Month-to-month
    - Quarter-to-quarter
    - Week-to-week
    - Year-to-year
  - **NEW! Environment Analysis**: Analyze Production vs Non-Production costs
    - Overall environment distribution
    - Production/Non-Production breakdown by organization, VP, and pillar
    - Identification of applications with high non-production costs

- **Versatile Grouping Options**: Analyze costs by:
  - Organization (ORG)
  - Vice President (VP)
  - Business Pillar (PILLAR)
  - Product (TR_PRODUCT)
  - Environment (ENV)
  - Cloud provider (Cloud)

- **Key Analysis Metrics**:
  - Total spend by period
  - Cost efficiencies (reductions)
  - Cost investments (increases)
  - Net change (absolute and percentage)
  - Production vs Non-Production distribution
  - Top N investments and efficiencies

- **Report Generation**:
  - Responsive HTML reports with visualizations
  - Customizable columns display
  - Easy CSV export option

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd cost-analysis
```

2. Install required dependencies:
```
pip install -r requirements.txt
```

3. Initialize the environment:
```
python init.py
```

## Usage

### Analysis Types

The tool now supports two types of analysis:

1. **Cloud Cost Analysis** - Compare costs across time periods
2. **Environment Analysis** - Analyze Production vs Non-Production costs

### Cloud Cost Analysis

Run the cloud cost analyzer with the default configuration:

```
python finops_analyzer.py cloud
```

With custom parameters:

```
python finops_analyzer.py cloud --parent-group VP --parent-value Bob
python finops_analyzer.py cloud --period quarter --period-value Q1
```

### Environment Analysis (New!)

Run the environment analyzer to see Prod vs Non-Prod distribution:

```
python finops_analyzer.py environment
```

With custom parameters:

```
python finops_analyzer.py environment --nonprod-threshold 30
python finops_analyzer.py environment --parent-group PILLAR --parent-value Retail
```

### Example Configurations

Use one of the predefined configurations:

```
python finops_analyzer.py cloud --config examples/vp_config.yaml
python finops_analyzer.py environment --config examples/env_config.yaml
```

## Configuration Options

Edit `config.yaml` to customize analysis parameters:

```yaml
# Data sources and paths
data:
  file_path: data/finops_data.csv
  output_dir: output

# Analysis settings
analysis:
  # Time period configuration
  period_type: month  # Options: month, quarter, week, year
  period_value: Mar   # Month name, quarter (Q1-Q4), week number, or year
  year: 2024
  
  # Grouping configuration
  parent_grouping: ORG  # Can be any column in dataset: ORG, TR_PRODUCT, ENV, Cloud, VP, PILLAR, etc.
  parent_grouping_value: Starling  # Default value for the parent grouping
  
  # Child grouping for detailed analysis
  child_grouping: Application_Name
  top_n: 10
  include_applications: true
  
  # Environment analysis settings (for Prod vs Non-Prod reporting)
  nonprod_threshold: 20  # Percentage threshold for highlighting high non-prod costs
  
  # Display columns (optional, for customizing report columns)
  display_columns:
    - Application_Name
    - ORG
    - VP
    - PILLAR
    - Cloud
    - Env
    - Cost

# Report settings
report:
  generate_html: true
  export_csv: true
  page_title: Cloud Spend Management Report
  company_name: FinOps
  logo_path: ""
```

## Data Format

The expected CSV format includes the following columns:

- DATE - Date of the cost entry
- WM_WEEK - Week identifier (e.g., Week 11)
- QTR - Quarter identifier (e.g., Q1)
- Month - Month name (e.g., Jan, Feb)
- FY - Fiscal year
- TR_PRODUCT - Product name
- ORG - Organization name
- VP - Vice President
- PILLAR - Business pillar/department
- Application_Name - Application identifier
- Cloud - Cloud provider name
- Env - Environment (e.g., Prod, Dev, Stage)
- Cost - Cost amount

## Project Structure

- `finops_analyzer.py` - Main entry point for all analysis types
- `common/` - Common modules
  - `finops_config.py` - Configuration management
  - `finops_data.py` - Data processing and analysis
  - `finops_html.py` - HTML report generation
- `cloud_analysis/` - Cloud cost analysis module
  - `finops_cloud_analyzer.py` - Cloud cost analyzer implementation
- `env_analysis/` - Environment analysis module
  - `finops_env_analyzer.py` - Environment analyzer implementation
- `config.yaml` - Default configuration file
- `examples/` - Example configuration files
  - `env_config.yaml` - Environment analysis configuration example
  - Additional period and grouping examples
- `output/` - Generated reports
- `data/` - Input data files
- `docs/` - Documentation files

## Example Outputs

### Cloud Cost Analysis Report

The cloud cost HTML report includes:

- Executive summary with key metrics
- Period and grouping information
- Top investments table by application
- Top efficiencies table by application
- Visualization of cost changes

### Environment Analysis Report (New!)

The environment analysis HTML report includes:

- Overall environment distribution (Prod vs Non-Prod)
- Visual breakdown with progress bars
- Environment costs by organization, VP, and pillar
- List of applications with high non-production costs
- Customizable threshold for flagging high non-prod costs