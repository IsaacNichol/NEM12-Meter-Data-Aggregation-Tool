"""Generic interval CSV parser for wide-format meter data."""

import pandas as pd
from datetime import timedelta
import re
from typing import List, Optional
import warnings
from utils import localize_naive_to_industry, get_industry_timezone


class GenericIntervalParser:
    """Parser for generic wide-format interval CSV files."""

    def __init__(self, filepath: str, state: str = 'NSW'):
        """
        Initialize parser with filepath.

        Args:
            filepath: Path to generic interval CSV file
            state: Australian state code (for timezone handling)
        """
        self.filepath = filepath
        self.state = state
        self.df_raw: Optional[pd.DataFrame] = None
        self.meter_info_cache: Optional[dict] = None

    def parse(self) -> pd.DataFrame:
        """
        Parse generic interval CSV and return DataFrame of interval data.

        Returns:
            DataFrame with columns: timestamp, nmi, register_id, consumption_kwh,
                                   quality_method, is_estimate

        Raises:
            ValueError: If file format is invalid
        """
        # Read CSV file
        self.df_raw = pd.read_csv(self.filepath, encoding='utf-8-sig')

        if self.df_raw.empty:
            raise ValueError("CSV file is empty")

        # Validate required columns
        required_columns = ['interval_start_at', 'interval_length']
        missing = [col for col in required_columns if col not in self.df_raw.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        # Check for meter identifier
        if 'meterpoint_id' not in self.df_raw.columns and 'device_id' not in self.df_raw.columns:
            raise ValueError("Missing meter identifier (meterpoint_id or device_id)")

        # Convert to long format
        rows = []

        for idx, row in self.df_raw.iterrows():
            try:
                # Extract metadata from row
                interval_length = int(row['interval_length'])

                # Validate interval length
                if interval_length not in [5, 15, 30]:
                    warnings.warn(f"Row {idx}: Invalid interval_length {interval_length}, skipping")
                    continue

                # Parse start datetime
                interval_start_at = pd.to_datetime(row['interval_start_at'])

                # Convert to timezone-aware Industry time if needed
                if interval_start_at.tzinfo is None:
                    # Naive datetime - assume it's Industry time
                    interval_start_at_aware = localize_naive_to_industry(
                        interval_start_at.to_pydatetime()
                    )
                else:
                    # Already timezone-aware - convert to Industry time
                    industry_tz = get_industry_timezone()
                    interval_start_at_aware = interval_start_at.tz_convert(industry_tz)

                # Get meter identifiers
                nmi = str(row.get('meterpoint_id', row.get('device_id', '')))
                register_id = str(row.get('register_identifier', ''))

                # Find all reading value columns
                reading_cols = [col for col in self.df_raw.columns if re.match(r'reading\d+_value', col)]

                if not reading_cols:
                    warnings.warn(f"Row {idx}: No reading columns found, skipping")
                    continue

                # Process each reading
                for reading_col in reading_cols:
                    # Extract reading number from column name (e.g., "reading1_value" -> 1)
                    match = re.match(r'reading(\d+)_value', reading_col)
                    if not match:
                        continue

                    reading_num = int(match.group(1))

                    # Get reading value
                    value = row[reading_col]

                    # Skip if value is null, empty, or zero
                    if pd.isna(value) or value == '' or value == 0:
                        continue

                    try:
                        consumption_kwh = float(value)
                    except (ValueError, TypeError):
                        continue

                    # Calculate timestamp for this interval
                    # reading1 corresponds to the first interval starting at interval_start_at
                    # reading2 is interval_length minutes later, etc.
                    timestamp = interval_start_at_aware + timedelta(minutes=interval_length * (reading_num - 1))

                    # Get quality information
                    quality_flag_col = f'reading{reading_num}_quality_flag'
                    quality_method_col = f'reading{reading_num}_quality_method'

                    quality_method = ''
                    if quality_method_col in self.df_raw.columns:
                        quality_method = str(row.get(quality_method_col, ''))

                    # Fall back to quality_flag if quality_method is empty
                    if not quality_method or quality_method == 'nan':
                        if quality_flag_col in self.df_raw.columns:
                            quality_method = str(row.get(quality_flag_col, 'A'))
                        else:
                            quality_method = 'A'  # Default to Actual

                    # Determine if estimate
                    # E = Estimated, F = Final Estimate, S = Substituted
                    is_estimate = quality_method.upper() in ['E', 'F', 'S']

                    # Create row
                    rows.append({
                        'timestamp': timestamp,
                        'nmi': nmi,
                        'register_id': register_id,
                        'consumption_kwh': consumption_kwh,
                        'quality_method': quality_method,
                        'is_estimate': is_estimate
                    })

            except Exception as e:
                warnings.warn(f"Error processing row {idx}: {str(e)}")
                continue

        if not rows:
            raise ValueError("No valid interval data found in file")

        # Create DataFrame
        df = pd.DataFrame(rows)

        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df

    def get_meter_info(self) -> dict:
        """
        Get summary information about the meter data.

        Returns:
            Dictionary with meter metadata
        """
        if self.meter_info_cache:
            return self.meter_info_cache

        if self.df_raw is None:
            # Parse if not already parsed
            self.parse()

        if self.df_raw is None or self.df_raw.empty:
            return {}

        # Get first row for metadata
        first_row = self.df_raw.iloc[0]

        # Get NMI (meterpoint_id or device_id)
        nmi = str(first_row.get('meterpoint_id', first_row.get('device_id', '')))

        # Get all unique NMIs
        if 'meterpoint_id' in self.df_raw.columns:
            all_nmis = self.df_raw['meterpoint_id'].dropna().astype(str).unique().tolist()
        elif 'device_id' in self.df_raw.columns:
            all_nmis = self.df_raw['device_id'].dropna().astype(str).unique().tolist()
        else:
            all_nmis = [nmi]

        # Get register ID
        register_id = str(first_row.get('register_identifier', ''))

        # Get meter serial
        meter_serial = str(first_row.get('device_id', ''))

        # Get unit of measure
        uom = str(first_row.get('units', 'KWH'))

        # Get interval length
        interval_length = int(first_row.get('interval_length', 30))

        # Get total days
        total_days = len(self.df_raw)

        self.meter_info_cache = {
            'nmi': nmi,
            'all_nmis': all_nmis,
            'register_id': register_id,
            'meter_serial': meter_serial,
            'uom': uom,
            'interval_length_minutes': interval_length,
            'total_days': total_days
        }

        return self.meter_info_cache
