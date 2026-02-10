"""NEM12 file parser for Australian electricity meter data."""

import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import warnings
from src.utils import localize_naive_to_industry


@dataclass
class Record200:
    """NEM12 Record 200 - Meter header information."""
    nmi: str
    nmi_configuration: str
    register_id: str
    nmi_suffix: str
    mdm_data_stream_identifier: str
    meter_serial_number: str
    uom: str  # Unit of measure (e.g., KWH)
    interval_length: int  # In minutes
    next_scheduled_read_date: str


@dataclass
class Record300:
    """NEM12 Record 300 - Interval data."""
    interval_date: datetime
    interval_values: List[float]
    quality_method: str
    reason_code: Optional[int]
    reason_description: Optional[str]
    update_datetime: Optional[str]
    msats_load_datetime: Optional[str]


class NEM12Parser:
    """Parser for NEM12 format electricity meter data files."""

    def __init__(self, filepath: str, state: str = 'NSW'):
        """
        Initialize parser with filepath.

        Args:
            filepath: Path to NEM12 CSV file
            state: Australian state code (for timezone handling)
        """
        self.filepath = filepath
        self.state = state
        self.current_record_200: Optional[Record200] = None
        self.records: List[tuple[Record200, Record300]] = []

    def parse(self) -> pd.DataFrame:
        """
        Parse NEM12 file and return DataFrame of interval data.

        Returns:
            DataFrame with columns: timestamp, nmi, register_id, consumption_kwh,
                                   quality_method, is_estimate

        Raises:
            ValueError: If file format is invalid
        """
        self._parse_file()
        return self._create_dataframe()

    def _parse_file(self):
        """Read and parse NEM12 file into record objects."""
        with open(self.filepath, 'r', encoding='utf-8-sig') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                fields = line.split(',')
                record_indicator = fields[0]

                try:
                    if record_indicator == '100':
                        self._parse_record_100(fields)
                    elif record_indicator == '200':
                        self._parse_record_200(fields)
                    elif record_indicator == '300':
                        self._parse_record_300(fields)
                    elif record_indicator == '400':
                        pass  # Event records - not needed for aggregation
                    elif record_indicator == '500':
                        pass  # End of data block
                    elif record_indicator == '900':
                        pass  # End of file
                    else:
                        warnings.warn(f"Unknown record type '{record_indicator}' at line {line_num}")
                except Exception as e:
                    warnings.warn(f"Error parsing line {line_num}: {str(e)}")
                    continue

    def _parse_record_100(self, fields: List[str]):
        """Parse 100 header record."""
        if len(fields) < 5:
            raise ValueError("Invalid 100 record format")
        # Record 100 just confirms NEM12 format - no data needed

    def _parse_record_200(self, fields: List[str]):
        """Parse 200 meter header record."""
        if len(fields) < 9:
            raise ValueError("Invalid 200 record format")

        self.current_record_200 = Record200(
            nmi=fields[1],
            nmi_configuration=fields[2],
            register_id=fields[3],
            nmi_suffix=fields[4],
            mdm_data_stream_identifier=fields[5],
            meter_serial_number=fields[6],
            uom=fields[7],
            interval_length=int(fields[8]),
            next_scheduled_read_date=fields[9] if len(fields) > 9 else ''
        )

    def _parse_record_300(self, fields: List[str]):
        """Parse 300 interval data record."""
        if not self.current_record_200:
            warnings.warn("300 record found before 200 record - skipping")
            return

        if len(fields) < 3:
            raise ValueError("Invalid 300 record format")

        # Parse date
        interval_date_str = fields[1]
        interval_date = datetime.strptime(interval_date_str, '%Y%m%d')

        # Calculate expected number of intervals
        interval_length = self.current_record_200.interval_length
        expected_intervals = (24 * 60) // interval_length

        # Parse interval values (starting at field 2)
        # Number of values varies: typically 48 for 30-min intervals,
        # but can be 46 or 50 on DST transition days
        interval_values = []
        field_index = 2

        while field_index < len(fields):
            value_str = fields[field_index].strip()

            # Check if we've reached the quality method field
            # Quality method is a single letter (A, E, F, S, etc.)
            if len(value_str) == 1 and value_str.isalpha():
                break

            # Try to parse as float
            try:
                if value_str:
                    interval_values.append(float(value_str))
                else:
                    interval_values.append(None)
            except ValueError:
                # If can't parse as float, we've reached metadata fields
                break

            field_index += 1

        # Get quality method (should be at current field_index)
        quality_method = fields[field_index] if field_index < len(fields) else 'A'

        # Remaining fields are optional metadata
        reason_code = None
        reason_description = None
        update_datetime = None
        msats_load_datetime = None

        if field_index + 1 < len(fields) and fields[field_index + 1]:
            try:
                reason_code = int(fields[field_index + 1])
            except ValueError:
                pass

        if field_index + 2 < len(fields):
            reason_description = fields[field_index + 2]

        if field_index + 3 < len(fields):
            update_datetime = fields[field_index + 3]

        if field_index + 4 < len(fields):
            msats_load_datetime = fields[field_index + 4]

        record_300 = Record300(
            interval_date=interval_date,
            interval_values=interval_values,
            quality_method=quality_method,
            reason_code=reason_code,
            reason_description=reason_description,
            update_datetime=update_datetime,
            msats_load_datetime=msats_load_datetime
        )

        self.records.append((self.current_record_200, record_300))

    def _create_dataframe(self) -> pd.DataFrame:
        """
        Convert parsed records into a DataFrame.

        Returns:
            DataFrame with one row per interval
        """
        if not self.records:
            raise ValueError("No valid interval data found in file")

        rows = []

        for record_200, record_300 in self.records:
            interval_date = record_300.interval_date
            interval_length_minutes = record_200.interval_length

            for interval_index, value in enumerate(record_300.interval_values):
                if value is None:
                    continue  # Skip missing values

                # Calculate timestamp for this interval
                # Interval 0 is from 00:00 to 00:30 (for 30-min intervals)
                naive_timestamp = interval_date + timedelta(minutes=interval_index * interval_length_minutes)
                # Convert naive timestamp to timezone-aware Industry time
                timestamp = localize_naive_to_industry(naive_timestamp)

                # Determine if this is an estimate
                is_estimate = record_300.quality_method in ['E', 'F', 'S']

                rows.append({
                    'timestamp': timestamp,
                    'nmi': record_200.nmi,
                    'register_id': record_200.register_id,
                    'consumption_kwh': value,
                    'quality_method': record_300.quality_method,
                    'is_estimate': is_estimate
                })

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
        if not self.records:
            return {}

        first_record_200, _ = self.records[0]

        nmis = set(rec[0].nmi for rec in self.records)

        return {
            'nmi': first_record_200.nmi,
            'all_nmis': list(nmis),
            'register_id': first_record_200.register_id,
            'meter_serial': first_record_200.meter_serial_number,
            'uom': first_record_200.uom,
            'interval_length_minutes': first_record_200.interval_length,
            'total_days': len(self.records)
        }
