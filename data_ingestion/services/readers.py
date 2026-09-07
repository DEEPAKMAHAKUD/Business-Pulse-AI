"""
File readers for CSV and Excel files.
"""
import pandas as pd
from io import BytesIO
from typing import Tuple, Optional


class FileReader:
    """Base class for file readers."""
    
    @staticmethod
    def read_file(file_content: bytes, file_type: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read file content and return DataFrame with error message if failed.
        
        Args:
            file_content: Raw file bytes
            file_type: File type ('csv', 'xlsx', 'xls')
            
        Returns:
            Tuple of (DataFrame, error_message). If successful, error_message is None.
        """
        try:
            if file_type == 'csv':
                return FileReader._read_csv(file_content)
            elif file_type in ['xlsx', 'xls']:
                return FileReader._read_excel(file_content)
            else:
                return None, f"Unsupported file type: {file_type}"
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
    
    @staticmethod
    def _read_csv(file_content: bytes) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Read CSV file content."""
        try:
            df = pd.read_csv(BytesIO(file_content))
            return df, None
        except pd.errors.EmptyDataError:
            return None, "CSV file is empty"
        except pd.errors.ParserError as e:
            return None, f"CSV parsing error: {str(e)}"
        except Exception as e:
            return None, f"Error reading CSV: {str(e)}"
    
    @staticmethod
    def _read_excel(file_content: bytes) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Read Excel file content."""
        try:
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
            return df, None
        except ValueError as e:
            return None, f"Excel file error: {str(e)}"
        except Exception as e:
            return None, f"Error reading Excel file: {str(e)}"
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Validate file size against maximum allowed size.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in megabytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"
        if file_size == 0:
            return False, "File is empty"
        return True, None
