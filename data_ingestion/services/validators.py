"""
Data validation service for ensuring data quality.
"""
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re


class DataValidator:
    """Validate data according to dataset type and business rules."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, dataset_type: str, 
                          column_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a DataFrame based on dataset type and column mapping.
        
        Args:
            df: Pandas DataFrame to validate
            dataset_type: Type of dataset (sales, customers, products, etc.)
            column_mapping: Column mapping results from ColumnMapper
            
        Returns:
            Validation results dictionary
        """
        validation_result = {
            'total_rows': len(df),
            'valid_rows': 0,
            'invalid_rows': 0,
            'warning_count': 0,
            'error_count': 0,
            'duplicate_count': 0,
            'missing_value_info': {},
            'column_errors': {},
            'row_errors': [],
            'can_import': True,
            'validation_summary': ''
        }
        
        if df.empty:
            validation_result['can_import'] = False
            validation_result['validation_summary'] = 'File is empty'
            return validation_result
        
        mapping = column_mapping.get('mapping', {})
        mapped_columns = {info['detected_column']: canonical for canonical, info in mapping.items()}
        
        # Check for required columns
        required_columns = DataValidator._get_required_columns(dataset_type)
        missing_required = [col for col in required_columns if col not in mapping]
        
        if missing_required:
            validation_result['can_import'] = False
            validation_result['error_count'] += len(missing_required)
            validation_result['column_errors']['missing_required'] = missing_required
            validation_result['validation_summary'] = f'Missing required columns: {", ".join(missing_required)}'
        
        # Analyze missing values
        for column in df.columns:
            missing_count = df[column].isna().sum()
            if missing_count > 0:
                canonical_name = mapped_columns.get(column, column)
                validation_result['missing_value_info'][canonical_name] = {
                    'count': int(missing_count),
                    'percentage': round((missing_count / len(df)) * 100, 2)
                }
        
        # Check for duplicates
        duplicate_count = df.duplicated().sum()
        validation_result['duplicate_count'] = int(duplicate_count)
        
        # Validate based on dataset type
        type_specific_validation = DataValidator._validate_by_type(
            df, dataset_type, mapping, mapped_columns
        )
        validation_result.update(type_specific_validation)
        
        # Calculate final counts
        validation_result['invalid_rows'] = validation_result['error_count']
        validation_result['valid_rows'] = validation_result['total_rows'] - validation_result['invalid_rows']
        
        # Generate summary
        validation_result['validation_summary'] = DataValidator._generate_summary(validation_result)
        
        return validation_result
    
    @staticmethod
    def _get_required_columns(dataset_type: str) -> List[str]:
        """Get required columns for dataset type."""
        requirements = {
            'sales': ['date', 'revenue'],
            'customers': ['customer_id'],
            'products': ['product_id', 'product_name'],
            'expenses': ['date', 'expense_amount'],
            'inventory': ['product_id', 'inventory_quantity'],
            'transactions': ['date', 'revenue'],
        }
        return requirements.get(dataset_type, [])
    
    @staticmethod
    def _validate_by_type(df: pd.DataFrame, dataset_type: str, 
                         mapping: Dict[str, Any], mapped_columns: Dict[str, str]) -> Dict[str, Any]:
        """Perform dataset type-specific validation."""
        result = {
            'error_count': 0,
            'warning_count': 0,
            'column_errors': {},
            'row_errors': []
        }
        
        if dataset_type == 'sales':
            result.update(DataValidator._validate_sales(df, mapping, mapped_columns))
        elif dataset_type == 'customers':
            result.update(DataValidator._validate_customers(df, mapping, mapped_columns))
        elif dataset_type == 'products':
            result.update(DataValidator._validate_products(df, mapping, mapped_columns))
        elif dataset_type == 'expenses':
            result.update(DataValidator._validate_expenses(df, mapping, mapped_columns))
        elif dataset_type == 'inventory':
            result.update(DataValidator._validate_inventory(df, mapping, mapped_columns))
        
        return result
    
    @staticmethod
    def _validate_sales(df: pd.DataFrame, mapping: Dict[str, Any], 
                      mapped_columns: Dict[str, str]) -> Dict[str, Any]:
        """Validate sales data."""
        errors = []
        warnings = []
        column_errors = {}
        
        # Validate date column
        if 'date' in mapping:
            date_col = mapping['date']['detected_column']
            try:
                pd.to_datetime(df[date_col], errors='coerce')
                invalid_dates = df[date_col].isna().sum()
                if invalid_dates > 0:
                    warnings.append(f'{invalid_dates} rows have invalid dates')
            except Exception as e:
                errors.append(f'Date column error: {str(e)}')
        
        # Validate revenue column
        if 'revenue' in mapping:
            revenue_col = mapping['revenue']['detected_column']
            try:
                # Check for non-numeric values
                non_numeric = df[revenue_col].apply(lambda x: not pd.api.types.is_numeric_dtype(type(x)))
                if non_numeric.any():
                    errors.append(f'Revenue column contains non-numeric values')
                
                # Check for negative values
                numeric_revenue = pd.to_numeric(df[revenue_col], errors='coerce')
                negative_count = (numeric_revenue < 0).sum()
                if negative_count > 0:
                    warnings.append(f'{negative_count} rows have negative revenue values')
            except Exception as e:
                errors.append(f'Revenue column error: {str(e)}')
        
        # Validate quantity column if present
        if 'quantity' in mapping:
            qty_col = mapping['quantity']['detected_column']
            try:
                numeric_qty = pd.to_numeric(df[qty_col], errors='coerce')
                negative_qty = (numeric_qty < 0).sum()
                if negative_qty > 0:
                    warnings.append(f'{negative_qty} rows have negative quantity values')
            except Exception as e:
                errors.append(f'Quantity column error: {str(e)}')
        
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'column_errors': column_errors,
            'row_errors': errors + warnings
        }
    
    @staticmethod
    def _validate_customers(df: pd.DataFrame, mapping: Dict[str, Any], 
                           mapped_columns: Dict[str, str]) -> Dict[str, Any]:
        """Validate customer data."""
        errors = []
        warnings = []
        
        # Validate customer ID uniqueness
        if 'customer_id' in mapping:
            cust_id_col = mapping['customer_id']['detected_column']
            duplicate_ids = df[cust_id_col].duplicated().sum()
            if duplicate_ids > 0:
                errors.append(f'{duplicate_ids} duplicate customer IDs found')
        
        # Validate email format if present
        if 'email' in mapping:
            email_col = mapping['email']['detected_column']
            invalid_emails = 0
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for email in df[email_col].dropna():
                if not re.match(email_pattern, str(email)):
                    invalid_emails += 1
            
            if invalid_emails > 0:
                warnings.append(f'{invalid_emails} rows have invalid email format')
        
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'row_errors': errors + warnings
        }
    
    @staticmethod
    def _validate_products(df: pd.DataFrame, mapping: Dict[str, Any], 
                           mapped_columns: Dict[str, str]) -> Dict[str, Any]:
        """Validate product data."""
        errors = []
        warnings = []
        
        # Validate product ID uniqueness
        if 'product_id' in mapping:
            prod_id_col = mapping['product_id']['detected_column']
            duplicate_ids = df[prod_id_col].duplicated().sum()
            if duplicate_ids > 0:
                errors.append(f'{duplicate_ids} duplicate product IDs found')
        
        # Validate product name presence
        if 'product_name' in mapping:
            name_col = mapping['product_name']['detected_column']
            missing_names = df[name_col].isna().sum()
            if missing_names > 0:
                warnings.append(f'{missing_names} rows have missing product names')
        
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'row_errors': errors + warnings
        }
    
    @staticmethod
    def _validate_expenses(df: pd.DataFrame, mapping: Dict[str, Any], 
                          mapped_columns: Dict[str, str]) -> Dict[str, Any]:
        """Validate expense data."""
        errors = []
        warnings = []
        
        # Validate date column
        if 'date' in mapping:
            date_col = mapping['date']['detected_column']
            try:
                pd.to_datetime(df[date_col], errors='coerce')
                invalid_dates = df[date_col].isna().sum()
                if invalid_dates > 0:
                    warnings.append(f'{invalid_dates} rows have invalid dates')
            except Exception as e:
                errors.append(f'Date column error: {str(e)}')
        
        # Validate amount column
        if 'expense_amount' in mapping:
            amount_col = mapping['expense_amount']['detected_column']
            try:
                numeric_amount = pd.to_numeric(df[amount_col], errors='coerce')
                negative_amount = (numeric_amount < 0).sum()
                if negative_amount > 0:
                    warnings.append(f'{negative_amount} rows have negative expense amounts')
            except Exception as e:
                errors.append(f'Expense amount column error: {str(e)}')
        
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'row_errors': errors + warnings
        }
    
    @staticmethod
    def _validate_inventory(df: pd.DataFrame, mapping: Dict[str, Any], 
                           mapped_columns: Dict[str, str]) -> Dict[str, Any]:
        """Validate inventory data."""
        errors = []
        warnings = []
        
        # Validate product ID presence
        if 'product_id' in mapping:
            prod_id_col = mapping['product_id']['detected_column']
            missing_ids = df[prod_id_col].isna().sum()
            if missing_ids > 0:
                errors.append(f'{missing_ids} rows have missing product IDs')
        
        # Validate quantity column
        if 'inventory_quantity' in mapping:
            qty_col = mapping['inventory_quantity']['detected_column']
            try:
                numeric_qty = pd.to_numeric(df[qty_col], errors='coerce')
                negative_qty = (numeric_qty < 0).sum()
                if negative_qty > 0:
                    warnings.append(f'{negative_qty} rows have negative inventory quantities')
            except Exception as e:
                errors.append(f'Inventory quantity column error: {str(e)}')
        
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'row_errors': errors + warnings
        }
    
    @staticmethod
    def _generate_summary(validation_result: Dict[str, Any]) -> str:
        """Generate human-readable validation summary."""
        if not validation_result['can_import']:
            return "File requires correction before it can be imported."
        
        if validation_result['error_count'] == 0 and validation_result['warning_count'] == 0:
            return "File was successfully analyzed and is ready for import."
        
        if validation_result['error_count'] > 0:
            return f"File has {validation_result['error_count']} errors that need correction."
        
        if validation_result['warning_count'] > 0:
            return f"File has {validation_result['warning_count']} warnings but can be imported."
        
        return "File was successfully analyzed."
