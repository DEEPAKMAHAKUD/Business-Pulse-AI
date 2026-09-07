# BusinessPulse AI

## Overview

BusinessPulse AI is an intelligent business analytics platform for small and medium-sized businesses that turns business data into decisions.

## Technology Stack

* Python 3.11+
* Django 5.2.17
* Django Templates
* PostgreSQL (production) / SQLite (development)
* Pandas (data processing)
* OpenPyXL (Excel file support)
* HTML5, CSS3, Vanilla JavaScript
* Bootstrap 5

## Current Capabilities (Phase 2)

### Data Ingestion
- **File Upload**: Support for CSV and Excel files (XLSX, XLS)
- **Data Profiling**: Automatic analysis of row/column counts, data types, missing values, duplicates
- **Column Detection**: Intelligent recognition of common field names (revenue, customer, product, date, quantity, etc.)
- **Data Validation**: Type-specific validation rules for sales, customers, products, expenses, and inventory data
- **Data Cleaning**: Safe, deterministic transformations (whitespace trimming, null standardization, date parsing, numeric conversion)
- **Validation Results**: Comprehensive reporting of data quality issues with actionable feedback

### Business Management
- **Business CRUD**: Create, read, update, delete business entities
- **User Authentication**: Registration, login, logout with unique email validation
- **Ownership Control**: Users can only access their own business data

### Canonical Data Models
- **Customer**: Customer records with ID, name, email, phone, address
- **Product**: Product catalog with ID, name, SKU, category, price
- **Sale**: Sales transactions with ID, date, revenue, quantity, customer, product relationships
- **Expense**: Expense records with ID, date, amount, category, description
- **InventoryRecord**: Inventory levels with product, quantity, date tracking

### User Interface
- **Professional Dashboard**: Bootstrap 5 responsive interface
- **Upload Workflow**: Step-by-step data upload process with validation feedback
- **Dataset Management**: View, manage, and delete datasets
- **Import History**: Track all file uploads and their results
- **Navigation**: Organized menu structure with placeholders for future features

## Supported File Formats

- **CSV**: Comma-separated values files
- **XLSX**: Modern Excel format
- **XLS**: Legacy Excel format

### File Requirements
- Maximum file size: 10MB
- First row must contain column headers
- Properly formatted data (dates, numbers, etc.)
- No corrupt or malformed files

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file from the `.env.example` and fill in the required environment variables.
6. Apply migrations: `python manage.py migrate`
7. Create a superuser: `python manage.py createsuperuser`
8. Run the development server: `python manage.py runserver`

## Usage

1. Visit `http://127.0.0.1:8000/` to access the application
2. Register a new account or login
3. Create a business entity
4. Navigate to "Upload Data" to upload your business files
5. Review the validation results and data profiling information
6. Manage your datasets from the "Datasets" page

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python manage.py test

# Run data ingestion tests only
python manage.py test data_ingestion

# Run with verbose output
python manage.py test data_ingestion -v 2
```

Test coverage includes:
- Authentication and authorization
- File upload (CSV, Excel, invalid types, empty files, size limits)
- Data profiling
- Column mapping and detection
- Data validation
- Data cleaning
- Model functionality
- Ownership isolation

## Architecture

### Phase 1 (Foundation)
- Django project structure
- User authentication and authorization
- Business entity management
- Basic dashboard

### Phase 2 (Data Ingestion) - Current
- Data ingestion architecture
- File upload and processing
- Data profiling and validation
- Column detection and mapping
- Canonical business data models
- Comprehensive testing

### Phase 3+ (Planned)
- Analytics engine
- ML pipelines
- Forecasting
- Anomaly detection
- AI assistant
- Advanced reporting

## Data Security

- Authentication required for all operations
- CSRF protection on all forms
- Server-side ownership verification
- File upload size limits
- Extension and content type validation
- No arbitrary file execution
- No user-controlled filesystem paths

## Development Status

**Current Phase**: Phase 2 - Data Ingestion & Canonical Data Model

**Completed Features**:
- ✅ User authentication and business management
- ✅ File upload system (CSV, Excel)
- ✅ Data profiling and validation
- ✅ Column detection and mapping
- ✅ Canonical data models
- ✅ Comprehensive testing
- ✅ Professional UI

**Coming Soon**:
- ⏳ Analytics engine
- ⏳ ML pipelines
- ⏳ Forecasting
- ⏳ Anomaly detection
- ⏳ AI assistant
- ⏳ Advanced reporting

## License

This project is proprietary and confidential.

## Contact

[Deepak Mahakud]
