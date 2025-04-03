import pandas as pd
import os
from jinja2 import Template
from datetime import datetime


def format_currency(value):
    """Format numeric value as currency."""
    return f"${value:,.2f}"


def format_percent(value, include_sign=True):
    """Format numeric value as percentage with optional sign."""
    if include_sign and value > 0:
        return f"+{value:.2f}%"
    return f"{value:.2f}%"


def format_change(value):
    """Format change value with sign."""
    prefix = '+' if value > 0 else ''
    return f"{prefix}{format_currency(value)}"


def generate_html_report(config, analysis_results, current_period_display, previous_period_display):
    """Generate HTML report from analysis results."""
    
    # Create directory if it doesn't exist
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Prepare data for template
    top_investments = analysis_results['top_investments']
    top_efficiencies = analysis_results['top_efficiencies']
    
    # Format investment data for HTML table
    investments_data = []
    for _, row in top_investments.iterrows():
        investments_data.append({
            'name': row[config.child_grouping],
            'previous_cost': format_currency(row['Total_Cost_previous']),
            'current_cost': format_currency(row['Total_Cost_current']),
            'change': format_change(row['Change']),
            'percent_change': format_percent(row['Percent_Change'], True),
            'percent_value': row['Percent_Change']  # Raw value for conditional styling
        })
    
    # Format efficiency data for HTML table
    efficiencies_data = []
    for _, row in top_efficiencies.iterrows():
        efficiencies_data.append({
            'name': row[config.child_grouping],
            'previous_cost': format_currency(row['Total_Cost_previous']),
            'current_cost': format_currency(row['Total_Cost_current']),
            'change': format_change(row['Change']),
            'percent_change': format_percent(abs(row['Percent_Change']), False),
            'percent_value': row['Percent_Change']  # Raw value for conditional styling
        })
    
    # Format summary data
    summary = {
        'previous_spend': format_currency(analysis_results['total_previous']),
        'current_spend': format_currency(analysis_results['total_current']),
        'efficiencies': format_change(analysis_results['efficiencies']),
        'investments': format_change(analysis_results['investments']),
        'net_change': format_change(analysis_results['net_change']),
        'percent_change': format_percent(analysis_results['percent_change'])
    }
    
    # Get period type name for display
    period_type_display = {
        'month': 'Month',
        'quarter': 'Quarter',
        'week': 'Week',
        'year': 'Year'
    }.get(config.period_type.lower(), 'Period')
    
    # Generate HTML using Jinja2 template
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Spend Management Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.5;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            font-size: 14px;
            background-color: #f9f9f9;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }
        .header-title {
            color: #0066cc;
            font-size: 22px;
            font-weight: 600;
        }
        .company-name {
            font-size: 18px;
            color: #555;
        }
        .summary-box {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .summary-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #0066cc;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        .summary-item {
            margin-bottom: 10px;
        }
        .summary-label {
            font-weight: 500;
            display: block;
            color: #555;
            font-size: 13px;
        }
        .summary-value {
            font-size: 18px;
            color: #333;
            font-weight: 600;
        }
        .period-info {
            font-weight: bold;
            color: #0066cc;
        }
        .positive {
            color: #c62828 !important;  /* Red for cost increases */
        }
        .negative {
            color: #2e7d32 !important;  /* Green for cost decreases */
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            background-color: #fff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background-color: #f2f7ff;
            font-weight: 600;
            color: #0066cc;
            font-size: 13px;
        }
        tr:last-child td {
            border-bottom: none;
        }
        tr:hover {
            background-color: #f5f9ff;
        }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin: 25px 0 15px;
            color: #0066cc;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }
        .report-subtitle {
            color: #555;
            margin-bottom: 20px;
            font-size: 15px;
            background-color: #f2f7ff;
            padding: 10px 15px;
            border-radius: 4px;
            border-left: 4px solid #0066cc;
        }
        footer {
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            color: #777;
            font-size: 12px;
            text-align: center;
        }
        .empty-table-msg {
            text-align: center;
            padding: 20px;
            color: #777;
            font-style: italic;
        }
        .cost-column {
            text-align: right;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-title">Cloud Spend Management Report</div>
        <div class="company-name">{{ company_name }} | FinOps Strategy</div>
    </header>
    
    <div class="report-subtitle">
        <strong>{{ period_type }} Report:</strong> {{ current_period }} compared to {{ previous_period }}<br>
        <strong>{{ parent_grouping }}:</strong> {{ parent_grouping_value }}
    </div>
    
    <div class="summary-box">
        <div class="summary-title">Executive Summary</div>
        <div class="summary-grid">
            <div class="summary-item">
                <span class="summary-label">{{ previous_period }} Spend</span>
                <div class="summary-value">{{ summary.previous_spend }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">{{ current_period }} Spend</span>
                <div class="summary-value">{{ summary.current_spend }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Net Change</span>
                <div class="summary-value {% if summary.net_change.startswith('+') %}positive{% else %}negative{% endif %}">
                    {{ summary.net_change }} ({{ summary.percent_change }})
                </div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Cost Reduction (Efficiencies)</span>
                <div class="summary-value negative">{{ summary.efficiencies }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Cost Increase (Investments)</span>
                <div class="summary-value positive">{{ summary.investments }}</div>
            </div>
        </div>
    </div>
    
    <div class="section-title">Top {{ top_n }} Investments by {{ child_grouping }}</div>
    <table>
        <thead>
            <tr>
                <th>{{ child_grouping }}</th>
                <th class="cost-column">Previous Cost</th>
                <th class="cost-column">Current Cost</th>
                <th class="cost-column">Change</th>
                <th class="cost-column">% Change</th>
            </tr>
        </thead>
        <tbody>
            {% for item in investments %}
            <tr>
                <td>{{ item.name }}</td>
                <td class="cost-column">{{ item.previous_cost }}</td>
                <td class="cost-column">{{ item.current_cost }}</td>
                <td class="cost-column positive">{{ item.change }}</td>
                <td class="cost-column positive">{{ item.percent_change }}</td>
            </tr>
            {% endfor %}
            {% if investments|length == 0 %}
            <tr>
                <td colspan="5" class="empty-table-msg">No significant investments found in this period</td>
            </tr>
            {% endif %}
        </tbody>
    </table>
    
    <div class="section-title">Top {{ top_n }} Efficiencies by {{ child_grouping }}</div>
    <table>
        <thead>
            <tr>
                <th>{{ child_grouping }}</th>
                <th class="cost-column">Previous Cost</th>
                <th class="cost-column">Current Cost</th>
                <th class="cost-column">Change</th>
                <th class="cost-column">% Change</th>
            </tr>
        </thead>
        <tbody>
            {% for item in efficiencies %}
            <tr>
                <td>{{ item.name }}</td>
                <td class="cost-column">{{ item.previous_cost }}</td>
                <td class="cost-column">{{ item.current_cost }}</td>
                <td class="cost-column negative">{{ item.change }}</td>
                <td class="cost-column negative">-{{ item.percent_change }}</td>
            </tr>
            {% endfor %}
            {% if efficiencies|length == 0 %}
            <tr>
                <td colspan="5" class="empty-table-msg">No significant efficiencies found in this period</td>
            </tr>
            {% endif %}
        </tbody>
    </table>
    
    <footer>
        Generated on {{ timestamp }} | FinOps Strategy
    </footer>
</body>
</html>
    """
    
    template = Template(html_template)
    rendered_html = template.render(
        company_name=config.company_name,
        parent_grouping=config.parent_grouping,
        parent_grouping_value=config.parent_grouping_value,
        child_grouping=config.child_grouping,
        top_n=config.top_n,
        current_period=current_period_display,
        previous_period=previous_period_display,
        period_type=period_type_display,
        summary=summary,
        investments=investments_data,
        efficiencies=efficiencies_data,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Generate a more descriptive filename
    output_filename = get_output_filename(config, current_period_display)
    
    with open(output_filename, 'w') as f:
        f.write(rendered_html)
    
    return output_filename


def get_output_filename(config, current_period_display):
    """Generate output filename with descriptive naming."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Format the parent grouping in a readable way
    parent_info = f"{config.parent_grouping}_{config.parent_grouping_value}".replace(" ", "_")
    
    # Create a clean period info string
    period_info = f"{config.period_type}_{current_period_display}".replace(" ", "_")
    
    # Generate final filename
    return f"{config.output_dir}/cloud_spend_report_{parent_info}_{period_info}_{timestamp}.html"