# API-IQSS - Lettres de Liaison Reporting

Automated reporting system for hospital discharge letters (Lettres de Liaison) indicators at Hôpital Foch.

## Overview

This API generates Excel reports on validation and diffusion metrics for discharge letters, following French healthcare regulations (Décret n° 2016-995).

**Key metrics tracked:**
- Validation rate of discharge letters
- Same-day validation rate (J0)
- Average validation delay
- Diffusion statistics

## Quick Start

### Prerequisites
- Python 3.12+
- Access to GAM (Oracle) and ESL (SQL Server) databases

### Installation

```bash
# Clone and install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### Configuration

Create a `.env` file:

```env
# GAM (Oracle)
GAM_USER=your_user
GAM_PASSWORD=your_password

# ESL (SQL Server)
ESL_USER=your_user
ESL_PASSWORD=your_password
```

### Run

```bash
python src/main.py
```

Access the web interface at: **http://localhost:8080**

## Usage

### Web Interface
1. Select report type: **By Period** or **By Stays**
2. Enter date range or stay IDs
3. Click "Generate Report"
4. Download Excel file

### API Endpoints

```bash
# Generate report by date range
POST /api/report/by-date
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}

# Generate report by stay IDs
POST /api/report/by-sejours
{
  "sejour_ids": ["240281460", "249050332"]
}
```

## Project Structure

```
api-iqss/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connections (GAM/ESL)
│   ├── data_processing.py   # Data processing logic
│   ├── excel_generator.py   # Excel report generation
│   ├── generate_files.py    # Report orchestration
│   └── static/index.html    # Web interface
├── data/db/                  # Specialty mapping matrix
├── Dockerfile
└── requirements.txt
```

## Docker

```bash
docker build -t api-iqss .
docker run --env-file .env -p 8080:8080 api-iqss   
```

## Deploying in production

# Export the image locally:

```bash
docker save api-iqss:latest -o api-iqss.tar
```
# Transfer the tar file to your production server (via scp, sftp, etc.)

# Load and run on production:
```bash
docker load -i api-iqss.tar
docker run -d --env-file .env -p 8080:8080 --restart unless-stopped api-iqss:latest
```