# ARGO ETL Pipeline - Project Structure

## Folder Organization

```
data_pipeline/
├── main.py                  # Run the pipeline
├── requirements.txt         # Install dependencies
├── config/
│   ├── config.py           # Settings
│   └── .env               # Database credentials
├── src/
│   ├── core/
│   │   └── pipeline.py    # Main pipeline logic
│   ├── database/
│   │   ├── models.py      # Database tables
│   │   └── database.py    # Database operations
│   ├── downloaders/
│   │   └── ftp_downloader.py  # Download files from FTP
│   ├── parsers/
│   │   └── netcdf_parser.py   # Parse NetCDF files
│   └── utils/
│       └── utils.py       # Logging setup
├── docs/                  # Documentation
└── tests/                 # Tests (empty for now)
```

## What Each Part Does

- **main.py** - Start here to run the pipeline
- **config/** - Database settings and credentials
- **core/** - Controls the entire pipeline process
- **database/** - Handles saving data to Supabase
- **downloaders/** - Gets files from ocean data server
- **parsers/** - Reads ocean measurement files
- **utils/** - Helper functions like logging

## How to Use

### 1. **Set up Virtual Environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### 3. **Set up database credentials in `config/.env`**
Add your Supabase credentials to the `.env` file.

### 4. **Run the pipeline:**
```bash
python main.py
```

### 5. **Deactivate virtual environment when done:**
```bash
deactivate
```

## Adding New Features

- New data sources → Add to `src/downloaders/`
- New file formats → Add to `src/parsers/`
- New database tables → Update `src/database/models.py`

That's it! The code is organized so each folder has one job, making it easy to find and modify
