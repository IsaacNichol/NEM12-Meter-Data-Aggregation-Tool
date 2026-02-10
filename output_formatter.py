"""Output formatting module for displaying and saving aggregated results."""

import pandas as pd
from datetime import datetime
from tabulate import tabulate
from typing import Optional
from utils import format_currency, format_number


class OutputFormatter:
    """Formatter for aggregated meter data results."""

    def __init__(self, aggregated_df: pd.DataFrame, summary_stats: dict, nmi: str):
        """
        Initialize formatter.

        Args:
            aggregated_df: DataFrame with aggregated results by period
            summary_stats: Dictionary of summary statistics
            nmi: National Metering Identifier
        """
        self.agg_df = aggregated_df
        self.stats = summary_stats
        self.nmi = nmi

    def display_console(self):
        """Display formatted results to console."""
        print("\n" + "=" * 70)
        print("NEM12 METER DATA AGGREGATION RESULTS")
        print("=" * 70)

        # Header information
        print(f"\nNMI: {self.nmi}")
        print(f"Date Range: {self.stats['date_range_start'].strftime('%Y-%m-%d')} to {self.stats['date_range_end'].strftime('%Y-%m-%d')}")
        print(f"Total Days: {self.stats['total_days']}")
        print(f"Total Intervals: {format_number(self.stats['total_intervals'], 0)}")

        # Estimated data warning
        if self.stats['estimated_percentage'] > 0:
            print(f"\n⚠ Warning: {self.stats['estimated_percentage']:.1f}% of data is estimated")

        # Period summary table
        print("\n" + "-" * 70)
        print("PERIOD SUMMARY")
        print("-" * 70)

        table_data = []
        has_costs = self.agg_df['total_cost'].notna().any()

        for _, row in self.agg_df.iterrows():
            row_data = [
                row['period'],
                format_number(row['total_kwh'], 2),
                format_number(row['interval_count'], 0),
                format_number(row['avg_kwh_per_interval'], 2),
            ]

            if has_costs:
                if pd.notna(row['total_cost']):
                    row_data.append(format_currency(row['total_cost']))
                else:
                    row_data.append('-')

            table_data.append(row_data)

        # Add total row
        total_kwh = self.agg_df['total_kwh'].sum()
        total_intervals = self.agg_df['interval_count'].sum()
        avg_kwh = total_kwh / total_intervals if total_intervals > 0 else 0

        total_row = [
            'TOTAL',
            format_number(total_kwh, 2),
            format_number(total_intervals, 0),
            format_number(avg_kwh, 2),
        ]

        if has_costs:
            total_cost = self.agg_df['total_cost'].sum()
            if pd.notna(total_cost):
                total_row.append(format_currency(total_cost))
            else:
                total_row.append('-')

        table_data.append(total_row)

        # Define headers
        headers = ['Period', 'Total kWh', 'Intervals', 'Avg kWh/Int']
        if has_costs:
            headers.append('Total Cost')

        # Print table
        print(tabulate(table_data, headers=headers, tablefmt='simple', stralign='right', numalign='right'))

        # Period distribution
        print("\n" + "-" * 70)
        print("PERIOD DISTRIBUTION")
        print("-" * 70)

        for _, row in self.agg_df.iterrows():
            if row['period'] != 'TOTAL':
                print(f"{row['period']:.<30} {row['percentage']:>6.1f}% of total consumption")

        # Unclassified warning
        if self.stats['unclassified_percentage'] > 0:
            print(f"\n⚠ Warning: {self.stats['unclassified_percentage']:.1f}% of intervals are unclassified")
            print("  Consider adding more time ranges to your period definitions")

        # Day type breakdown
        print("\n" + "-" * 70)
        print("DAY TYPE BREAKDOWN")
        print("-" * 70)
        print(f"Weekday intervals: {format_number(self.stats['weekday_intervals'], 0)}")
        print(f"Weekend intervals: {format_number(self.stats['weekend_intervals'], 0)}")
        print(f"Holiday intervals: {format_number(self.stats['holiday_intervals'], 0)}")

        print("\n" + "=" * 70)

    def save_csv(self, filepath: Optional[str] = None) -> str:
        """
        Save aggregated results to CSV file.

        Args:
            filepath: Optional output filepath. If None, auto-generates filename.

        Returns:
            Path to saved file
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"aggregated_results_{self.nmi}_{timestamp}.csv"

        # Prepare DataFrame for export
        export_df = self.agg_df.copy()

        # Format columns for CSV
        export_df['Total_kWh'] = export_df['total_kwh'].round(2)
        export_df['Interval_Count'] = export_df['interval_count'].astype(int)
        export_df['Avg_kWh_per_Interval'] = export_df['avg_kwh_per_interval'].round(2)
        export_df['Percentage'] = export_df['percentage'].round(2)

        # Handle cost column
        if export_df['total_cost'].notna().any():
            export_df['Total_Cost'] = export_df['total_cost'].round(2)
        else:
            export_df = export_df.drop('total_cost', axis=1)

        # Select and rename columns for export
        columns_to_export = {
            'period': 'Period',
            'Total_kWh': 'Total_kWh',
            'Interval_Count': 'Interval_Count',
            'Avg_kWh_per_Interval': 'Avg_kWh_per_Interval',
            'Percentage': 'Percentage_of_Total'
        }

        if 'Total_Cost' in export_df.columns:
            columns_to_export['Total_Cost'] = 'Total_Cost'

        export_df = export_df.rename(columns=columns_to_export)
        export_df = export_df[[col for col in columns_to_export.values() if col in export_df.columns]]

        # Save to CSV
        export_df.to_csv(filepath, index=False)

        return filepath

    def save_detailed_csv(self, classified_df: pd.DataFrame, filepath: Optional[str] = None) -> str:
        """
        Save detailed interval-level data with period classifications.

        Args:
            classified_df: DataFrame with classified intervals
            filepath: Optional output filepath. If None, auto-generates filename.

        Returns:
            Path to saved file
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"detailed_intervals_{self.nmi}_{timestamp}.csv"

        # Prepare DataFrame for export
        export_df = classified_df.copy()

        # Select and format columns
        export_df = export_df[[
            'timestamp',
            'consumption_kwh',
            'period',
            'day_type',
            'quality_method',
            'is_estimate'
        ]]

        export_df = export_df.rename(columns={
            'timestamp': 'Timestamp',
            'consumption_kwh': 'Consumption_kWh',
            'period': 'Period',
            'day_type': 'Day_Type',
            'quality_method': 'Quality_Method',
            'is_estimate': 'Is_Estimate'
        })

        # Sort by timestamp
        export_df = export_df.sort_values('Timestamp')

        # Save to CSV
        export_df.to_csv(filepath, index=False)

        return filepath
