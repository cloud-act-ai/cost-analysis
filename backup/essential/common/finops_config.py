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
    skip_hierarchy_analysis: bool = False  # Set to True if hierarchy columns are missing
    
    # BigQuery settings
    use_bigquery: bool = False
    bigquery_project_id: str = None
    bigquery_dataset: str = None
    bigquery_table: str = None
    bigquery_credentials: str = None
    use_bqdf: bool = True           # Whether to use BigQuery DataFrames
    selected_columns: list = None   # Columns to select from BigQuery
    
    def get(self, key, default=None):
        """Dictionary-like getter for compatibility with existing code."""
        if hasattr(self, key):
            return getattr(self, key)
        return default
    
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
        
        # Validate BigQuery settings if enabled
        if self.use_bigquery:
            if not self.bigquery_project_id:
                raise ValueError("Missing BigQuery project_id. When use_bigquery is True, project_id must be provided.")
            if not self.bigquery_dataset:
                raise ValueError("Missing BigQuery dataset. When use_bigquery is True, dataset must be provided.")
            if not self.bigquery_table:
                raise ValueError("Missing BigQuery table. When use_bigquery is True, table must be provided.")
        
        # Validate hierarchy and display columns if dataframe is provided
        if df is not None:
            # Check if we can use hierarchy-based analysis
            missing_hierarchy_columns = []
            for column in self.hierarchy:
                if column not in df.columns:
                    missing_hierarchy_columns.append(column)
            
            if missing_hierarchy_columns:
                print(f"Warning: The following hierarchy columns are missing: {missing_hierarchy_columns}")
                print(f"Available columns: {sorted(list(df.columns))}")
                print("Will disable hierarchy-based analysis and perform environment-only analysis.")
                # Disable hierarchy analysis by setting hierarchy to empty
                self.skip_hierarchy_analysis = True
            else:
                self.skip_hierarchy_analysis = False
            
            # Check display columns
            if self.display_columns:
                valid_display_columns = []
                for col in self.display_columns:
                    if col in df.columns:
                        valid_display_columns.append(col)
                    else:
                        print(f"Warning: Display column '{col}' not found in dataset. Skipping.")
                # Update display columns to only include valid ones
                self.display_columns = valid_display_columns
            
            # Ensure environment column exists
            env_column = 'Env' if 'Env' in df.columns else 'environment'
            if env_column not in df.columns:
                raise ValueError(f"Required environment column not found. Need 'Env' or 'environment' column in the dataset.")
            
            # Check selected columns if specified
            if self.use_bigquery and self.selected_columns:
                for col in self.selected_columns:
                    if col not in df.columns:
                        print(f"Warning: Column '{col}' in selected_columns is not present in the loaded data. It may be a case sensitivity or naming issue.")


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
    
    # Get BigQuery settings if specified
    use_bigquery = False
    bigquery_project_id = None
    bigquery_dataset = None
    bigquery_table = None
    use_bqdf = True
    selected_columns = None
    
    if 'bigquery' in config_data:
        bigquery_project_id = config_data['bigquery'].get('project_id')
        bigquery_dataset = config_data['bigquery'].get('dataset')
        bigquery_table = config_data['bigquery'].get('table')
        use_bigquery = config_data['bigquery'].get('use_bigquery', False)
        use_bqdf = config_data['bigquery'].get('use_bqdf', True)
        selected_columns = config_data['bigquery'].get('selected_columns')
    
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
        top_n_by_level=top_n_by_level,
        use_bigquery=use_bigquery,
        bigquery_project_id=bigquery_project_id,
        bigquery_dataset=bigquery_dataset,
        bigquery_table=bigquery_table,
        use_bqdf=use_bqdf,
        selected_columns=selected_columns
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
