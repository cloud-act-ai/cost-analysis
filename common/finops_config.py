import yaml
import os
import pandas as pd
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FinOpsConfig:
    """Configuration settings for FinOps analysis."""
    file_path: str
    output_dir: str
    period_type: str
    period_value: str
    year: str
    top_n: int
    generate_html: bool
    export_csv: bool
    page_title: str
    company_name: str
    logo_path: str
    display_columns: list = None     # Configurable columns for reports
    hierarchy: list = None           # Organizational hierarchy for analysis
    nonprod_threshold: float = 20    # Threshold for highlighting high non-prod costs
    top_n_by_level: dict = None      # Level-specific top_n limits
    
    def validate(self, df=None):
        """Validate configuration settings."""
        # Validate period type
        valid_period_types = ['month', 'quarter', 'week', 'year']
        if self.period_type not in valid_period_types:
            raise ValueError(f"Invalid period_type: {self.period_type}. Must be one of {valid_period_types}")
        
        # Validate period value based on type (only if not 'last')
        if self.period_value != 'last':
            if self.period_type == 'month':
                valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                if self.period_value not in valid_months:
                    raise ValueError(f"Invalid month: {self.period_value}. Must be one of {valid_months} or 'last'")
            
            elif self.period_type == 'quarter':
                valid_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
                if self.period_value not in valid_quarters:
                    raise ValueError(f"Invalid quarter: {self.period_value}. Must be one of {valid_quarters} or 'last'")
            
            elif self.period_type == 'week':
                try:
                    week_num = int(self.period_value)
                    if week_num < 1 or week_num > 53:
                        raise ValueError(f"Invalid week number: {self.period_value}. Must be between 1 and 53 or 'last'")
                except ValueError:
                    if self.period_value != 'last':
                        raise ValueError(f"Invalid week number: {self.period_value}. Must be an integer between 1 and 53 or 'last'")
            
            elif self.period_type == 'year':
                if self.period_value != 'current':
                    try:
                        if self.period_value.startswith('FY'):
                            year = int(self.period_value[2:])
                        else:
                            year = int(self.period_value)
                        if year < 2000 or year > 2100:
                            raise ValueError(f"Invalid year: {self.period_value}. Must be between 2000 and 2100, 'current', or 'last'")
                    except ValueError:
                        raise ValueError(f"Invalid year: {self.period_value}. Must be a valid year (e.g., 2023, FY2023), 'current', or 'last'")
        
        # Validate year if it's not 'current'
        if self.year != 'current':
            try:
                if self.year.startswith('FY'):
                    year_value = int(self.year[2:])
                else:
                    year_value = int(self.year)
                if year_value < 2000 or year_value > 2100:
                    raise ValueError(f"Invalid year: {self.year}. Must be between 2000 and 2100 or 'current'")
            except ValueError:
                raise ValueError(f"Invalid year: {self.year}. Must be a valid year (e.g., 2023, FY2023) or 'current'")
        
        # Validate that we have a hierarchy defined
        if not self.hierarchy or not isinstance(self.hierarchy, list) or len(self.hierarchy) == 0:
            raise ValueError("Missing or invalid hierarchy configuration. Must be a non-empty list of column names.")
        
        # Validate hierarchy and display columns if dataframe is provided
        if df is not None:
            # Check hierarchy columns
            for column in self.hierarchy:
                if column not in df.columns:
                    raise ValueError(f"Invalid hierarchy column: '{column}'. Must be a column in the dataset. Available columns: {list(df.columns)}")
            
            # Check display columns
            if self.display_columns:
                for col in self.display_columns:
                    if col not in df.columns:
                        raise ValueError(f"Invalid column '{col}' in display_columns. Must be a column in the dataset. Available columns: {list(df.columns)}")
            
            # Ensure environment column exists
            env_column = 'Env' if 'Env' in df.columns else 'environment'
            if env_column not in df.columns:
                raise ValueError(f"Required environment column not found. Need 'Env' or 'environment' column in the dataset.")


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Get display columns if specified
    display_columns = None
    if 'display_columns' in config_data.get('analysis', {}):
        display_columns = config_data['analysis']['display_columns']
    
    # Get organizational hierarchy if specified
    hierarchy = None
    if 'hierarchy' in config_data.get('analysis', {}):
        hierarchy = config_data['analysis']['hierarchy']
    
    # Get nonprod threshold
    nonprod_threshold = 20
    if 'nonprod_threshold' in config_data.get('analysis', {}):
        nonprod_threshold = config_data['analysis']['nonprod_threshold']
    
    # Get top_n by level if specified
    top_n_by_level = None
    if 'top_n_by_level' in config_data.get('analysis', {}):
        top_n_by_level = config_data['analysis']['top_n_by_level']
    
    config = FinOpsConfig(
        file_path=config_data['data']['file_path'],
        output_dir=config_data['data']['output_dir'],
        period_type=config_data['analysis']['period_type'],
        period_value=str(config_data['analysis']['period_value']),
        year=str(config_data['analysis']['year']),
        top_n=config_data['analysis'].get('top_n', 10),
        generate_html=config_data['report']['generate_html'],
        export_csv=config_data['report']['export_csv'],
        page_title=config_data['report'].get('page_title', 'Environment Cost Analysis'),
        company_name=config_data['report'].get('company_name', 'FinOps'),
        logo_path=config_data['report'].get('logo_path', ''),
        display_columns=display_columns,
        hierarchy=hierarchy,
        nonprod_threshold=nonprod_threshold,
        top_n_by_level=top_n_by_level
    )
    
    # Validate configuration
    config.validate()
    
    return config


def validate_config_with_data(config, df):
    """Validate configuration with actual data."""
    config.validate(df)
    

def get_output_filename(config, report_type, current_period_display=None, extension="html"):
    """Generate output filename with descriptive naming."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Format the parent grouping in a readable way
    parent_info = f"{config.parent_grouping}_{config.parent_grouping_value}".replace(" ", "_")
    
    # Create a clean period info string if provided
    period_info = ""
    if current_period_display:
        period_info = f"{config.period_type}_{current_period_display}".replace(" ", "_")
    else:
        period_info = f"{config.period_type}_{config.period_value}_{config.year}"
    
    # Generate final filename
    return f"{config.output_dir}/{report_type}_report_{parent_info}_{period_info}_{timestamp}.{extension}"
