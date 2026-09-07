"""
Comprehensive tests for data ingestion functionality.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from io import BytesIO
import pandas as pd
from businesses.models import Business
from .models import Dataset, DataImport, Customer, Product, Sale, Expense, InventoryRecord
from .services.readers import FileReader
from .services.profiler import DataProfiler
from .services.column_mapper import ColumnMapper
from .services.validators import DataValidator
from .services.cleaner import DataCleaner


class DataIngestionAuthenticationTests(TestCase):
    """Test authentication and authorization for data ingestion."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        self.business = Business.objects.create(owner=self.user, name='Test Business')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass123', email='other@example.com')
        self.other_business = Business.objects.create(owner=self.other_user, name='Other Business')
        self.client = Client()
    
    def test_upload_page_requires_authentication(self):
        """Test that upload page redirects unauthenticated users."""
        response = self.client.get(reverse('upload_data'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_upload_page_accessible_when_authenticated(self):
        """Test that authenticated users can access upload page."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('upload_data'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_cannot_access_other_business_dataset(self):
        """Test that users cannot access datasets from other businesses."""
        self.client.login(username='testuser', password='testpass123')
        
        # Create dataset for other business
        other_dataset = Dataset.objects.create(
            business=self.other_business,
            name='Other Dataset',
            dataset_type='sales'
        )
        
        # Try to access other user's dataset
        response = self.client.get(reverse('dataset_detail', kwargs={'dataset_id': other_dataset.id}))
        self.assertEqual(response.status_code, 404)  # Not found due to ownership check


class FileUploadTests(TestCase):
    """Test file upload functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        self.business = Business.objects.create(owner=self.user, name='Test Business')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_valid_csv_upload_succeeds(self):
        """Test that valid CSV file can be uploaded."""
        # Create a simple CSV file
        csv_content = b"date,revenue,quantity\n2024-01-01,100.50,5\n2024-01-02,200.75,10"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        
        # Create dataset
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        # Upload file
        response = self.client.post(reverse('upload_file', kwargs={'dataset_id': dataset.id}), {
            'uploaded_file': csv_file
        })
        
        # Check that import was created
        self.assertEqual(DataImport.objects.count(), 1)
        data_import = DataImport.objects.first()
        self.assertEqual(data_import.original_filename, 'test.csv')
        self.assertEqual(data_import.file_type, 'csv')
    
    def test_valid_xlsx_upload_succeeds(self):
        """Test that valid Excel file can be uploaded."""
        # Create a simple Excel file
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'revenue': [100.50, 200.75],
            'quantity': [5, 10]
        })
        
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        xlsx_file = SimpleUploadedFile("test.xlsx", excel_buffer.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        # Create dataset
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        # Upload file
        response = self.client.post(reverse('upload_file', kwargs={'dataset_id': dataset.id}), {
            'uploaded_file': xlsx_file
        })
        
        # Check that import was created
        self.assertEqual(DataImport.objects.count(), 1)
        data_import = DataImport.objects.first()
        self.assertEqual(data_import.original_filename, 'test.xlsx')
        self.assertEqual(data_import.file_type, 'xlsx')
    
    def test_unsupported_file_type_rejected(self):
        """Test that unsupported file types are rejected."""
        # Create a text file
        txt_content = b"This is not a CSV or Excel file"
        txt_file = SimpleUploadedFile("test.txt", txt_content, content_type="text/plain")
        
        # Create dataset
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        # Try to upload
        response = self.client.post(reverse('upload_file', kwargs={'dataset_id': dataset.id}), {
            'uploaded_file': txt_file
        })
        
        # Check that no import was created
        self.assertEqual(DataImport.objects.count(), 0)
    
    def test_empty_file_rejected(self):
        """Test that empty files are rejected."""
        empty_file = SimpleUploadedFile("empty.csv", b"", content_type="text/csv")
        
        # Create dataset
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        # Try to upload
        response = self.client.post(reverse('upload_file', kwargs={'dataset_id': dataset.id}), {
            'uploaded_file': empty_file
        })
        
        # Check that no import was created
        self.assertEqual(DataImport.objects.count(), 0)
    
    def test_file_size_validation_works(self):
        """Test that file size validation works."""
        # Create a large file (simulated)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile("large.csv", large_content, content_type="text/csv")
        
        # Create dataset
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        # Try to upload
        response = self.client.post(reverse('upload_file', kwargs={'dataset_id': dataset.id}), {
            'uploaded_file': large_file
        })
        
        # Check that no import was created
        self.assertEqual(DataImport.objects.count(), 0)


class DataProfilingTests(TestCase):
    """Test data profiling functionality."""
    
    def test_profiling_returns_correct_row_column_counts(self):
        """Test that profiling returns correct row and column counts."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'revenue': [100.50, 200.75, 150.25],
            'quantity': [5, 10, 7]
        })
        
        profile = DataProfiler.profile_dataframe(df)
        
        self.assertEqual(profile['row_count'], 3)
        self.assertEqual(profile['column_count'], 3)
    
    def test_profiling_detects_missing_values(self):
        """Test that profiling detects missing values."""
        df = pd.DataFrame({
            'date': ['2024-01-01', None, '2024-01-03'],
            'revenue': [100.50, 200.75, None],
            'quantity': [5, 10, 7]
        })
        
        profile = DataProfiler.profile_dataframe(df)
        
        self.assertEqual(profile['missing_values']['date']['count'], 1)
        self.assertEqual(profile['missing_values']['revenue']['count'], 1)
    
    def test_profiling_detects_duplicate_rows(self):
        """Test that profiling detects duplicate rows."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'revenue': [100.50, 100.50, 200.75],
            'quantity': [5, 5, 10]
        })
        
        profile = DataProfiler.profile_dataframe(df)
        
        self.assertEqual(profile['duplicate_rows'], 1)
    
    def test_profiling_infers_data_types(self):
        """Test that profiling infers data types correctly."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'revenue': [100.50, 200.75],
            'quantity': [5, 10]
        })
        
        profile = DataProfiler.profile_dataframe(df)
        
        self.assertIn('data_types', profile)
        self.assertEqual(len(profile['data_types']), 3)


class ColumnMappingTests(TestCase):
    """Test column detection and mapping functionality."""
    
    def test_column_detection_works_for_common_aliases(self):
        """Test that column detection works for common aliases."""
        columns = ['order_date', 'sales_amount', 'customer_id', 'qty']
        
        mapping_result = ColumnMapper.detect_mapping(columns)
        mapping = mapping_result['mapping']
        
        # Check that common columns were detected
        self.assertIn('date', mapping)
        self.assertIn('revenue', mapping)
        self.assertIn('customer_id', mapping)
        self.assertIn('quantity', mapping)
    
    def test_ambiguous_mappings_are_reported(self):
        """Test that ambiguous column mappings are reported."""
        columns = ['amount', 'sales', 'total']
        
        mapping_result = ColumnMapper.detect_mapping(columns)
        
        # Check that ambiguous mappings are reported
        self.assertIn('ambiguous_mappings', mapping_result)
    
    def test_unmapped_columns_are_reported(self):
        """Test that unmapped columns are reported."""
        columns = ['date', 'revenue', 'unknown_column_1', 'unknown_column_2']
        
        mapping_result = ColumnMapper.detect_mapping(columns)
        
        # Check that unmapped columns are reported
        self.assertIn('unmapped_columns', mapping_result)
        self.assertTrue(len(mapping_result['unmapped_columns']) > 0)


class DataValidationTests(TestCase):
    """Test data validation functionality."""
    
    def test_validation_detects_missing_required_columns(self):
        """Test that validation detects missing required columns."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'quantity': [5, 10]
        })
        
        column_mapping = {'mapping': {}}
        validation_result = DataValidator.validate_dataframe(df, 'sales', column_mapping)
        
        self.assertFalse(validation_result['can_import'])
        self.assertIn('missing_required', validation_result['column_errors'])
    
    def test_validation_detects_invalid_dates(self):
        """Test that validation detects invalid dates."""
        df = pd.DataFrame({
            'date': ['2024-01-01', 'invalid_date', '2024-01-03'],
            'revenue': [100.50, 200.75, 150.25]
        })
        
        column_mapping = {'mapping': {'date': {'detected_column': 'date'}, 'revenue': {'detected_column': 'revenue'}}}
        validation_result = DataValidator.validate_dataframe(df, 'sales', column_mapping)
        
        self.assertGreater(validation_result['warning_count'], 0)
    
    def test_validation_detects_negative_revenue(self):
        """Test that validation detects negative revenue values."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'revenue': [100.50, -50.00, 150.25]
        })
        
        column_mapping = {'mapping': {'date': {'detected_column': 'date'}, 'revenue': {'detected_column': 'revenue'}}}
        validation_result = DataValidator.validate_dataframe(df, 'sales', column_mapping)
        
        self.assertGreater(validation_result['warning_count'], 0)
    
    def test_validation_does_not_fabricate_data(self):
        """Test that validation does not fabricate missing data."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'revenue': [100.50, 200.75]
        })
        
        column_mapping = {'mapping': {'date': {'detected_column': 'date'}, 'revenue': {'detected_column': 'revenue'}}}
        validation_result = DataValidator.validate_dataframe(df, 'sales', column_mapping)
        
        # Check that row counts match original
        self.assertEqual(validation_result['total_rows'], len(df))
        self.assertEqual(validation_result['valid_rows'] + validation_result['invalid_rows'], len(df))


class DataCleaningTests(TestCase):
    """Test data cleaning functionality."""
    
    def test_cleaning_trims_whitespace(self):
        """Test that cleaning trims whitespace from strings."""
        df = pd.DataFrame({
            'name': ['  John Doe  ', '  Jane Smith  ', 'Bob Johnson']
        })
        
        column_mapping = {'mapping': {}}
        df_cleaned, summary = DataCleaner.clean_dataframe(df, 'customers', column_mapping)
        
        self.assertIn('trim_whitespace', summary['operations_performed'])
        self.assertEqual(df_cleaned['name'].iloc[0], 'John Doe')
    
    def test_cleaning_standardizes_nulls(self):
        """Test that cleaning standardizes null representations."""
        df = pd.DataFrame({
            'email': ['test@example.com', 'NA', 'N/A', None]
        })
        
        column_mapping = {'mapping': {}}
        df_cleaned, summary = DataCleaner.clean_dataframe(df, 'customers', column_mapping)
        
        self.assertIn('standardize_nulls', summary['operations_performed'])
    
    def test_cleaning_parses_dates(self):
        """Test that cleaning parses date columns."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        column_mapping = {'mapping': {'date': {'detected_column': 'date'}}}
        df_cleaned, summary = DataCleaner.clean_dataframe(df, 'sales', column_mapping)
        
        self.assertIn('parse_dates', summary['operations_performed'])
    
    def test_cleaning_removes_exact_duplicates(self):
        """Test that cleaning removes exact duplicate rows when appropriate."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'revenue': [100.50, 100.50, 200.75]
        })
        
        column_mapping = {'mapping': {}}
        df_cleaned, summary = DataCleaner.clean_dataframe(df, 'sales', column_mapping)
        
        # Sales should have duplicates removed
        self.assertIn('remove_exact_duplicates', summary['operations_performed'])
        self.assertLess(len(df_cleaned), len(df))


class DatasetModelTests(TestCase):
    """Test Dataset model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        self.business = Business.objects.create(owner=self.user, name='Test Business')
    
    def test_dataset_creation(self):
        """Test that dataset can be created."""
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        self.assertEqual(dataset.name, 'Test Dataset')
        self.assertEqual(dataset.dataset_type, 'sales')
        self.assertEqual(dataset.status, 'pending')
    
    def test_dataset_ownership(self):
        """Test that dataset is properly associated with business."""
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        self.assertEqual(dataset.business, self.business)
    
    def test_dataset_string_representation(self):
        """Test dataset string representation."""
        dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
        
        expected = f"Test Dataset ({self.business.name})"
        self.assertEqual(str(dataset), expected)


class DataImportModelTests(TestCase):
    """Test DataImport model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        self.business = Business.objects.create(owner=self.user, name='Test Business')
        self.dataset = Dataset.objects.create(
            business=self.business,
            name='Test Dataset',
            dataset_type='sales'
        )
    
    def test_dataimport_creation(self):
        """Test that data import can be created."""
        csv_content = b"date,revenue\n2024-01-01,100.50"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        
        data_import = DataImport.objects.create(
            dataset=self.dataset,
            uploaded_file=csv_file,
            original_filename='test.csv',
            file_type='csv',
            file_size=len(csv_content)
        )
        
        self.assertEqual(data_import.original_filename, 'test.csv')
        self.assertEqual(data_import.file_type, 'csv')
        self.assertEqual(data_import.import_status, 'pending')
    
    def test_dataimport_ownership(self):
        """Test that data import is properly associated with dataset."""
        csv_content = b"date,revenue\n2024-01-01,100.50"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        
        data_import = DataImport.objects.create(
            dataset=self.dataset,
            uploaded_file=csv_file,
            original_filename='test.csv',
            file_type='csv',
            file_size=len(csv_content)
        )
        
        self.assertEqual(data_import.dataset, self.dataset)


class CanonicalDataModelTests(TestCase):
    """Test canonical business data models."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        self.business = Business.objects.create(owner=self.user, name='Test Business')
    
    def test_customer_creation(self):
        """Test that customer can be created."""
        customer = Customer.objects.create(
            business=self.business,
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        
        self.assertEqual(customer.customer_id, 'CUST001')
        self.assertEqual(customer.business, self.business)
    
    def test_product_creation(self):
        """Test that product can be created."""
        product = Product.objects.create(
            business=self.business,
            product_id='PROD001',
            name='Test Product',
            sku='SKU001',
            category='Electronics'
        )
        
        self.assertEqual(product.product_id, 'PROD001')
        self.assertEqual(product.business, self.business)
    
    def test_sale_creation(self):
        """Test that sale can be created."""
        customer = Customer.objects.create(
            business=self.business,
            customer_id='CUST001',
            name='John Doe'
        )
        product = Product.objects.create(
            business=self.business,
            product_id='PROD001',
            name='Test Product'
        )
        
        sale = Sale.objects.create(
            business=self.business,
            sale_id='SALE001',
            date='2024-01-01',
            revenue=100.50,
            quantity=5,
            customer=customer,
            product=product
        )
        
        self.assertEqual(sale.sale_id, 'SALE001')
        self.assertEqual(sale.business, self.business)
        self.assertEqual(sale.revenue, 100.50)
    
    def test_expense_creation(self):
        """Test that expense can be created."""
        expense = Expense.objects.create(
            business=self.business,
            expense_id='EXP001',
            date='2024-01-01',
            amount=50.00,
            category='Office Supplies'
        )
        
        self.assertEqual(expense.expense_id, 'EXP001')
        self.assertEqual(expense.business, self.business)
        self.assertEqual(expense.amount, 50.00)
    
    def test_unique_constraints(self):
        """Test that unique constraints are enforced."""
        # Create first customer
        Customer.objects.create(
            business=self.business,
            customer_id='CUST001',
            name='John Doe'
        )
        
        # Try to create duplicate customer
        with self.assertRaises(Exception):  # Should raise IntegrityError
            Customer.objects.create(
                business=self.business,
                customer_id='CUST001',
                name='Jane Doe'
            )
