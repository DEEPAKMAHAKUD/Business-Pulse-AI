"""
Views for data ingestion.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from businesses.models import Business
from .models import Dataset, DataImport
from .forms import DatasetForm, DataImportForm
from .services.readers import FileReader
from .services.profiler import DataProfiler
from .services.column_mapper import ColumnMapper
from .services.validators import DataValidator


@login_required
def upload_data(request):
    """Main upload page - select business and start upload process."""
    businesses = Business.objects.filter(owner=request.user)
    
    if not businesses:
        messages.warning(request, 'You need to create a business first before uploading data.')
        return redirect('business_create')
    
    if request.method == 'POST':
        business_id = request.POST.get('business')
        if not business_id:
            messages.error(request, 'Please select a business.')
            return render(request, 'data_ingestion/upload_data.html', {'businesses': businesses})
        
        business = get_object_or_404(Business, pk=business_id, owner=request.user)
        
        # Create dataset form
        dataset_form = DatasetForm(request.POST)
        if dataset_form.is_valid():
            dataset = dataset_form.save(commit=False)
            dataset.business = business
            dataset.status = 'pending'
            dataset.save()
            
            return redirect('upload_file', dataset_id=dataset.id)
        else:
            messages.error(request, 'Please correct the errors in the form.')
    
    else:
        dataset_form = DatasetForm()
    
    return render(request, 'data_ingestion/upload_data.html', {
        'businesses': businesses,
        'dataset_form': dataset_form
    })


@login_required
def upload_file(request, dataset_id):
    """Handle file upload for a specific dataset."""
    dataset = get_object_or_404(Dataset, pk=dataset_id, business__owner=request.user)
    
    if request.method == 'POST':
        import_form = DataImportForm(request.POST, request.FILES)
        
        if import_form.is_valid():
            uploaded_file = request.FILES['uploaded_file']
            
            # Determine file type
            file_name = uploaded_file.name.lower()
            if file_name.endswith('.csv'):
                file_type = 'csv'
            elif file_name.endswith('.xlsx'):
                file_type = 'xlsx'
            elif file_name.endswith('.xls'):
                file_type = 'xls'
            else:
                messages.error(request, 'Invalid file type.')
                return render(request, 'data_ingestion/upload_file.html', {
                    'dataset': dataset,
                    'import_form': import_form
                })
            
            # Create DataImport record
            data_import = DataImport.objects.create(
                dataset=dataset,
                uploaded_file=uploaded_file,
                original_filename=uploaded_file.name,
                file_type=file_type,
                file_size=uploaded_file.size,
                import_status='processing',
                started_at=timezone.now()
            )
            
            # Process the file
            try:
                # Read file
                file_content = uploaded_file.read()
                df, error = FileReader.read_file(file_content, file_type)
                
                if error:
                    data_import.import_status = 'failed'
                    data_import.validation_summary = {'error': error}
                    data_import.completed_at = timezone.now()
                    data_import.save()
                    
                    messages.error(request, f'Error reading file: {error}')
                    return render(request, 'data_ingestion/upload_file.html', {
                        'dataset': dataset,
                        'import_form': import_form
                    })
                
                # Profile the data
                profile = DataProfiler.profile_dataframe(df)
                
                # Detect dataset type if not specified
                if dataset.dataset_type == 'unknown':
                    detected_type = DataProfiler.detect_dataset_type(profile)
                    dataset.dataset_type = detected_type
                    dataset.save()
                
                # Update dataset with profiling info
                dataset.row_count = profile['row_count']
                dataset.column_count = profile['column_count']
                dataset.status = 'processing'
                dataset.save()
                
                # Update import record
                data_import.rows_processed = profile['row_count']
                data_import.save()
                
                # Detect column mapping
                column_mapping = ColumnMapper.detect_mapping(profile['columns'])
                
                # Validate data
                validation_result = DataValidator.validate_dataframe(
                    df, dataset.dataset_type, column_mapping
                )
                
                # Update import with validation results
                data_import.rows_accepted = validation_result['valid_rows']
                data_import.rows_rejected = validation_result['invalid_rows']
                data_import.error_count = validation_result['error_count']
                
                # Include profile and column mapping in validation summary
                validation_result['profile'] = profile
                validation_result['column_mapping'] = column_mapping
                
                data_import.validation_summary = validation_result
                data_import.import_status = 'completed' if validation_result['can_import'] else 'validation_failed'
                data_import.completed_at = timezone.now()
                data_import.save()
                
                # Update dataset status
                dataset.status = 'completed' if validation_result['can_import'] else 'validation_failed'
                dataset.validation_status = validation_result['validation_summary']
                dataset.save()
                
                # Redirect to results page
                return redirect('import_result', import_id=data_import.id)
                
            except Exception as e:
                data_import.import_status = 'failed'
                data_import.validation_summary = {'error': str(e)}
                data_import.completed_at = timezone.now()
                data_import.save()
                
                messages.error(request, f'Error processing file: {str(e)}')
                return render(request, 'data_ingestion/upload_file.html', {
                    'dataset': dataset,
                    'import_form': import_form
                })
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        import_form = DataImportForm()
    
    return render(request, 'data_ingestion/upload_file.html', {
        'dataset': dataset,
        'import_form': import_form
    })


@login_required
def import_result(request, import_id):
    """Display import results and validation summary."""
    data_import = get_object_or_404(
        DataImport, 
        pk=import_id, 
        dataset__business__owner=request.user
    )
    
    validation_summary = data_import.validation_summary or {}
    
    # Get column mapping information
    profile = validation_summary.get('profile', {})
    column_mapping = validation_summary.get('column_mapping', {})
    
    return render(request, 'data_ingestion/import_result.html', {
        'data_import': data_import,
        'dataset': data_import.dataset,
        'validation_summary': validation_summary,
        'column_mapping': column_mapping,
        'profile': profile
    })


@login_required
def dataset_list(request):
    """List all datasets for the user's businesses."""
    businesses = Business.objects.filter(owner=request.user)
    datasets = Dataset.objects.filter(business__in=businesses).select_related('business').order_by('-created_at')
    
    return render(request, 'data_ingestion/dataset_list.html', {
        'datasets': datasets,
        'businesses': businesses
    })


@login_required
def dataset_detail(request, dataset_id):
    """Show details of a specific dataset."""
    dataset = get_object_or_404(Dataset, pk=dataset_id, business__owner=request.user)
    imports = dataset.imports.all().order_by('-created_at')
    
    return render(request, 'data_ingestion/dataset_detail.html', {
        'dataset': dataset,
        'imports': imports
    })


@login_required
def dataset_delete(request, dataset_id):
    """Delete a dataset and all its imports."""
    dataset = get_object_or_404(Dataset, pk=dataset_id, business__owner=request.user)
    
    if request.method == 'POST':
        dataset.delete()
        messages.success(request, 'Dataset deleted successfully.')
        return redirect('dataset_list')
    
    return render(request, 'data_ingestion/dataset_confirm_delete.html', {
        'dataset': dataset
    })
