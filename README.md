# NEM12 Meter Data Aggregation Tool

A Python CLI tool for aggregating Australian Electricity Interval Meter Data (NEM12 format) into user-defined time-of-use periods with optional cost calculation.

## Features

- **NEM12 Format Parsing**: Automatically parses Australian standard NEM12 CSV files
- **Generic Interval CSV Support**: Also handles wide-format interval CSV files
- **Interactive Configuration**: User-friendly CLI to define custom time-of-use periods
- **Flexible Period Definitions**: Different time ranges for weekdays, weekends, and public holidays
- **Timezone Handling**: Proper DST-aware classification using state-specific timezones
- **Australian Public Holidays**: Automatic detection of public holidays by state
- **Cost Calculation**: Optional pricing per period to calculate electricity costs
- **Detailed Reporting**: Console output with formatted tables and CSV export
- **Data Quality Tracking**: Identifies estimated vs actual readings
- **DST Transition Detection**: Automatically detects and warns about daylight saving changes

## Timezone Handling

The tool properly handles timezone conversion for Australian electricity meter data:

### Input Data Format
- **Industry Time**: All meter data is in "Industry Time" (UTC+10, no DST)
- Industry time is equivalent to Queensland time year-round
- This is the standard format for NEM12 files and most meter data

### State Selection
- **Required for accurate TOU classification**
- Different states have different timezones and DST rules
- Your state selection determines how periods are classified

### Period Matching
- **Uses local clock time**: Peak period "16:00-20:00" matches your local 4-8 PM
- Accounts for DST differences between Industry time and your state
- Day-type classification (weekday/weekend/holiday) uses local date

### Output Format
- **Timestamps displayed in Industry time**: Preserves source data format
- All timestamps labeled with timezone (e.g., "AEST")
- Classification results (period, day_type) based on local time

### State Timezones

| State | Standard Time | DST? | UTC Offset | Notes |
|-------|---------------|------|------------|-------|
| NSW, VIC, ACT, TAS | AEST/AEDT | Yes | +10/+11 | DST Oct-Apr |
| QLD | AEST | No | +10 | No DST (same as Industry time) |
| SA | ACST/ACDT | Yes | +9.5/+10.5 | DST Oct-Apr |
| NT | ACST | No | +9.5 | No DST |
| WA | AWST | No | +8 | No DST |

### DST Transitions

On DST transition days, you may see:
- **Spring forward** (first Sunday in October): 46 intervals instead of 48 (one hour skipped)
- **Fall back** (first Sunday in April): 50 intervals instead of 48 (one hour repeated)

These are expected and do not affect aggregation accuracy. The tool will display a warning when DST transitions are detected, showing:
- Date of transition
- Actual interval count vs expected
- Type of transition (spring forward/fall back)
- Note that timestamps remain in Industry time

**Example**: In NSW during summer DST:
- Industry time: 16:00 (UTC+10)
- Local time: 17:00 (AEDT, UTC+11)
- If your peak period is 16:00-20:00, it matches local time 16:00-20:00 (4-8 PM on your clock)
- The 16:00 Industry time reading is classified as off-peak (local 17:00 is outside 16:00-20:00 local)

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
   - Select your meter data file (if multiple found)
   - Choose your Australian state (required for timezone handling)
   - Define time-of-use periods
   - Set time ranges for weekdays, weekends, and holidays (in local time)
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

## Supported File Formats

### NEM12 Format

NEM12 is the Australian standard format for interval meter data. Files contain:

- **Record 100**: File header
- **Record 200**: Meter/NMI header
- **Record 300**: Interval data (typically 48 x 30-minute intervals per day)
- **Record 400**: Events (optional)
- **Record 500**: End of data block
- **Record 900**: End of file

### Generic Interval CSV Format

Wide-format CSV files with columns:
- `interval_start_at`: Starting timestamp
- `interval_length`: Minutes per interval (5, 15, or 30)
- `meterpoint_id` or `device_id`: Meter identifier
- `reading1_value`, `reading2_value`, etc.: Consumption values

The tool automatically detects the format and handles:
- Multiple days of data
- Daylight saving time transitions (with warnings)
- Missing or estimated readings
- Multiple NMIs (processes first by default)
- Both naive and timezone-aware timestamps

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
- Timestamp (Industry Time) for each interval
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

Supported state codes for holiday detection and timezone handling:
- NSW - New South Wales (AEST/AEDT with DST)
- VIC - Victoria (AEST/AEDT with DST)
- QLD - Queensland (AEST, no DST)
- SA - South Australia (ACST/ACDT with DST)
- WA - Western Australia (AWST, no DST)
- TAS - Tasmania (AEST/AEDT with DST)
- NT - Northern Territory (ACST, no DST)
- ACT - Australian Capital Territory (AEST/AEDT with DST)

## Project Structure

```
Meter-data/
├── meter_aggregator.py       # Main orchestration script
├── nem12_parser.py           # NEM12 format parser
├── generic_interval_parser.py # Generic interval CSV parser
├── tou_config.py             # Interactive TOU configuration
├── aggregator.py             # Data classification and aggregation
├── output_formatter.py       # Console and CSV output formatting
├── utils.py                  # Utility functions (includes timezone helpers)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Error Handling

The tool handles:
- Invalid meter data file format (NEM12 or generic CSV)
- Missing or corrupted interval data
- Invalid time format inputs
- Multiple NMIs in a single file
- Daylight saving time transitions (with detection and warnings)
- Timezone-aware and naive timestamps
- Unclassified intervals (gaps in period definitions)

## Tips

1. **Define Complete Periods**: Ensure all 24 hours are covered by your periods to avoid "Unclassified" intervals
2. **Use Local Time**: Define time ranges in your local clock time (e.g., "4-7 PM" means 16:00-19:00 local)
3. **Test with Sample Data**: Start with a small date range to test your configuration
4. **Save Configuration**: The tool displays your configuration summary - save it for future reference
5. **Check Estimated Data**: Review the warning if significant data is estimated rather than actual
6. **Midnight Wrap**: Use ranges like `22:00-07:00` for periods spanning midnight
7. **DST Transitions**: The tool automatically handles DST - check warnings for transition days
8. **Queensland Exception**: QLD has no DST, so Industry time = local time year-round

## Troubleshooting

### "No CSV files found"
- Ensure your NEM12 file has a `.csv` extension
- Check you're running the script from the correct directory

### "Invalid file format" or parsing errors
- Verify the file is in NEM12 or generic interval CSV format
- Check the file isn't corrupted
- Ensure the file has proper headers (for CSV format)

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

### Unexpected classification during DST
- Remember: Time ranges are in local time, but timestamps shown are Industry time
- During NSW summer DST, Industry 16:00 = Local 17:00
- Check the DST transition warnings in output

## Version

Version 1.2.0 - Timezone handling update
- Added proper timezone-aware timestamp handling
- Implemented DST transition detection
- State-specific timezone conversion for accurate TOU classification

Version 1.1.0 - Generic file handling 
- Added support for a generic interval CSV format

Version 1.0.0 - Initial release
