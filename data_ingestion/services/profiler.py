"""
Data profiling service for analyzing uploaded files.
"""
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime


class DataProfiler:
    """Profile and analyze data from uploaded files."""
    
    @staticmethod
    def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive profile of a DataFrame.
        
        Args:
            df: Pandas DataFrame to profile
            
        Returns:
            Dictionary containing profiling results
        """
        if df.empty:
            return {
                'row_count': 0,
                'column_count': 0,
                'columns': [],
                'data_types': {},
                'missing_values': {},
                'duplicate_rows': 0,
                'unique_values': {},
                'sample_data': [],
                'numeric_stats': {},
                'date_stats': {},
            }
        
        profile = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'data_types': {},
            'missing_values': {},
            'duplicate_rows': df.duplicated().sum(),
            'unique_values': {},
            'sample_data': df.head(5).to_dict('records') if len(df) > 0 else [],
            'numeric_stats': {},
            'date_stats': {},
        }
        
        # Analyze each column
        for column in df.columns:
            col_data = df[column]
            
            # Data type
            profile['data_types'][column] = str(col_data.dtype)
            
            # Missing values
            missing_count = col_data.isna().sum()
            profile['missing_values'][column] = {
                'count': int(missing_count),
                'percentage': round((missing_count / len(df)) * 100, 2) if len(df) > 0 else 0
            }
            
            # Unique values (for columns with reasonable cardinality)
            unique_count = col_data.nunique()
            if unique_count <= 50:
                profile['unique_values'][column] = {
                    'count': int(unique_count),
                    'values': col_data.dropna().unique().tolist()[:20]  # Limit to 20 values
                }
            else:
                profile['unique_values'][column] = {
                    'count': int(unique_count),
                    'values': []
                }
            
            # Numeric statistics
            if pd.api.types.is_numeric_dtype(col_data):
                profile['numeric_stats'][column] = {
                    'min': float(col_data.min()) if not col_data.isna().all() else None,
                    'max': float(col_data.max()) if not col_data.isna().all() else None,
                    'mean': float(col_data.mean()) if not col_data.isna().all() else None,
                    'median': float(col_data.median()) if not col_data.isna().all() else None,
                    'std': float(col_data.std()) if not col_data.isna().all() else None,
                }
            
            # Date statistics
            if DataProfiler._is_date_column(col_data):
                try:
                    col_dates = pd.to_datetime(col_data, errors='coerce')
                    valid_dates = col_dates.dropna()
                    if len(valid_dates) > 0:
                        profile['date_stats'][column] = {
                            'min_date': valid_dates.min().isoformat(),
                            'max_date': valid_dates.max().isoformat(),
                            'date_range_days': (valid_dates.max() - valid_dates.min()).days
                        }
                except Exception:
                    pass
        
        return profile
    
    @staticmethod
    def _is_date_column(series: pd.Series) -> bool:
        """
        Check if a series appears to contain date/datetime data.
        
        Args:
            series: Pandas Series to check
            
        Returns:
            True if series appears to be date data
        """
        # Check if column name suggests dates
        date_keywords = ['date', 'time', 'day', 'month', 'year', 'created', 'updated', 'timestamp']
        col_name_lower = str(series.name).lower()
        if any(keyword in col_name_lower for keyword in date_keywords):
            return True
        
        # Try to convert to datetime
        try:
            sample = series.dropna().head(100)
            if len(sample) > 0:
                pd.to_datetime(sample, errors='coerce')
                return True
        except Exception:
            pass
        
        return False
    
    @staticmethod
    def detect_dataset_type(profile: Dict[str, Any]) -> str:
        """
        Detect likely dataset type based on column names and data.
        
        Args:
            profile: Profiling results from profile_dataframe
            
        Returns:
            Detected dataset type (sales, customers, products, expenses, inventory, transactions, unknown)
        """
        columns = [col.lower() for col in profile.get('columns', [])]
        
        # Sales/Transactions detection
        sales_keywords = ['revenue', 'sales', 'amount', 'total', 'price', 'quantity', 'qty', 'order', 'transaction']
        if any(keyword in ' '.join(columns) for keyword in sales_keywords):
            return 'sales'
        
        # Customers detection
        customer_keywords = ['customer', 'client', 'email', 'phone', 'address', 'name']
        if any(keyword in ' '.join(columns) for keyword in customer_keywords):
            return 'customers'
        
        # Products detection
        product_keywords = ['product', 'item', 'sku', 'category', 'inventory', 'stock']
        if any(keyword in ' '.join(columns) for keyword in product_keywords):
            return 'products'
        
        # Expenses detection
        expense_keywords = ['expense', 'cost', 'spending', 'budget', 'payment']
        if any(keyword in ' '.join(columns) for keyword in expense_keywords):
            return 'expenses'
        
        # Inventory detection
        inventory_keywords = ['inventory', 'stock', 'quantity', 'on_hand', 'available']
        if any(keyword in ' '.join(columns) for keyword in inventory_keywords):
            return 'inventory'
        
        return 'unknown'
