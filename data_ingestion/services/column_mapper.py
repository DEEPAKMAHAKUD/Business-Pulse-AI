"""
Column detection and mapping service for intelligent field recognition.
"""
from typing import Dict, List, Tuple, Any
import re


class ColumnMapper:
    """Detect and map columns to canonical field names."""
    
    # Canonical field mappings with common aliases
    COLUMN_MAPPINGS = {
        # Revenue/Sales amount
        'revenue': ['revenue', 'sales', 'sales_amount', 'amount', 'total', 'total_amount', 'net_sales', 
                   'gross_sales', 'income', 'turnover', 'sales_value', 'revenue_amount'],
        
        # Customer identifiers
        'customer_id': ['customer_id', 'client_id', 'customer', 'client', 'cust_id', 'client_num', 
                      'customer_number', 'client_number', 'cust_number'],
        
        # Product identifiers
        'product_id': ['product_id', 'product', 'item', 'sku', 'item_id', 'product_code', 
                      'item_code', 'product_num', 'product_number'],
        
        # Date fields
        'date': ['date', 'order_date', 'transaction_date', 'sale_date', 'purchase_date', 
                'created_date', 'orderdate', 'transactiondate', 'saledate'],
        
        # Quantity
        'quantity': ['quantity', 'qty', 'units', 'amount', 'count', 'num_items', 'item_count'],
        
        # Category
        'category': ['category', 'product_category', 'type', 'group', 'classification', 'segment'],
        
        # Price
        'price': ['price', 'unit_price', 'unitprice', 'price_per_unit', 'selling_price'],
        
        # Customer name
        'customer_name': ['customer_name', 'client_name', 'name', 'customer', 'client'],
        
        # Email
        'email': ['email', 'email_address', 'mail', 'contact_email'],
        
        # Phone
        'phone': ['phone', 'telephone', 'mobile', 'contact_phone', 'phone_number'],
        
        # Address
        'address': ['address', 'shipping_address', 'billing_address', 'location'],
        
        # Product name
        'product_name': ['product_name', 'item_name', 'name', 'description', 'product'],
        
        # SKU
        'sku': ['sku', 'stock_keeping_unit', 'stock_code', 'item_code'],
        
        # Expense amount
        'expense_amount': ['expense', 'amount', 'cost', 'price', 'expense_amount', 'spending'],
        
        # Expense category
        'expense_category': ['category', 'expense_category', 'cost_category', 'type'],
        
        # Expense description
        'description': ['description', 'notes', 'details', 'comments', 'remark'],
        
        # Inventory quantity
        'inventory_quantity': ['quantity', 'stock', 'on_hand', 'available', 'inventory', 'stock_level'],
        
        # Transaction/Sale ID
        'transaction_id': ['transaction_id', 'sale_id', 'order_id', 'order_number', 'transaction', 
                         'sale', 'order', 'id', 'transaction_number'],
        
        # Expense ID
        'expense_id': ['expense_id', 'expense_number', 'cost_id', 'payment_id'],
    }
    
    @staticmethod
    def detect_mapping(columns: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect column mappings from actual column names to canonical fields.
        
        Args:
            columns: List of actual column names from the uploaded file
            
        Returns:
            Dictionary mapping canonical fields to detection results:
            {
                'canonical_field': {
                    'detected_column': 'actual_column_name',
                    'confidence': 0.95,
                    'aliases_matched': ['alias1', 'alias2']
                }
            }
        """
        mapping = {}
        unmapped_columns = []
        ambiguous_mappings = []
        
        for canonical_field, aliases in ColumnMapper.COLUMN_MAPPINGS.items():
            best_match = None
            best_confidence = 0.0
            matched_aliases = []
            
            for column in columns:
                column_lower = column.lower().strip()
                column_normalized = ColumnMapper._normalize_column_name(column_lower)
                
                for alias in aliases:
                    alias_lower = alias.lower()
                    alias_normalized = ColumnMapper._normalize_column_name(alias_lower)
                    
                    # Exact match
                    if column_lower == alias_lower:
                        confidence = 1.0
                        if confidence > best_confidence:
                            best_match = column
                            best_confidence = confidence
                            matched_aliases = [alias]
                    
                    # Normalized match
                    elif column_normalized == alias_normalized:
                        confidence = 0.9
                        if confidence > best_confidence:
                            best_match = column
                            best_confidence = confidence
                            matched_aliases = [alias]
                    
                    # Partial match (contains)
                    elif alias_lower in column_lower or column_lower in alias_lower:
                        confidence = 0.7
                        if confidence > best_confidence:
                            best_match = column
                            best_confidence = confidence
                            matched_aliases = [alias]
            
            if best_match and best_confidence >= 0.7:
                mapping[canonical_field] = {
                    'detected_column': best_match,
                    'confidence': best_confidence,
                    'aliases_matched': matched_aliases
                }
        
        # Find unmapped columns
        mapped_columns = {info['detected_column'] for info in mapping.values()}
        for column in columns:
            if column not in mapped_columns:
                unmapped_columns.append(column)
        
        # Find ambiguous mappings (same column mapped to multiple canonical fields)
        column_usage = {}
        for canonical_field, info in mapping.items():
            detected_col = info['detected_column']
            if detected_col in column_usage:
                column_usage[detected_col].append(canonical_field)
            else:
                column_usage[detected_col] = [canonical_field]
        
        for column, fields in column_usage.items():
            if len(fields) > 1:
                ambiguous_mappings.append({
                    'column': column,
                    'mapped_to': fields
                })
        
        return {
            'mapping': mapping,
            'unmapped_columns': unmapped_columns,
            'ambiguous_mappings': ambiguous_mappings
        }
    
    @staticmethod
    def _normalize_column_name(name: str) -> str:
        """
        Normalize column name for comparison.
        
        Args:
            name: Column name to normalize
            
        Returns:
            Normalized column name
        """
        # Remove special characters and spaces
        normalized = re.sub(r'[^a-zA-Z0-9]', '', name)
        return normalized.lower()
    
    @staticmethod
    def apply_mapping(df, mapping: Dict[str, str]) -> any:
        """
        Apply column mapping to a DataFrame.
        
        Args:
            df: Pandas DataFrame
            mapping: Dictionary mapping canonical fields to actual column names
            
        Returns:
            DataFrame with renamed columns
        """
        reverse_mapping = {v: k for k, v in mapping.items()}
        return df.rename(columns=reverse_mapping)
    
    @staticmethod
    def get_required_columns(dataset_type: str) -> List[str]:
        """
        Get required columns for a specific dataset type.
        
        Args:
            dataset_type: Type of dataset (sales, customers, products, etc.)
            
        Returns:
            List of required canonical field names
        """
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
    def get_optional_columns(dataset_type: str) -> List[str]:
        """
        Get optional columns for a specific dataset type.
        
        Args:
            dataset_type: Type of dataset (sales, customers, products, etc.)
            
        Returns:
            List of optional canonical field names
        """
        optionals = {
            'sales': ['customer_id', 'product_id', 'quantity', 'category', 'transaction_id'],
            'customers': ['customer_name', 'email', 'phone', 'address'],
            'products': ['sku', 'category', 'price', 'description'],
            'expenses': ['expense_category', 'description', 'expense_id'],
            'inventory': ['inventory_quantity'],
            'transactions': ['customer_id', 'product_id', 'quantity', 'category', 'transaction_id'],
        }
        
        return optionals.get(dataset_type, [])
