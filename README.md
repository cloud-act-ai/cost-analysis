# Cloud Spend Management Tool

A modular Python application for analyzing cloud cost data and generating reports to identify efficiencies and investments.

## Features

- **Flexible Analysis Types**: Support for different time period comparisons:
  - Month-to-month
  - Quarter-to-quarter
  - Week-to-week
  - Year-to-year

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
  - Top N investments and efficiencies

- **Report Generation**:
  - Responsive HTML reports
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

### Basic Usage

Run the analyzer with the default configuration:

```
python finops_analyzer.py
```

### Custom Grouping

Analyze by different grouping columns:

```
python finops_analyzer.py --parent-group VP --parent-value Bob
python finops_analyzer.py --parent-group PILLAR --parent-value Retail
```

### Different Time Periods

Analyze by different time periods:

```
python finops_analyzer.py --period quarter --period-value Q1
python finops_analyzer.py --period week --period-value 11
```

### Example Configurations

Use one of the predefined configurations:

```
python finops_analyzer.py --config examples/vp_config.yaml
python finops_analyzer.py --config examples/pillar_config.yaml
```

## Configuration Options

Edit `config.yaml` to customize analysis parameters:

```yaml
# Time period configuration
period_type: month  # Options: month, quarter, week, year
period_value: Mar   # Month name, quarter (Q1-Q4), week number, or year
year: 2024
  
# Grouping configuration
parent_grouping: VP  # Can be any column in your dataset
parent_grouping_value: Bob  # Value for the parent grouping
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

- `finops_analyzer.py` - Main entry point
- `finops_config.py` - Configuration management
- `finops_data.py` - Data processing and analysis
- `finops_html.py` - HTML report generation
- `init.py` - Environment initialization
- `config.yaml` - Default configuration file
- `examples/` - Example configuration files
- `output/` - Generated reports
- `data/` - Input data files
- `docs/` - Documentation files

## Example Output

The HTML report includes:

- Executive summary with key metrics
- Period and grouping information
- Top investments table by application
- Top efficiencies table by application