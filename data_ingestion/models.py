from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from decimal import Decimal


class Dataset(models.Model):
    """Represents a logical dataset belonging to a business."""
    
    DATASET_TYPES = [
        ('sales', 'Sales'),
        ('customers', 'Customers'),
        ('products', 'Products'),
        ('expenses', 'Expenses'),
        ('inventory', 'Inventory'),
        ('transactions', 'Transactions'),
        ('unknown', 'Unknown'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('validation_failed', 'Validation Failed'),
    ]
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255, blank=True)
    dataset_type = models.CharField(max_length=20, choices=DATASET_TYPES, default='unknown')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    validation_status = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'dataset_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.business.name})"


class DataImport(models.Model):
    """Represents an individual file upload/import operation."""
    
    IMPORT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('validation_failed', 'Validation Failed'),
    ]
    
    FILE_TYPES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('xls', 'Excel (Legacy)'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='imports')
    uploaded_file = models.FileField(
        upload_to='data_uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])]
    )
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    import_status = models.CharField(max_length=20, choices=IMPORT_STATUS, default='pending')
    rows_processed = models.IntegerField(default=0)
    rows_accepted = models.IntegerField(default=0)
    rows_rejected = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    validation_summary = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset', 'import_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.import_status}"


class Customer(models.Model):
    """Canonical customer data model."""
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='customers')
    customer_id = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['business', 'customer_id']
        indexes = [
            models.Index(fields=['business', 'customer_id']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.customer_id} - {self.name or 'Unnamed'}"


class Product(models.Model):
    """Canonical product data model."""
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='products')
    product_id = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['business', 'product_id']
        indexes = [
            models.Index(fields=['business', 'product_id']),
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.product_id} - {self.name}"


class Sale(models.Model):
    """Canonical sales/transaction data model."""
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='sales')
    sale_id = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)
    revenue = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField(default=1)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['business', 'sale_id']
        indexes = [
            models.Index(fields=['business', 'date']),
            models.Index(fields=['business', 'sale_id']),
        ]
    
    def __str__(self):
        return f"{self.sale_id} - {self.revenue}"


class Expense(models.Model):
    """Canonical expense data model."""
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='expenses')
    expense_id = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['business', 'expense_id']
        indexes = [
            models.Index(fields=['business', 'date']),
            models.Index(fields=['business', 'expense_id']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.expense_id} - {self.amount}"


class InventoryRecord(models.Model):
    """Canonical inventory record data model."""
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='inventory_records')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_records')
    quantity = models.IntegerField()
    recorded_at = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['business', 'product', 'recorded_at']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} on {self.recorded_at}"
