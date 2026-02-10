# Quick Start Guide

## Installation (5 minutes)

1. **Activate virtual environment:**
```bash
source .venv/bin/activate
```

2. **Verify dependencies are installed:**
```bash
pip list | grep -E "pandas|holidays|tabulate|dateutil"
```

You should see:
- pandas (>=2.1.0)
- holidays (>=0.36)
- python-dateutil (>=2.8.2)
- tabulate (>=0.9.0)

## Running the Tool

### Quick Test with Sample Data

A test NEM12 file (`test_nem12.csv`) is included with 7 days of sample data.

```bash
python meter_aggregator.py
```

Follow the prompts:

1. **Select file**: Press Enter to use `test_nem12.csv`
2. **State**: Enter your state (e.g., `NSW`)
3. **Number of periods**: Try `3` for a standard setup
4. **Configure periods**: See example below

### Example: Standard 3-Period Configuration

**Period 1: Peak**
- Weekday ranges: `7:00-9:00` then `17:00-20:00`
- Weekend ranges: (press Enter to skip)
- Holiday ranges: (press Enter to skip)
- Price: `0.35`

**Period 2: Shoulder**
- Weekday ranges: `9:00-17:00` then `20:00-22:00`
- Weekend ranges: Use same as weekdays? `n`
  - Range: `7:00-22:00`
- Holiday ranges: Use same as weekends? `y`
- Price: `0.25`

**Period 3: Off-peak**
- Weekday ranges: `22:00-7:00`
- Weekend ranges: Use same as weekdays? `y`
- Holiday ranges: Use same as weekends? `y`
- Price: `0.15`

### Understanding the Output

The tool will display:

1. **Meter Information**: NMI, date range, interval count
2. **Period Summary Table**: Total kWh, costs, and intervals per period
3. **Period Distribution**: Percentage breakdown
4. **Day Type Breakdown**: Weekday/weekend/holiday split

### Output Files

Two CSV files are created:

1. **Aggregated Results** (`aggregated_results_*.csv`):
   - Summary by period
   - Ready for reporting

2. **Detailed Intervals** (`detailed_intervals_*.csv`) - Optional:
   - Every 30-minute interval with its classification
   - Useful for detailed analysis

## Common Time Range Examples

### All Day
```
00:00-00:00  (represents full 24 hours)
```

### Business Hours
```
09:00-17:00
```

### Overnight (spanning midnight)
```
22:00-07:00
```

### Multiple Ranges (Morning + Evening Peak)
```
First range:  07:00-09:00
Second range: 17:00-20:00
Third range:  (press Enter to finish)
```

### 12-Hour Format
```
7:00 AM-9:00 AM
5:00 PM-8:00 PM
```

## Tips for Success

1. **Complete Coverage**: Make sure your time ranges cover all 24 hours to avoid "Unclassified" intervals

2. **Test First**: Use the sample file to test your configuration before processing real data

3. **Save Configuration**: Take a screenshot or note down your period setup for future use

4. **Check Unclassified**: If you see many unclassified intervals, review your time ranges

5. **Midnight Ranges**: For periods like `22:00-07:00`, the tool automatically handles the midnight crossing

## Troubleshooting

### "No CSV files found"
Place your NEM12 CSV file in the same directory as `meter_aggregator.py`

### "Invalid time format"
Use formats like:
- `14:30` (24-hour)
- `2:30 PM` (12-hour)

### "High percentage of unclassified"
Add more time ranges or adjust existing ranges to cover gaps

### Import errors
Make sure virtual environment is activated:
```bash
source .venv/bin/activate
```

## Using Your Own Data

1. Place your NEM12 CSV file in the project directory
2. Run `python meter_aggregator.py`
3. Select your file when prompted
4. Follow the same configuration steps

## Getting Help

- Review the main README.md for detailed documentation
- Check your NEM12 file format matches the standard
- Ensure time ranges don't have gaps

## Example Session

```
$ python meter_aggregator.py

======================================================================
  NEM12 METER DATA AGGREGATION TOOL
  Australian Electricity Interval Data Analysis
======================================================================

Searching for NEM12 CSV files in current directory...
✓ Found 1 CSV file: test_nem12.csv

Validating NEM12 file structure...
✓ File structure is valid

Parsing NEM12 file...
✓ Successfully parsed 336 intervals

----------------------------------------------------------------------
METER INFORMATION
----------------------------------------------------------------------
NMI: 1234567890
Register ID: E1
Meter Serial: METER001
Unit of Measure: KWH
Interval Length: 30 minutes
Total Days of Data: 7
----------------------------------------------------------------------

==================================================
Time-of-Use Period Configuration
==================================================

Available states: NSW, VIC, QLD, SA, WA, TAS, NT, ACT
Enter your Australian state (e.g., NSW): NSW
✓ State set to: NSW

How many time-of-use periods do you want to define? 3

[... follow the prompts ...]

✓ Aggregation complete

[... results displayed ...]

✓ Aggregated results saved to: aggregated_results_1234567890_20240210_180530.csv
```

Enjoy using the NEM12 Meter Data Aggregation Tool!
