#!/usr/bin/env python3
"""
NEM12 Meter Data Aggregation Tool

Main script for aggregating Australian electricity interval meter data
into user-defined time-of-use periods with optional cost calculation.
"""

import sys
import os
from nem12_parser import NEM12Parser
from generic_interval_parser import GenericIntervalParser
from tou_config import TOUConfigurator
from aggregator import MeterDataAggregator
from output_formatter import OutputFormatter
from utils import (
    find_nem12_files,
    find_meter_data_files,
    validate_nem12_structure,
    validate_generic_csv_structure,
    detect_csv_format,
    get_parser_for_format
)


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 70)
    print("  NEM12 METER DATA AGGREGATION TOOL")
    print("  Australian Electricity Interval Data Analysis")
    print("=" * 70)


def select_file() -> str:
    """
    Find and select meter data file to process.

    Returns:
        Path to selected file

    Raises:
        SystemExit: If no files found or user cancels
    """
    print("\nSearching for meter data CSV files in current directory...")

    files = find_meter_data_files('.')

    if not files:
        print("\n✗ No CSV files found in current directory")
        filepath = input("Enter path to meter data file (or 'q' to quit): ").strip()
        if filepath.lower() == 'q':
            print("Exiting...")
            sys.exit(0)
        if not os.path.exists(filepath):
            print(f"✗ File not found: {filepath}")
            sys.exit(1)
        return filepath

    if len(files) == 1:
        print(f"✓ Found 1 CSV file: {os.path.basename(files[0])}")
        return files[0]

    # Multiple files - let user choose
    print(f"\nFound {len(files)} CSV files:")
    for i, filepath in enumerate(files, 1):
        print(f"  {i}. {os.path.basename(filepath)}")

    while True:
        try:
            choice = input(f"\nSelect file (1-{len(files)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                print("Exiting...")
                sys.exit(0)
            choice_num = int(choice)
            if 1 <= choice_num <= len(files):
                selected_file = files[choice_num - 1]
                print(f"✓ Selected: {os.path.basename(selected_file)}")
                return selected_file
            else:
                print(f"✗ Please enter a number between 1 and {len(files)}")
        except ValueError:
            print("✗ Invalid input")


def validate_file(filepath: str):
    """
    Validate file structure based on detected format.

    Args:
        filepath: Path to file

    Raises:
        SystemExit: If validation fails
    """
    print("\nDetecting file format...")

    # Detect format
    format_type = detect_csv_format(filepath)

    if format_type == 'unknown':
        print("✗ Unknown file format. Expected NEM12 or generic interval CSV.")
        sys.exit(1)

    print(f"✓ Detected format: {format_type}")

    # Validate based on format
    print(f"\nValidating {format_type} file structure...")

    if format_type == 'nem12':
        is_valid, error_msg = validate_nem12_structure(filepath)
    elif format_type == 'generic_interval':
        is_valid, error_msg = validate_generic_csv_structure(filepath)
    else:
        print(f"✗ Unsupported format: {format_type}")
        sys.exit(1)

    if not is_valid:
        print(f"✗ Validation failed: {error_msg}")
        sys.exit(1)

    print("✓ File structure is valid")


def parse_file(filepath: str) -> tuple:
    """
    Parse file using appropriate parser based on detected format.

    Args:
        filepath: Path to file

    Returns:
        Tuple of (dataframe, meter_info)

    Raises:
        SystemExit: If parsing fails
    """
    print("\nParsing file...")

    try:
        # Detect format
        format_type = detect_csv_format(filepath)

        # Get appropriate parser
        parser = get_parser_for_format(format_type, filepath)

        # Parse (same interface for both parsers)
        df = parser.parse()
        meter_info = parser.get_meter_info()

        print(f"✓ Successfully parsed {len(df):,} intervals")

        return df, meter_info

    except Exception as e:
        print(f"✗ Error parsing file: {str(e)}")
        sys.exit(1)


def display_meter_info(meter_info: dict):
    """Display meter information."""
    print("\n" + "-" * 70)
    print("METER INFORMATION")
    print("-" * 70)
    print(f"NMI: {meter_info['nmi']}")
    print(f"Register ID: {meter_info['register_id']}")
    print(f"Meter Serial: {meter_info['meter_serial']}")
    print(f"Unit of Measure: {meter_info['uom']}")
    print(f"Interval Length: {meter_info['interval_length_minutes']} minutes")
    print(f"Total Days of Data: {meter_info['total_days']}")

    if len(meter_info['all_nmis']) > 1:
        print(f"\n⚠ Warning: Multiple NMIs detected: {', '.join(meter_info['all_nmis'])}")
        print("  Processing first NMI only")

    print("-" * 70)


def configure_periods() -> tuple:
    """
    Run interactive TOU configuration.

    Returns:
        Tuple of (periods, state)

    Raises:
        SystemExit: If user cancels or no periods defined
    """
    try:
        configurator = TOUConfigurator()
        periods, state = configurator.run_interactive_config()

        if not periods:
            print("\n✗ No periods defined")
            sys.exit(1)

        return periods, state

    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user")
        sys.exit(0)


def aggregate_data(df, periods, state):
    """
    Classify and aggregate interval data.

    Args:
        df: DataFrame with interval data
        periods: List of PeriodDefinition objects
        state: Australian state code

    Returns:
        Tuple of (aggregated_df, classified_df, summary_stats)
    """
    print("\nClassifying intervals by time-of-use periods...")

    aggregator = MeterDataAggregator(df, periods, state)
    classified_df = aggregator.classify_intervals()

    print("✓ Intervals classified")

    print("\nAggregating consumption by period...")
    aggregated_df = aggregator.aggregate()

    print("✓ Aggregation complete")

    summary_stats = aggregator.get_summary_stats()

    return aggregated_df, classified_df, summary_stats


def display_and_save_results(aggregated_df, classified_df, summary_stats, nmi):
    """
    Display results to console and save to CSV files.

    Args:
        aggregated_df: Aggregated results DataFrame
        classified_df: Classified intervals DataFrame
        summary_stats: Summary statistics dictionary
        nmi: National Metering Identifier
    """
    formatter = OutputFormatter(aggregated_df, summary_stats, nmi)

    # Display to console
    formatter.display_console()

    # Save aggregated results
    print("\nSaving results...")
    agg_filepath = formatter.save_csv()
    print(f"✓ Aggregated results saved to: {agg_filepath}")

    # Ask if user wants detailed interval data
    save_detailed = input("\nSave detailed interval-level data? (y/n): ").strip().lower()
    if save_detailed == 'y':
        detail_filepath = formatter.save_detailed_csv(classified_df)
        print(f"✓ Detailed intervals saved to: {detail_filepath}")


def main():
    """Main execution flow."""
    try:
        # Display banner
        print_banner()

        # Select file
        filepath = select_file()

        # Validate file
        validate_file(filepath)

        # Parse file
        df, meter_info = parse_file(filepath)

        # Display meter info
        display_meter_info(meter_info)

        # Configure TOU periods
        periods, state = configure_periods()

        # Aggregate data
        aggregated_df, classified_df, summary_stats = aggregate_data(df, periods, state)

        # Display and save results
        display_and_save_results(aggregated_df, classified_df, summary_stats, meter_info['nmi'])

        # Completion message
        print("\n" + "=" * 70)
        print("  AGGREGATION COMPLETE")
        print("=" * 70)
        print("\nThank you for using the NEM12 Meter Data Aggregation Tool!")
        print()

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
