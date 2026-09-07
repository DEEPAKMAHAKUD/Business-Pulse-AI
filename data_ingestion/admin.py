from django.contrib import admin
from .models import Dataset, DataImport, Customer, Product, Sale, Expense, InventoryRecord


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'dataset_type', 'status', 'row_count', 'column_count', 'created_at']
    list_filter = ['dataset_type', 'status', 'created_at']
    search_fields = ['name', 'business__name']


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'original_filename', 'file_type', 'import_status', 'rows_processed', 'created_at']
    list_filter = ['import_status', 'file_type', 'created_at']
    search_fields = ['original_filename', 'dataset__name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['business', 'customer_id', 'name', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer_id', 'name', 'email']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['business', 'product_id', 'name', 'sku', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['product_id', 'name', 'sku']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['business', 'sale_id', 'date', 'revenue', 'quantity', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['sale_id']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['business', 'expense_id', 'date', 'amount', 'category', 'created_at']
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['expense_id', 'description']


@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ['business', 'product', 'quantity', 'recorded_at', 'created_at']
    list_filter = ['recorded_at', 'created_at']
    search_fields = ['product__name']
