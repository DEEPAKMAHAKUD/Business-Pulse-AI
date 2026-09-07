"""
Forms for data ingestion.
"""
from django import forms
from django.core.validators import FileExtensionValidator
from .models import Dataset, DataImport


class DatasetForm(forms.ModelForm):
    """Form for creating a dataset."""
    
    class Meta:
        model = Dataset
        fields = ['name', 'dataset_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter dataset name'}),
            'dataset_type': forms.Select(attrs={'class': 'form-select'}),
        }


class DataImportForm(forms.ModelForm):
    """Form for uploading a data file."""
    
    class Meta:
        model = DataImport
        fields = ['uploaded_file']
        widgets = {
            'uploaded_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.xls'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['uploaded_file'].required = True
        self.fields['uploaded_file'].help_text = 'Supported formats: CSV, XLSX, XLS (Max 10MB)'
    
    def clean_uploaded_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data.get('uploaded_file')
        
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size exceeds maximum allowed size of 10MB')
            
            # Check file extension
            valid_extensions = ['.csv', '.xlsx', '.xls']
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError('Invalid file type. Only CSV and Excel files are allowed.')
            
            # Check if file is empty
            if file.size == 0:
                raise forms.ValidationError('File is empty')
        
        return file


class DatasetTypeDetectionForm(forms.Form):
    """Form for confirming detected dataset type."""
    
    dataset_type = forms.ChoiceField(
        choices=Dataset.DATASET_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    def __init__(self, *args, detected_type='unknown', **kwargs):
        super().__init__(*args, **kwargs)
        if detected_type:
            self.fields['dataset_type'].initial = detected_type
