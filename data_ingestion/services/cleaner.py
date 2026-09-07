"""
Data cleaning service for safe, deterministic data transformations.
"""
import pandas as pd
from typing import Dict, List, Any, Tuple
import re


class DataCleaner:
    """Clean and normalize data safely without fabricating information."""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame, dataset_type: str, 
                       column_mapping: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Clean a DataFrame based on dataset type and column mapping.
        
        Args:
            df: Pandas DataFrame to clean
            dataset_type: Type of dataset (sales, customers, products, etc.)
            column_mapping: Column mapping results from ColumnMapper
            
        Returns:
            Tuple of (cleaned DataFrame, cleaning summary)
        """
        df_cleaned = df.copy()
        cleaning_summary = {
            'operations_performed': [],
            'rows_before': len(df),
            'rows_after': len(df),
            'columns_renamed': {},
            'dates_parsed': [],
            'numbers_converted': [],
            'whitespace_trimmed': [],
            'nulls_standardized': [],
            'duplicates_removed': 0
        }
        
        mapping = column_mapping.get('mapping', {})
        
        # 1. Trim whitespace from string columns
        df_cleaned, trimmed_cols = DataCleaner._trim_whitespace(df_cleaned)
        if trimmed_cols:
            cleaning_summary['whitespace_trimmed'] = trimmed_cols
            cleaning_summary['operations_performed'].append('trim_whitespace')
        
        # 2. Normalize column names
        df_cleaned, renamed_cols = DataCleaner._normalize_column_names(df_cleaned, mapping)
        if renamed_cols:
            cleaning_summary['columns_renamed'] = renamed_cols
            cleaning_summary['operations_performed'].append('normalize_column_names')
        
        # 3. Standardize null representations
        df_cleaned, null_cols = DataCleaner._standardize_nulls(df_cleaned)
        if null_cols:
            cleaning_summary['nulls_standardized'] = null_cols
            cleaning_summary['operations_performed'].append('standardize_nulls')
        
        # 4. Parse dates
        df_cleaned, date_cols = DataCleaner._parse_dates(df_cleaned, dataset_type, mapping)
        if date_cols:
            cleaning_summary['dates_parsed'] = date_cols
            cleaning_summary['operations_performed'].append('parse_dates')
        
        # 5. Convert numeric fields
        df_cleaned, numeric_cols = DataCleaner._convert_numeric(df_cleaned, dataset_type, mapping)
        if numeric_cols:
            cleaning_summary['numbers_converted'] = numeric_cols
            cleaning_summary['operations_performed'].append('convert_numeric')
        
        # 6. Remove exact duplicates (only if appropriate)
        should_remove_duplicates = DataCleaner._should_remove_duplicates(dataset_type)
        if should_remove_duplicates:
            df_cleaned, duplicates_removed = DataCleaner._remove_exact_duplicates(df_cleaned)
            if duplicates_removed > 0:
                cleaning_summary['duplicates_removed'] = duplicates_removed
                cleaning_summary['operations_performed'].append('remove_exact_duplicates')
        
        cleaning_summary['rows_after'] = len(df_cleaned)
        
        return df_cleaned, cleaning_summary
    
    @staticmethod
    def _trim_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Trim whitespace from string columns."""
        df_cleaned = df.copy()
        trimmed_columns = []
        
        for column in df.columns:
            if df[column].dtype == 'object':
                # Trim leading/trailing whitespace
                df_cleaned[column] = df[column].astype(str).str.strip()
                trimmed_columns.append(column)
        
        return df_cleaned, trimmed_columns
    
    @staticmethod
    def _normalize_column_names(df: pd.DataFrame, mapping: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Rename columns to canonical names based on mapping."""
        df_cleaned = df.copy()
        renamed_columns = {}
        
        # Create reverse mapping: actual column -> canonical name
        for canonical_field, info in mapping.items():
            actual_column = info['detected_column']
            if actual_column in df_cleaned.columns and actual_column != canonical_field:
                df_cleaned = df_cleaned.rename(columns={actual_column: canonical_field})
                renamed_columns[actual_column] = canonical_field
        
        return df_cleaned, renamed_columns
    
    @staticmethod
    def _standardize_nulls(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Standardize various null representations to NaN."""
        df_cleaned = df.copy()
        null_columns = []
        
        # Common null representations
        null_values = ['', 'NA', 'N/A', 'null', 'NULL', 'None', 'none', '-', '--', 'NaN']
        
        for column in df.columns:
            if df[column].dtype == 'object':
                # Replace common null representations with actual NaN
                for null_val in null_values:
                    df_cleaned[column] = df_cleaned[column].replace(null_val, pd.NA)
                
                if df[column].isin(null_values).any():
                    null_columns.append(column)
        
        return df_cleaned, null_columns
    
    @staticmethod
    def _parse_dates(df: pd.DataFrame, dataset_type: str, 
                    mapping: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Parse date columns to datetime objects."""
        df_cleaned = df.copy()
        date_columns = []
        
        # Date-related canonical fields
        date_fields = ['date', 'order_date', 'transaction_date', 'sale_date', 
                      'purchase_date', 'created_date', 'recorded_at']
        
        for field in date_fields:
            if field in mapping and field in df_cleaned.columns:
                try:
                    # Parse dates with automatic format detection
                    df_cleaned[field] = pd.to_datetime(df_cleaned[field], errors='coerce')
                    date_columns.append(field)
                except Exception:
                    # If parsing fails, leave as is
                    pass
        
        return df_cleaned, date_columns
    
    @staticmethod
    def _convert_numeric(df: pd.DataFrame, dataset_type: str, 
                        mapping: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Convert appropriate columns to numeric types."""
        df_cleaned = df.copy()
        numeric_columns = []
        
        # Numeric fields by dataset type
        numeric_fields = {
            'sales': ['revenue', 'quantity', 'price'],
            'expenses': ['expense_amount', 'amount'],
            'inventory': ['inventory_quantity', 'quantity'],
            'products': ['price'],
        }
        
        target_fields = numeric_fields.get(dataset_type, [])
        
        for field in target_fields:
            if field in mapping and field in df_cleaned.columns:
                try:
                    # Convert to numeric, coercing errors to NaN
                    df_cleaned[field] = pd.to_numeric(df_cleaned[field], errors='coerce')
                    numeric_columns.append(field)
                except Exception:
                    # If conversion fails, leave as is
                    pass
        
        return df_cleaned, numeric_columns
    
    @staticmethod
    def _should_remove_duplicates(dataset_type: str) -> bool:
        """Determine if exact duplicates should be removed for this dataset type."""
        # Only remove duplicates for transactional data where exact duplicates are likely errors
        return dataset_type in ['sales', 'transactions', 'expenses']
    
    @staticmethod
    def _remove_exact_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Remove exact duplicate rows."""
        original_count = len(df)
        df_cleaned = df.drop_duplicates()
        duplicates_removed = original_count - len(df_cleaned)
        
        return df_cleaned, duplicates_removed
    
    @staticmethod
    def clean_string_value(value: Any) -> Any:
        """
        Clean a single string value.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        if pd.isna(value):
            return value
        
        if isinstance(value, str):
            # Trim whitespace
            value = value.strip()
            
            # If empty after trimming, return NaN
            if value == '':
                return pd.NA
        
        return value
    
    @staticmethod
    def safe_numeric_conversion(value: Any, default: Any = pd.NA) -> Any:
        """
        Safely convert a value to numeric.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Numeric value or default
        """
        try:
            return pd.to_numeric(value, errors='coerce')
        except Exception:
            return default
