# FinOps360 Cost Analysis Tool

A modular Python application for analyzing cloud cost data and generating FinOps reports to identify efficiencies and investments.

## Features

- **Flexible Analysis Types**: Support for different time period comparisons:
  - Month-to-month
  - Quarter-to-quarter
  - Week-to-week
  - Year-to-year

- **Grouping Options**: Analyze costs by:
  - Organization (ORG)
  - Product (TR_PRODUCT)
  - Environment (ENV)
  - Cloud provider (Cloud)

- **Key Analysis Metrics**:
  - Total spend by period
  - Cost efficiencies (reductions)
  - Cost investments (increases)
  - Net change (absolute and percentage)
  - Top N investments and efficiencies

- **Report Generation**:
  - Interactive HTML reports
  - Export options for data

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

## Usage

### Basic Usage

Run the analyzer with the default configuration:

```
python finops_analyzer.py
```

### Custom Configuration

Run with a custom configuration file:

```
python finops_analyzer.py --config examples/quarter_config.yaml
```

### Configuration Options

Edit `config.yaml` to customize analysis parameters:

```yaml
# Time period configuration
period_type: month  # Options: month, quarter, week, year
period_value: Mar   # Month name, quarter (Q1-Q4), week number, or year
year: 2024
  
# Grouping configuration
parent_grouping: ORG  # Can be ORG, TR_PRODUCT, ENV, or Cloud
parent_grouping_value: Starling  # Default value for the parent grouping
```

## Example Configurations

The `examples/` directory contains sample configurations for different analysis types:

- `month_config.yaml` - Month-to-month analysis
- `quarter_config.yaml` - Quarter-to-quarter analysis
- `week_config.yaml` - Week-to-week analysis
- `year_config.yaml` - Year-to-year analysis

## Data Format

The expected CSV format includes the following columns:

- DATE - Date of the cost entry
- WM_WEEK - Week identifier (e.g., Week 11)
- QTR - Quarter identifier (e.g., Q1)
- Month - Month name (e.g., Jan, Feb)
- FY - Fiscal year
- TR_PRODUCT - Product name
- ORG - Organization name
- Application_Name - Application identifier
- Cloud - Cloud provider name
- Env - Environment (e.g., Prod, Dev, Stage)
- Cost - Cost amount

## Project Structure

- `finops_analyzer.py` - Main entry point
- `finops_config.py` - Configuration management
- `finops_data.py` - Data processing and analysis
- `finops_html.py` - HTML report generation
- `config.yaml` - Default configuration file
- `examples/` - Example configuration files
- `output/` - Generated reports
- `data/` - Input data files

## Example Output

The HTML report includes:

- Summary metrics with previous and current period spend
- Efficiencies and investments summary
- Top investments table by application
- Top efficiencies table by application