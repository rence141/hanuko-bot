# 🗄️ Local PostgreSQL Setup Guide

## Option 1: XAMPP PostgreSQL (if available)
Since you're using XAMPP, check if PostgreSQL is included in your XAMPP installation.

## Option 2: Install PostgreSQL separately

### Windows Installation:
1. **Download PostgreSQL:**
   - Go to https://www.postgresql.org/download/windows/
   - Download the installer for Windows

2. **Install PostgreSQL:**
   - Run the installer
   - Choose installation directory
   - Set password for postgres user
   - Keep default port (5432)
   - Complete installation

3. **Create Database:**
   ```bash
   # Open pgAdmin (comes with PostgreSQL)
   # Or use command line:
   psql -U postgres
   CREATE DATABASE hanuko_bot;
   \q
   ```

4. **Set Environment Variables:**
   ```bash
   # In your system environment variables or .env file:
   DB_HOST=localhost
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   DB_NAME=hanuko_bot
   DB_PORT=5432
   ```

## Option 3: Docker PostgreSQL (Recommended for development)

1. **Install Docker Desktop**

2. **Run PostgreSQL container:**
   ```bash
   docker run --name hanuko-postgres \
     -e POSTGRES_PASSWORD=your_password \
     -e POSTGRES_DB=hanuko_bot \
     -p 5432:5432 \
     -d postgres:15
   ```

3. **Set environment variables:**
   ```
   DB_HOST=localhost
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_NAME=hanuko_bot
   DB_PORT=5432
   ```

## Testing Database Connection

Run the setup script to test:
```bash
python setup_database.py
```

## For Render Deployment

Use Render's PostgreSQL service instead of local setup for production.
