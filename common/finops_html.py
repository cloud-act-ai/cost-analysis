import pandas as pd
import os
from jinja2 import Template
from datetime import datetime
from common.finops_config import get_output_filename


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
        'percent_change': format_percent(analysis_results['percent_change']),
        'raw_net_change': analysis_results['net_change']
    }
    
    # Get period type name for display
    period_type_display = {
        'month': 'Month',
        'quarter': 'Quarter',
        'week': 'Week',
        'year': 'Year'
    }.get(config.period_type.lower(), 'Period')
    
    # Get some insights from the data
    has_investments = len(investments_data) > 0
    has_efficiencies = len(efficiencies_data) > 0
    top_investment = investments_data[0] if has_investments else None
    top_efficiency = efficiencies_data[0] if has_efficiencies else None
    
    # Determine the message based on data
    insight_message = ""
    if analysis_results['net_change'] > 0:
        if has_investments and has_efficiencies:
            insight_message = f"Overall spending has increased by {summary['percent_change']}. Investigate top investments like <strong>{top_investment['name']}</strong> while leveraging successful cost-saving efforts in <strong>{top_efficiency['name']}</strong>."
        elif has_investments:
            insight_message = f"Spending increased by {summary['percent_change']}, primarily driven by <strong>{top_investment['name']}</strong>. Focus on identifying cost optimization opportunities."
        else:
            insight_message = f"Spending increased by {summary['percent_change']}. Review new applications or services to identify optimization targets."
    else:
        if has_efficiencies and has_investments:
            insight_message = f"Great job! Overall spending decreased by {format_percent(abs(analysis_results['percent_change']))} despite some investments. Cost saving efforts in <strong>{top_efficiency['name']}</strong> significantly contributed to this reduction."
        elif has_efficiencies:
            insight_message = f"Excellent! Spending reduced by {format_percent(abs(analysis_results['percent_change']))}. The largest savings came from <strong>{top_efficiency['name']}</strong>."
        else:
            insight_message = f"Spending decreased by {format_percent(abs(analysis_results['percent_change']))}. Continue monitoring for any service impact."
    
    # Generate HTML using Jinja2 template
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Spend Management Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --primary-color: #1a73e8;
            --primary-light: #e8f0fe;
            --primary-dark: #0d47a1;
            --green-color: #0f9d58;
            --green-light: #e6f4ea;
            --red-color: #d93025;
            --red-light: #fce8e6;
            --neutral-light: #f8f9fa;
            --neutral-medium: #dadce0;
            --neutral-dark: #5f6368;
            --text-primary: #202124;
            --text-secondary: #5f6368;
            --shadow-sm: 0 1px 2px rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15);
            --shadow-md: 0 2px 6px rgba(60, 64, 67, 0.15), 0 1px 2px rgba(60, 64, 67, 0.3);
            --radius-sm: 4px;
            --radius-md: 8px;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: var(--font-main);
            line-height: 1.5;
            color: var(--text-primary);
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
            font-size: 14px;
            background-color: var(--neutral-light);
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 16px;
        }
        
        .header-title {
            color: var(--primary-color);
            font-size: 24px;
            font-weight: 600;
        }
        
        .company-name {
            font-size: 18px;
            color: var(--text-secondary);
            background-color: var(--primary-light);
            padding: 6px 12px;
            border-radius: var(--radius-sm);
        }
        
        .report-subtitle {
            color: var(--text-secondary);
            margin-bottom: 24px;
            font-size: 15px;
            background-color: white;
            padding: 16px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            border-left: 4px solid var(--primary-color);
        }
        
        .insight-box {
            background-color: var(--primary-light);
            color: var(--primary-dark);
            padding: 16px;
            border-radius: var(--radius-md);
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
            line-height: 1.6;
            font-size: 15px;
        }
        
        .insight-title {
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 16px;
            display: flex;
            align-items: center;
        }
        
        .insight-title svg {
            margin-right: 8px;
        }
        
        .summary-box {
            background-color: white;
            border-radius: var(--radius-md);
            padding: 20px;
            margin-bottom: 32px;
            box-shadow: var(--shadow-md);
        }
        
        .summary-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--primary-color);
            border-bottom: 1px solid var(--neutral-medium);
            padding-bottom: 12px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        
        .summary-item {
            padding: 16px;
            border-radius: var(--radius-sm);
            background-color: var(--neutral-light);
        }
        
        .summary-label {
            font-weight: 500;
            display: block;
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 4px;
        }
        
        .summary-value {
            font-size: 20px;
            color: var(--text-primary);
            font-weight: 600;
        }
        
        .period-info {
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .positive {
            color: var(--red-color) !important;  /* Red for cost increases */
        }
        
        .negative {
            color: var(--green-color) !important;  /* Green for cost decreases */
        }
        
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge-positive {
            background-color: var(--red-light);
            color: var(--red-color);
        }
        
        .badge-negative {
            background-color: var(--green-light);
            color: var(--green-color);
        }
        
        .highlight-box {
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        
        .highlight-card {
            background-color: white;
            border-radius: var(--radius-sm);
            padding: 16px;
            box-shadow: var(--shadow-sm);
        }
        
        .highlight-card-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .highlight-card-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--neutral-medium);
        }
        
        .highlight-card-content:last-child {
            border-bottom: none;
        }
        
        .highlight-name {
            font-weight: 500;
        }
        
        .highlight-value {
            font-weight: 600;
        }
        
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-bottom: 32px;
            background-color: white;
            box-shadow: var(--shadow-md);
            border-radius: var(--radius-md);
            overflow: hidden;
        }
        
        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--neutral-medium);
        }
        
        th {
            background-color: var(--primary-light);
            font-weight: 600;
            color: var(--primary-dark);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        tr:hover {
            background-color: var(--neutral-light);
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin: 32px 0 16px;
            color: var(--primary-color);
            display: flex;
            align-items: center;
        }
        
        .section-title svg {
            margin-right: 8px;
        }
        
        footer {
            margin-top: 48px;
            padding-top: 16px;
            border-top: 1px solid var(--neutral-medium);
            color: var(--text-secondary);
            font-size: 12px;
            text-align: center;
        }
        
        .empty-table-msg {
            text-align: center;
            padding: 24px;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        .cost-column {
            text-align: right;
        }
        
        /* Icon for trend */
        .trend-icon {
            display: inline-block;
            width: 0;
            height: 0;
            margin-right: 4px;
        }
        
        .trend-up {
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-bottom: 8px solid var(--red-color);
        }
        
        .trend-down {
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 8px solid var(--green-color);
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .highlight-box {
                grid-template-columns: 1fr;
            }
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
    
    <div class="insight-box">
        <div class="insight-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#1a73e8" stroke-width="2"/>
                <path d="M12 8V13" stroke="#1a73e8" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="16" r="1" fill="#1a73e8"/>
            </svg>
            Key Insight
        </div>
        {{ insight_message }}
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
                <div class="summary-value {% if summary.raw_net_change > 0 %}positive{% else %}negative{% endif %}">
                    {% if summary.raw_net_change > 0 %}
                    <span class="trend-icon trend-up"></span>
                    {% else %}
                    <span class="trend-icon trend-down"></span>
                    {% endif %}
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
    
    <div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22V2M12 2L6 8M12 2L18 8" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Top {{ top_n }} Investments by {{ child_grouping }}
    </div>
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
                <td class="cost-column positive">
                    <span class="badge badge-positive">{{ item.percent_change }}</span>
                </td>
            </tr>
            {% endfor %}
            {% if investments|length == 0 %}
            <tr>
                <td colspan="5" class="empty-table-msg">No significant investments found in this period</td>
            </tr>
            {% endif %}
        </tbody>
    </table>
    
    <div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2V22M12 22L6 16M12 22L18 16" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Top {{ top_n }} Efficiencies by {{ child_grouping }}
    </div>
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
                <td class="cost-column negative">
                    <span class="badge badge-negative">-{{ item.percent_change }}</span>
                </td>
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
        insight_message=insight_message,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Generate a more descriptive filename
    output_filename = get_output_filename(config, "cloud_spend", current_period_display)
    
    with open(output_filename, 'w') as f:
        f.write(rendered_html)
    
    return output_filename


def generate_env_report_html(config, env_analysis):
    """Generate HTML report for environment analysis (Prod vs Non-Prod)."""
    
    # Create directory if it doesn't exist
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Get overall data
    overall = env_analysis['overall']
    hierarchical = env_analysis['hierarchical']
    hierarchy = env_analysis.get('hierarchy', [])
    
    # Format summary data
    summary = {
        'total_cost': format_currency(overall['total_cost']),
        'prod_cost': format_currency(overall['prod_cost']),
        'nonprod_cost': format_currency(overall['nonprod_cost']),
        'prod_percentage': format_percent(overall['prod_percentage'], False),
        'nonprod_percentage': format_percent(overall['nonprod_percentage'], False),
    }
    
    # Format environment breakdown data for HTML table
    env_breakdown_data = []
    for _, row in overall['env_breakdown'].iterrows():
        env_breakdown_data.append({
            'name': row['Environment'],
            'cost': format_currency(row['Cost']),
            'percentage': format_percent(row['Percentage'], False),
            'type': row['Type'],
            'raw_percentage': row['Percentage']  # Raw value for conditional styling
        })
    
    # Format hierarchical data
    hierarchy_data = {}
    hierarchy_levels = hierarchical.get('hierarchy_levels', {})
    nonprod_threshold = hierarchical.get('nonprod_threshold', 20)
    
    # Process each level of the hierarchy
    for level in hierarchy:
        if level in hierarchy_levels:
            level_data = []
            level_analysis = hierarchy_levels[level]
            
            # Get group environment data (the main table)
            if not level_analysis['group_env_data'].empty:
                for _, row in level_analysis['group_env_data'].iterrows():
                    level_data.append({
                        'name': row[level],
                        'total_cost': format_currency(row['Total_Cost']),
                        'prod_percentage': format_percent(row.get('Production', 0), False),
                        'nonprod_percentage': format_percent(row.get('Non-Production', 0), False),
                        'other_percentage': format_percent(row.get('Other', 0), False),
                        'raw_nonprod': row.get('Non-Production', 0)  # Raw value for conditional styling
                    })
            
            # Store formatted data
            hierarchy_data[level] = {
                'data': level_data,
                'display_name': level.replace('_', ' ').title(),
                'high_nonprod': []
            }
            
            # Get high non-prod items
            if not level_analysis['high_nonprod_groups'].empty:
                for _, row in level_analysis['high_nonprod_groups'].iterrows():
                    hierarchy_data[level]['high_nonprod'].append({
                        'name': row[level],
                        'total_cost': format_currency(row['Total_Cost']),
                        'prod_percentage': format_percent(row.get('Production', 0), False),
                        'nonprod_percentage': format_percent(row.get('Non-Production', 0), False),
                        'other_percentage': format_percent(row.get('Other', 0), False),
                        'raw_nonprod': row.get('Non-Production', 0)
                    })
            
            # Process child data
            child_key = f"{level}_children"
            if child_key in hierarchy_levels:
                children_data = hierarchy_levels[child_key]
                
                # For each parent item, get its children
                parent_children = {}
                for parent_name, child_analysis in children_data.items():
                    child_items = []
                    
                    if not child_analysis['group_env_data'].empty:
                        next_level = hierarchy[hierarchy.index(level) + 1]
                        for _, row in child_analysis['group_env_data'].iterrows():
                            child_items.append({
                                'name': row[next_level],
                                'total_cost': format_currency(row['Total_Cost']),
                                'prod_percentage': format_percent(row.get('Production', 0), False),
                                'nonprod_percentage': format_percent(row.get('Non-Production', 0), False),
                                'other_percentage': format_percent(row.get('Other', 0), False),
                                'raw_nonprod': row.get('Non-Production', 0)
                            })
                    
                    parent_children[parent_name] = child_items
                
                # Store parent-child relationships
                hierarchy_data[level]['children'] = parent_children
    
    # Generate HTML using Jinja2 template
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Environment Cost Analysis Report</title>
    <!-- No JavaScript needed for simplified report -->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --primary-color: #1a73e8;
            --primary-light: #e8f0fe;
            --primary-dark: #0d47a1;
            --green-color: #0f9d58;
            --green-light: #e6f4ea;
            --red-color: #d93025;
            --red-light: #fce8e6;
            --neutral-light: #f8f9fa;
            --neutral-medium: #dadce0;
            --neutral-dark: #5f6368;
            --text-primary: #202124;
            --text-secondary: #5f6368;
            --shadow-sm: 0 1px 2px rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15);
            --shadow-md: 0 2px 6px rgba(60, 64, 67, 0.15), 0 1px 2px rgba(60, 64, 67, 0.3);
            --radius-sm: 4px;
            --radius-md: 8px;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: var(--font-main);
            line-height: 1.5;
            color: var(--text-primary);
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
            font-size: 14px;
            background-color: var(--neutral-light);
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 16px;
        }
        
        .header-title {
            color: var(--primary-color);
            font-size: 24px;
            font-weight: 600;
        }
        
        .company-name {
            font-size: 18px;
            color: var(--text-secondary);
            background-color: var(--primary-light);
            padding: 6px 12px;
            border-radius: var(--radius-sm);
        }
        
        .report-subtitle {
            color: var(--text-secondary);
            margin-bottom: 24px;
            font-size: 15px;
            background-color: white;
            padding: 16px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            border-left: 4px solid var(--primary-color);
        }
        
        .summary-box {
            background-color: white;
            border-radius: var(--radius-md);
            padding: 20px;
            margin-bottom: 32px;
            box-shadow: var(--shadow-md);
        }
        
        .summary-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--primary-color);
            border-bottom: 1px solid var(--neutral-medium);
            padding-bottom: 12px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        
        .summary-item {
            padding: 16px;
            border-radius: var(--radius-sm);
            background-color: var(--neutral-light);
        }
        
        .summary-label {
            font-weight: 500;
            display: block;
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 4px;
        }
        
        .summary-value {
            font-size: 20px;
            color: var(--text-primary);
            font-weight: 600;
        }
        
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge-prod {
            background-color: var(--green-light);
            color: var(--green-color);
        }
        
        .badge-nonprod {
            background-color: var(--red-light);
            color: var(--red-color);
        }
        
        .badge-other {
            background-color: var(--neutral-medium);
            color: var(--neutral-dark);
        }
        
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-bottom: 32px;
            background-color: white;
            box-shadow: var(--shadow-md);
            border-radius: var(--radius-md);
            overflow: hidden;
        }
        
        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--neutral-medium);
        }
        
        th {
            background-color: var(--primary-light);
            font-weight: 600;
            color: var(--primary-dark);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        tr:hover {
            background-color: var(--neutral-light);
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin: 32px 0 16px;
            color: var(--primary-color);
            display: flex;
            align-items: center;
        }
        
        .section-title svg {
            margin-right: 8px;
        }
        
        footer {
            margin-top: 48px;
            padding-top: 16px;
            border-top: 1px solid var(--neutral-medium);
            color: var(--text-secondary);
            font-size: 12px;
            text-align: center;
        }
        
        .empty-table-msg {
            text-align: center;
            padding: 24px;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        .cost-column {
            text-align: right;
        }
        
        .progress-bar-container {
            width: 100%;
            height: 12px;
            background-color: var(--neutral-light);
            border-radius: 6px;
            overflow: hidden;
            margin-top: 6px;
        }
        
        .progress-bar {
            height: 100%;
            float: left;
        }
        
        .progress-bar-prod {
            background-color: var(--green-color);
        }
        
        .progress-bar-nonprod {
            background-color: var(--red-color);
        }
        
        .progress-bar-other {
            background-color: var(--neutral-dark);
        }
        
        .percentage-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 8px;
        }
        
        .percentage-item {
            text-align: center;
            font-size: 12px;
        }
        
        .percentage-value {
            font-weight: 600;
            font-size: 14px;
        }
        
        .env-type-prod {
            color: var(--green-color);
        }
        
        .env-type-nonprod {
            color: var(--red-color);
        }
        
        .env-type-other {
            color: var(--neutral-dark);
        }
        
        /* Remove warning-row styling */
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Hierarchy-specific styles */
        .table-container {
            margin-bottom: 20px;
            overflow-x: auto;
        }
        
        .child-container {
            padding: 10px 20px;
            background-color: var(--primary-light);
            border-radius: var(--radius-sm);
        }
        
        .child-table-wrapper {
            margin: 10px 0;
        }
        
        .child-table-wrapper h4 {
            margin-bottom: 10px;
            color: var(--primary-dark);
        }
        
        .child-table {
            width: 100%;
            background-color: white;
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-sm);
        }
        
        .child-table th {
            background-color: var(--primary-light);
            color: var(--primary-dark);
            font-weight: 600;
            text-align: left;
            padding: 8px 12px;
        }
        
        .child-table td {
            padding: 8px 12px;
            border-bottom: 1px solid var(--neutral-medium);
        }
        
        .expand-button {
            background-color: var(--primary-light);
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
            border-radius: var(--radius-sm);
            padding: 4px 8px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .expand-button:hover {
            background-color: var(--primary-color);
            color: white;
        }
        
        .section-divider {
            margin: 30px 0;
            border: 0;
            border-top: 1px solid var(--neutral-medium);
        }
        
        .subsection-title {
            font-size: 16px;
            font-weight: 500;
            margin: 20px 0 10px;
            color: var(--red-color);
            display: flex;
            align-items: center;
        }
        
        .subsection-title svg {
            margin-right: 8px;
        }
        
        .warning-table {
            border: 1px solid var(--red-light);
        }
        
        .warning-table th {
            background-color: var(--red-light);
            color: var(--red-color);
        }
    </style>
</head>
<body>
    <header>
        <div class="header-title">Environment Cost Analysis Report</div>
        <div class="company-name">{{ company_name }} | FinOps Strategy</div>
    </header>
    
    <div class="report-subtitle">
        <strong>Environment Analysis:</strong> Production vs. Non-Production Costs
        {% if parent_grouping and parent_grouping_value %}
        <br><strong>{{ parent_grouping }}:</strong> {{ parent_grouping_value }}
        {% endif %}
    </div>
    
    <div class="summary-box">
        <div class="summary-title">Overall Environment Distribution</div>
        <div class="summary-grid">
            <div class="summary-item">
                <span class="summary-label">Total Cost</span>
                <div class="summary-value">{{ summary.total_cost }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Production Cost</span>
                <div class="summary-value env-type-prod">{{ summary.prod_cost }} ({{ summary.prod_percentage }})</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Non-Production Cost</span>
                <div class="summary-value env-type-nonprod">{{ summary.nonprod_cost }} ({{ summary.nonprod_percentage }})</div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <div class="progress-bar-container">
                <div class="progress-bar progress-bar-prod" style="width: {{ overall.prod_percentage }}%;"></div>
                <div class="progress-bar progress-bar-nonprod" style="width: {{ overall.nonprod_percentage }}%;"></div>
                {% if 100 - overall.prod_percentage - overall.nonprod_percentage > 0 %}
                <div class="progress-bar progress-bar-other" style="width: {{ 100 - overall.prod_percentage - overall.nonprod_percentage }}%;"></div>
                {% endif %}
            </div>
            <div class="percentage-grid">
                <div class="percentage-item">
                    <div class="percentage-value env-type-prod">{{ summary.prod_percentage }}</div>
                    <div>Production</div>
                </div>
                <div class="percentage-item">
                    <div class="percentage-value env-type-nonprod">{{ summary.nonprod_percentage }}</div>
                    <div>Non-Production</div>
                </div>
                {% if 100 - overall.prod_percentage - overall.nonprod_percentage > 0 %}
                <div class="percentage-item">
                    <div class="percentage-value env-type-other">{{ 100 - overall.prod_percentage - overall.nonprod_percentage|float|round(2) }}%</div>
                    <div>Other/Unknown</div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 3h18v18H3V3z" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 9h18M9 3v18" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Environment Breakdown by Type
    </div>
    <table>
        <thead>
            <tr>
                <th>Environment</th>
                <th class="cost-column">Cost</th>
                <th class="cost-column">Percentage</th>
                <th>Type</th>
            </tr>
        </thead>
        <tbody>
            {% for item in env_breakdown %}
            <tr>
                <td>{{ item.name }}</td>
                <td class="cost-column">{{ item.cost }}</td>
                <td class="cost-column">{{ item.percentage }}</td>
                <td>
                    {% if item.type == 'Production' %}
                    <span class="badge badge-prod">Production</span>
                    {% elif item.type == 'Non-Production' %}
                    <span class="badge badge-nonprod">Non-Production</span>
                    {% else %}
                    <span class="badge badge-other">Other</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
            {% if env_breakdown|length == 0 %}
            <tr>
                <td colspan="4" class="empty-table-msg">No environment data available</td>
            </tr>
            {% endif %}
        </tbody>
    </table>
    
    {% if by_org_data|length > 0 %}
    <div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 3L2 12h3v8h14v-8h3L12 3z" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 21v-6h6v6" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Environment Distribution by Organization
    </div>
    <table>
        <thead>
            <tr>
                <th>Organization</th>
                <th class="cost-column">Total Cost</th>
                <th>Prod/Non-Prod Split</th>
                <th class="cost-column">Production %</th>
                <th class="cost-column">Non-Production %</th>
            </tr>
        </thead>
        <tbody>
            {% for item in by_org_data %}
            <tr {% if item.raw_nonprod >= nonprod_threshold %}class="warning-row"{% endif %}>
                <td>{{ item.name }}</td>
                <td class="cost-column">{{ item.total_cost }}</td>
                <td>
                    <div class="progress-bar-container">
                        <div class="progress-bar progress-bar-prod" style="width: {{ item.prod_percentage|replace('%', '') }}%;"></div>
                        <div class="progress-bar progress-bar-nonprod" style="width: {{ item.nonprod_percentage|replace('%', '') }}%;"></div>
                        {% if item.other_percentage and item.other_percentage != '0.00%' %}
                        <div class="progress-bar progress-bar-other" style="width: {{ item.other_percentage|replace('%', '') }}%;"></div>
                        {% endif %}
                    </div>
                </td>
                <td class="cost-column env-type-prod">{{ item.prod_percentage }}</td>
                <td class="cost-column env-type-nonprod">{{ item.nonprod_percentage }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    {% if by_vp_data|length > 0 %}
    <div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="8.5" cy="7" r="4" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M20 8v6m-3-3h6" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Environment Distribution by VP
    </div>
    <table>
        <thead>
            <tr>
                <th>VP</th>
                <th class="cost-column">Total Cost</th>
                <th>Prod/Non-Prod Split</th>
                <th class="cost-column">Production %</th>
                <th class="cost-column">Non-Production %</th>
            </tr>
        </thead>
        <tbody>
            {% for item in by_vp_data %}
            <tr {% if item.raw_nonprod >= nonprod_threshold %}class="warning-row"{% endif %}>
                <td>{{ item.name }}</td>
                <td class="cost-column">{{ item.total_cost }}</td>
                <td>
                    <div class="progress-bar-container">
                        <div class="progress-bar progress-bar-prod" style="width: {{ item.prod_percentage|replace('%', '') }}%;"></div>
                        <div class="progress-bar progress-bar-nonprod" style="width: {{ item.nonprod_percentage|replace('%', '') }}%;"></div>
                        {% if item.other_percentage and item.other_percentage != '0.00%' %}
                        <div class="progress-bar progress-bar-other" style="width: {{ item.other_percentage|replace('%', '') }}%;"></div>
                        {% endif %}
                    </div>
                </td>
                <td class="cost-column env-type-prod">{{ item.prod_percentage }}</td>
                <td class="cost-column env-type-nonprod">{{ item.nonprod_percentage }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    {# Render each level of the hierarchy #}
    {% for level in hierarchy %}
        {% if level in hierarchy_data and hierarchy_data[level].data|length > 0 %}
        <div class="section-title" id="section-{{ level }}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2z" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 9h6m-6 6h6" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Environment Distribution by {{ hierarchy_data[level].display_name }}
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>{{ hierarchy_data[level].display_name }}</th>
                        <th class="cost-column">Total Cost</th>
                        <th>Prod/Non-Prod Split</th>
                        <th class="cost-column">Production %</th>
                        <th class="cost-column">Non-Production %</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in hierarchy_data[level].data %}
                    <tr>
                        <td>{{ item.name }}</td>
                        <td class="cost-column">{{ item.total_cost }}</td>
                        <td>
                            <div class="progress-bar-container">
                                <div class="progress-bar progress-bar-prod" style="width: {{ item.prod_percentage|replace('%', '') }}%;"></div>
                                <div class="progress-bar progress-bar-nonprod" style="width: {{ item.nonprod_percentage|replace('%', '') }}%;"></div>
                                {% if item.other_percentage and item.other_percentage != '0.00%' %}
                                <div class="progress-bar progress-bar-other" style="width: {{ item.other_percentage|replace('%', '') }}%;"></div>
                                {% endif %}
                            </div>
                        </td>
                        <td class="cost-column env-type-prod">{{ item.prod_percentage }}</td>
                        <td class="cost-column env-type-nonprod">{{ item.nonprod_percentage }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <hr class="section-divider">
        {% endif %}
    {% endfor %}
    
    <div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 9v2m0 4h.01m-6.99 4h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Applications with High Non-Production Costs (>= {{ nonprod_threshold }}%)
    </div>
    <table>
        <thead>
            <tr>
                <th>{{ grouping_column }}</th>
                <th class="cost-column">Total Cost</th>
                <th>Prod/Non-Prod Split</th>
                <th class="cost-column">Production %</th>
                <th class="cost-column">Non-Production %</th>
            </tr>
        </thead>
        <tbody>
            {% for item in high_nonprod %}
            <tr>
                <td>{{ item.name }}</td>
                <td class="cost-column">{{ item.total_cost }}</td>
                <td>
                    <div class="progress-bar-container">
                        <div class="progress-bar progress-bar-prod" style="width: {{ item.prod_percentage|replace('%', '') }}%;"></div>
                        <div class="progress-bar progress-bar-nonprod" style="width: {{ item.nonprod_percentage|replace('%', '') }}%;"></div>
                        {% if item.other_percentage and item.other_percentage != '0.00%' %}
                        <div class="progress-bar progress-bar-other" style="width: {{ item.other_percentage|replace('%', '') }}%;"></div>
                        {% endif %}
                    </div>
                </td>
                <td class="cost-column env-type-prod">{{ item.prod_percentage }}</td>
                <td class="cost-column env-type-nonprod">{{ item.nonprod_percentage }}</td>
            </tr>
            {% endfor %}
            {% if high_nonprod|length == 0 %}
            <tr>
                <td colspan="5" class="empty-table-msg">No applications found with high non-production costs</td>
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
    
    # Extract high non-prod applications for the warning section
    high_nonprod_data = []
    application_level = hierarchy[-1] if hierarchy else None
    
    if application_level and application_level in hierarchy_levels:
        level_analysis = hierarchy_levels[application_level]
        if 'high_nonprod_groups' in level_analysis and not level_analysis['high_nonprod_groups'].empty:
            for _, row in level_analysis['high_nonprod_groups'].iterrows():
                high_nonprod_data.append({
                    'name': row[application_level],
                    'total_cost': format_currency(row['Total_Cost']),
                    'prod_percentage': format_percent(row.get('Production', 0), False),
                    'nonprod_percentage': format_percent(row.get('Non-Production', 0), False),
                    'other_percentage': format_percent(row.get('Other', 0), False),
                    'raw_nonprod': row.get('Non-Production', 0)
                })
    
    template = Template(html_template)
    rendered_html = template.render(
        company_name=config.company_name,
        period_type=env_analysis.get('period_type', config.period_type),
        period_value=env_analysis.get('period_value', config.period_value),
        year=env_analysis.get('year', config.year),
        summary=summary,
        overall=overall,
        env_breakdown=env_breakdown_data,
        hierarchy=hierarchy,
        hierarchy_data=hierarchy_data,
        nonprod_threshold=hierarchical.get('nonprod_threshold', 20),
        high_nonprod=high_nonprod_data,
        grouping_column=application_level.replace('_', ' ').title() if application_level else "Application",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Generate a descriptive filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    period_info = f"{env_analysis.get('period_type', config.period_type)}_{env_analysis.get('period_value', config.period_value)}_{env_analysis.get('year', config.year)}"
    output_filename = f"{config.output_dir}/env_analysis_report_{period_info.replace(' ', '_')}_{timestamp}.html"
    
    with open(output_filename, 'w') as f:
        f.write(rendered_html)
    
    return output_filename