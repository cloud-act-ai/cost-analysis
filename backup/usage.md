# FinOps360 Usage Guide

## Flexible Analysis Options

The FinOps360 Cost Analysis Tool now supports flexible analysis options, allowing you to analyze your cost data by any column available in your dataset.

## Supported Grouping Columns

You can use any column in your dataset as a parent grouping. Based on your dataset, these include:

- **ORG**: Analyze by organization
- **VP**: Analyze by VP
- **PILLAR**: Analyze by pillar/department
- **TR_PRODUCT**: Analyze by product
- **Cloud**: Analyze by cloud provider
- **Env**: Analyze by environment (Prod, Stage, Dev)

## Configuration File

In the `config.yaml` file, you can set the `parent_grouping` to any column name in your dataset:

```yaml
# Grouping configuration
parent_grouping: VP  # Can be any column in dataset: ORG, TR_PRODUCT, ENV, Cloud, VP, PILLAR, etc.
parent_grouping_value: Bob  # Value for the parent grouping
```

## Command Line Override

You can also override the configuration with command line parameters:

```
python finops_analyzer.py --parent-group VP --parent-value Bob
```

## Example Configurations

Several example configurations are provided in the `examples/` directory:

- `month_config.yaml` - Month-to-month analysis by ORG
- `quarter_config.yaml` - Quarter-to-quarter analysis by ORG
- `week_config.yaml` - Week-to-week analysis by Cloud
- `year_config.yaml` - Year-to-year analysis by TR_PRODUCT
- `vp_config.yaml` - Analysis by VP
- `pillar_config.yaml` - Analysis by PILLAR

To use an example configuration:

```
python finops_analyzer.py --config examples/vp_config.yaml
```

## Combining Parameters

You can combine different parameters to create custom analyses on the fly:

```
python finops_analyzer.py --parent-group VP --parent-value Diana --period quarter --period-value Q1 --year 2024
```

## Output

Each analysis will generate an HTML report in the `output/` directory with a filename that includes:
- Time period
- Parent grouping column and value
- Timestamp

For example: `finops_report_month_Mar_2024_VP_Bob_20250402_162530.html`