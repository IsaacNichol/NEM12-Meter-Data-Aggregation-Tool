# NEM12 Meter Data Aggregation Tool

A Python CLI tool for aggregating Australian Electricity Interval Meter Data (NEM12 format) into user-defined time-of-use periods with optional cost calculation.

## Features

- **NEM12 Format Parsing**: Automatically parses Australian standard NEM12 CSV files
- **Interactive Configuration**: User-friendly CLI to define custom time-of-use periods
- **Flexible Period Definitions**: Different time ranges for weekdays, weekends, and public holidays
- **Australian Public Holidays**: Automatic detection of public holidays by state
- **Cost Calculation**: Optional pricing per period to calculate electricity costs
- **Detailed Reporting**: Console output with formatted tables and CSV export
- **Data Quality Tracking**: Identifies estimated vs actual readings

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Navigate to the project directory:

2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

1. Place your NEM12 CSV file(s) in the project directory

2. Run the script:
```bash
python meter_aggregator.py
```

3. Follow the interactive prompts to:
   - Select your NEM12 file (if multiple found)
   - Choose your Australian state
   - Define time-of-use periods
   - Set time ranges for weekdays, weekends, and holidays
   - Optionally add pricing per period

4. View results in the console and exported CSV files

### Example Configuration

**Scenario**: Standard 3-period tariff (Peak, Shoulder, Off-peak) in NSW

```
State: NSW
Number of periods: 3

Period 1: Peak
  Weekdays: 07:00-09:00, 17:00-20:00
  Weekends: (none)
  Holidays: (none)
  Price: $0.35/kWh

Period 2: Shoulder
  Weekdays: 09:00-17:00, 20:00-22:00
  Weekends: 07:00-22:00
  Holidays: 07:00-22:00
  Price: $0.25/kWh

Period 3: Off-peak
  Weekdays: 22:00-07:00
  Weekends: 22:00-07:00
  Holidays: 22:00-07:00
  Price: $0.15/kWh
```

## NEM12 Format

NEM12 is the Australian standard format for interval meter data. Files contain:

- **Record 100**: File header
- **Record 200**: Meter/NMI header
- **Record 300**: Interval data (typically 48 x 30-minute intervals per day)
- **Record 400**: Events (optional)
- **Record 500**: End of data block
- **Record 900**: End of file

The tool automatically handles:
- Multiple days of data
- Daylight saving time transitions
- Missing or estimated readings
- Multiple NMIs (processes first by default)

## Output Files

### Aggregated Results CSV
`aggregated_results_{NMI}_{timestamp}.csv`

Contains:
- Period name
- Total kWh consumption
- Number of intervals
- Average kWh per interval
- Percentage of total consumption
- Total cost (if pricing provided)

### Detailed Intervals CSV (Optional)
`detailed_intervals_{NMI}_{timestamp}.csv`

Contains:
- Timestamp for each interval
- Consumption in kWh
- Assigned period
- Day type (weekday/weekend/holiday)
- Quality method
- Estimated flag

## Time Format Support

The tool accepts multiple time formats:

- 24-hour: `14:30` or `14:30:00`
- 12-hour: `2:30 PM` or `2:30:00 PM`

Time ranges can span midnight (e.g., `23:00-02:00` for overnight periods).

## Australian States

Supported state codes for holiday detection:
- NSW - New South Wales
- VIC - Victoria
- QLD - Queensland
- SA - South Australia
- WA - Western Australia
- TAS - Tasmania
- NT - Northern Territory
- ACT - Australian Capital Territory

## Project Structure

```
Meter-data/
├── meter_aggregator.py      # Main orchestration script
├── nem12_parser.py           # NEM12 format parser
├── tou_config.py             # Interactive TOU configuration
├── aggregator.py             # Data classification and aggregation
├── output_formatter.py       # Console and CSV output formatting
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Error Handling

The tool handles:
- Invalid NEM12 file format
- Missing or corrupted interval data
- Invalid time format inputs
- Multiple NMIs in a single file
- Daylight saving time transitions
- Unclassified intervals (gaps in period definitions)

## Tips

1. **Define Complete Periods**: Ensure all 24 hours are covered by your periods to avoid "Unclassified" intervals
2. **Test with Sample Data**: Start with a small date range to test your configuration
3. **Save Configuration**: The tool displays your configuration summary - save it for future reference
4. **Check Estimated Data**: Review the warning if significant data is estimated rather than actual
5. **Midnight Wrap**: Use ranges like `22:00-07:00` for periods spanning midnight

## Troubleshooting

### "No CSV files found"
- Ensure your NEM12 file has a `.csv` extension
- Check you're running the script from the correct directory

### "Invalid 200/300 record format"
- Verify the file is in NEM12 format (not a different meter data format)
- Check the file isn't corrupted

### "High percentage of unclassified intervals"
- Review your time ranges to ensure all 24 hours are covered
- Check for gaps between periods

### Import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're using the virtual environment

## License

This tool is provided as-is for aggregating NEM12 meter data files.

## Support

For issues or questions:
1. Review this README
2. Check your NEM12 file format
3. Verify your time range definitions cover all required hours
4. Ensure dependencies are correctly installed

## Version

Version 1.0.0 - Initial release
