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

# Authentification
JWT_SECRET_KEY=your_secret_key
ADMIN_SEED_USERNAME=admin
ADMIN_SEED_PASSWORD=your_admin_password

# Environnement : "production" | "uat" | "development"
APP_ENV=development

# LDAP (production uniquement)
LDAP_SERVER=ldap://your-ldap-server
LDAP_BASE_DN=your-domain.net
```

### Run

```bash
python src/main.py
```

Access the web interface at: **http://localhost:8080**

Default admin credentials: `admin` / `admin` (configurable via `ADMIN_SEED_*` variables).

## Authentication & Roles

The application requires authentication to access all features.

### Authentication modes

| Environment | Mode | Description |
|---|---|---|
| `production` | LDAP + local | Authenticates against the enterprise LDAP. Users must be pre-created by an admin. Local fallback for admin accounts. |
| `uat` / `development` | Local only | Authentication against the local SQLite database. |

### Roles

| Role | Access |
|---|---|
| **admin** | Full access + user management page (`/admin`) |
| **expert** | Full access including raw data sheet ("Données d'analyse") |
| **normal** | Reports without the raw data sheet |

### API Endpoints

```bash
# Login
POST /api/auth/login
{ "username": "admin", "password": "admin" }
# Returns: { "access_token": "...", "role": "admin", "username": "admin" }

# Current user info
GET /api/auth/me
# Header: Authorization: Bearer <token>

# Generate report by date range
POST /api/report/by-date
{ "start_date": "2025-01-01", "end_date": "2025-01-31" }

# Generate report by stay IDs
POST /api/report/by-sejours
{ "sejour_ids": ["240281460", "249050332"] }

# Admin - List users
GET /api/admin/users

# Admin - Create user
POST /api/admin/users
{ "username": "jdoe", "password": "pass", "role": "expert", "auth_type": "local" }

# Admin - Update role
PUT /api/admin/users/{id}
{ "role": "admin" }

# Admin - Delete user
DELETE /api/admin/users/{id}
```

All `/api/report/*` and `/api/admin/*` endpoints require a `Authorization: Bearer <token>` header.

## Project Structure

```
api-iqss/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── auth.py              # Authentication (JWT, LDAP)
│   ├── auth_db.py           # User database (SQLite)
│   ├── database.py          # Database connections (GAM/ESL)
│   ├── data_processing.py   # Data processing logic
│   ├── excel_generator.py   # Excel report generation
│   ├── generate_files.py    # Report orchestration
│   └── static/
│       ├── index.html       # Main web interface
│       ├── login.html       # Login page
│       └── admin.html       # Admin panel
├── data/db/                  # Specialty mapping matrices
├── k8s/
│   ├── production/           # K8s configs (production)
│   └── uat/                  # K8s configs (UAT)
├── Dockerfile
├── .env
└── requirements.txt
```

## Docker

```bash
docker build -t api-iqss .
docker run --env-file .env -p 8080:8080 api-iqss   
```

## Kubernetes Deployment

The CI/CD pipeline (GitHub Actions) handles build, push to Harbor, and deployment updates automatically on push to `main` (production) or `uat`.

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `HARBOR_USERNAME` | Harbor registry username |
| `HARBOR_PASSWORD` | Harbor registry password |
| `GAM_USER` | Oracle database user |
| `GAM_PASSWORD` | Oracle database password |
| `ESL_USER` | SQL Server database user |
| `ESL_PASSWORD` | SQL Server database password |
| `JWT_SECRET_KEY` | Secret key for JWT signing |
| `ADMIN_SEED_PASSWORD` | Initial admin password |
| `LDAP_SERVER` | LDAP server URL (production only) |
| `LDAP_BASE_DN` | LDAP base domain (production only) |
