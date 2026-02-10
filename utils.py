"""Utility functions for NEM12 meter data processing."""

import os
import re
from datetime import datetime, time
from typing import List, Optional
import pytz


def parse_time_string(time_str: str) -> time:
    """
    Parse various time formats to datetime.time object.

    Supports:
    - HH:MM (24-hour)
    - HH:MM:SS (24-hour)
    - HH:MM AM/PM (12-hour)
    - HH:MM:SS AM/PM (12-hour)

    Args:
        time_str: Time string to parse

    Returns:
        datetime.time object

    Raises:
        ValueError: If time format is invalid
    """
    time_str = time_str.strip()

    # Try 24-hour formats first
    for fmt in ['%H:%M:%S', '%H:%M']:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.time()
        except ValueError:
            continue

    # Try 12-hour formats
    for fmt in ['%I:%M:%S %p', '%I:%M %p']:
        try:
            dt = datetime.strptime(time_str.upper(), fmt)
            return dt.time()
        except ValueError:
            continue

    raise ValueError(f"Invalid time format: '{time_str}'. Use HH:MM (24-hour) or HH:MM AM/PM (12-hour)")


def validate_time_format(time_str: str) -> bool:
    """
    Validate if a string is a valid time format.

    Args:
        time_str: Time string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_time_string(time_str)
        return True
    except ValueError:
        return False


def find_nem12_files(directory: str = '.') -> List[str]:
    """
    Find all CSV files in a directory that might be NEM12 files.

    Args:
        directory: Directory to search (default: current directory)

    Returns:
        List of CSV file paths
    """
    csv_files = []
    for file in os.listdir(directory):
        if file.endswith('.csv') or file.endswith('.CSV'):
            csv_files.append(os.path.join(directory, file))
    return sorted(csv_files)


def find_meter_data_files(directory: str = '.') -> List[str]:
    """
    Find all CSV files in a directory that might be meter data files.
    Alias for find_nem12_files for backward compatibility.

    Args:
        directory: Directory to search (default: current directory)

    Returns:
        List of CSV file paths
    """
    return find_nem12_files(directory)


def validate_nem12_structure(filepath: str) -> tuple[bool, str]:
    """
    Quick validation of NEM12 file structure.

    Checks for:
    - 100 header record
    - 900 footer record
    - At least one 200/300 record pair

    Args:
        filepath: Path to NEM12 file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        if not lines:
            return False, "File is empty"

        # Check for 100 header
        if not lines[0].strip().startswith('100'):
            return False, "Missing 100 header record"

        # Check for 900 footer
        if not lines[-1].strip().startswith('900'):
            return False, "Missing 900 footer record"

        # Check for at least one 200 and 300 record
        has_200 = any(line.strip().startswith('200') for line in lines)
        has_300 = any(line.strip().startswith('300') for line in lines)

        if not has_200:
            return False, "No 200 (meter header) records found"
        if not has_300:
            return False, "No 300 (interval data) records found"

        return True, ""

    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def get_australian_timezone(state: str) -> pytz.timezone:
    """
    Get the timezone for an Australian state.

    Args:
        state: Australian state code (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)

    Returns:
        pytz timezone object
    """
    state = state.upper()

    # Timezone mapping
    timezone_map = {
        'NSW': 'Australia/Sydney',
        'VIC': 'Australia/Melbourne',
        'QLD': 'Australia/Brisbane',
        'SA': 'Australia/Adelaide',
        'WA': 'Australia/Perth',
        'TAS': 'Australia/Hobart',
        'NT': 'Australia/Darwin',
        'ACT': 'Australia/Sydney',
    }

    tz_name = timezone_map.get(state, 'Australia/Sydney')
    return pytz.timezone(tz_name)


def format_currency(amount: float) -> str:
    """
    Format a number as Australian currency.

    Args:
        amount: Dollar amount

    Returns:
        Formatted string (e.g., "$1,234.56")
    """
    return f"${amount:,.2f}"


def format_number(number: float, decimals: int = 2) -> str:
    """
    Format a number with thousands separators.

    Args:
        number: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "1,234.56")
    """
    return f"{number:,.{decimals}f}"


def detect_csv_format(filepath: str) -> str:
    """
    Detect the format of a CSV file.

    Returns:
        'nem12', 'generic_interval', or 'unknown'

    Detection logic:
        1. Read first 10 lines
        2. Check first line:
           - Starts with "100" -> likely NEM12
           - Starts with alphabetic chars -> likely generic CSV (has header)
        3. If has header:
           - Check for 'interval_length' and 'reading1_value' columns -> 'generic_interval'
        4. Otherwise check for NEM12 markers (200, 300 records) -> 'nem12'
        5. Else -> 'unknown'
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = [f.readline().strip() for _ in range(10) if f.readable()]

        if not lines:
            return 'unknown'

        first_line = lines[0]

        # Check if first line starts with "100" (NEM12 header)
        if first_line.startswith('100'):
            return 'nem12'

        # Check if first line looks like a CSV header (starts with alphabetic chars)
        if first_line and first_line[0].isalpha():
            # Parse header columns
            header_columns = [col.strip() for col in first_line.split(',')]

            # Check for generic interval CSV markers
            has_interval_length = 'interval_length' in header_columns
            has_reading_value = any('reading' in col and 'value' in col for col in header_columns)

            if has_interval_length and has_reading_value:
                return 'generic_interval'

        # Check for NEM12 record markers (200, 300)
        for line in lines:
            if line.startswith('200') or line.startswith('300'):
                return 'nem12'

        return 'unknown'

    except Exception:
        return 'unknown'


def validate_generic_csv_structure(filepath: str) -> tuple[bool, str]:
    """
    Validate generic interval CSV structure.

    Checks:
        - Has header row (first line doesn't start with digit)
        - Required columns present: interval_start_at, interval_length, meterpoint_id or device_id
        - At least one readingN_value column exists
        - interval_length is valid (5, 15, or 30)

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()

        if not first_line:
            return False, "File is empty"

        # Check for header row
        if first_line[0].isdigit():
            return False, "Missing header row (expected column names)"

        # Parse header columns
        header_columns = [col.strip() for col in first_line.split(',')]

        # Check for required columns
        required_base_columns = ['interval_start_at', 'interval_length']
        missing_columns = [col for col in required_base_columns if col not in header_columns]

        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        # Check for meter identifier (meterpoint_id or device_id)
        has_meter_id = 'meterpoint_id' in header_columns or 'device_id' in header_columns
        if not has_meter_id:
            return False, "Missing meter identifier (meterpoint_id or device_id)"

        # Check for at least one reading value column
        has_reading_value = any('reading' in col and 'value' in col for col in header_columns)
        if not has_reading_value:
            return False, "No reading value columns found (expected reading1_value, reading2_value, etc.)"

        # Validate interval_length in first data row
        if second_line:
            data_values = second_line.split(',')
            interval_length_index = header_columns.index('interval_length')

            if interval_length_index < len(data_values):
                try:
                    interval_length = int(data_values[interval_length_index])
                    if interval_length not in [5, 15, 30]:
                        return False, f"Invalid interval_length: {interval_length} (must be 5, 15, or 30 minutes)"
                except ValueError:
                    return False, f"Invalid interval_length value: {data_values[interval_length_index]}"

        return True, ""

    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def get_parser_for_format(format_type: str, filepath: str):
    """
    Factory function to return appropriate parser instance.

    Args:
        format_type: 'nem12' or 'generic_interval'
        filepath: Path to CSV file

    Returns:
        NEM12Parser or GenericIntervalParser instance

    Raises:
        ValueError: If format_type is not supported
    """
    if format_type == 'nem12':
        from nem12_parser import NEM12Parser
        return NEM12Parser(filepath)
    elif format_type == 'generic_interval':
        from generic_interval_parser import GenericIntervalParser
        return GenericIntervalParser(filepath)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")
