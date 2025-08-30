# Supabase Configuration Guide

## Steps to Configure Supabase for ARGO ETL Pipeline

### 1. Get Your Supabase Credentials

1. **Go to your Supabase Dashboard**: https://app.supabase.com/
2. **Select your project** or create a new one
3. **Go to Settings > API** to find your credentials:
   - **Project URL**: `https://your-project-ref.supabase.co`
   - **Anon Public Key**: Your public API key
   - **Service Role Key**: Your service role key (more permissions)

### 2. Get Your Database Connection String

1. **In Supabase Dashboard, go to Settings > Database**
2. **Find "Connection string" section**
3. **Copy the connection string** which looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
4. **Replace `[YOUR-PASSWORD]` with your actual database password**

### 3. Update Your .env File

Replace the placeholder values in your `.env` file:

```env
# Supabase Database Configuration
SUPABASE_URL=https://your-actual-project-ref.supabase.co
SUPABASE_KEY=your-actual-anon-public-key-here
SUPABASE_SERVICE_ROLE_KEY=your-actual-service-role-key-here

# Database connection
DATABASE_URL=postgresql://postgres:your-actual-password@db.your-actual-project-ref.supabase.co:5432/postgres
```

### 4. Install Additional Dependencies

Run this command to install the Supabase client:

```bash
pip install supabase
```

Or install all updated requirements:

```bash
pip install -r requirements.txt
```

### 5. Test Your Connection

You can test your Supabase connection by running:

```python
from supabase_client import SupabaseClient

client = SupabaseClient()
if client.test_connection():
    print("✅ Supabase connection successful!")
else:
    print("❌ Supabase connection failed")
```

### 6. Database Schema Setup

The pipeline will automatically create the required tables:
- `argo_floats` - Float metadata
- `argo_profiles` - Profile measurements

### 7. Security Notes

- **Never commit your `.env` file** to version control
- **Use Service Role Key** for backend operations (more permissions)
- **Use Anon Key** for frontend/client operations (limited permissions)
- **Keep your database password secure**

### Example .env File Structure

```env
# Replace with your actual Supabase values
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=API_KEY
SUPABASE_SERVICE_ROLE_KEY=ROLE_KEY

# Replace with your actual database connection string
DATABASE_URL=postgresql://postgres:your_secure_password@db.abcdefghijklmnop.supabase.co:5432/postgres

# FTP and Pipeline settings (these can remain as is)
FTP_HOST=ftp.ifremer.fr
FTP_PATH=/ifremer/argo/dac/incois/
MAX_FILES=5
LOG_LEVEL=INFO
```

### Troubleshooting

**Connection Issues:**
- Verify your credentials are correct
- Check that your IP is allowed (Supabase may have IP restrictions)
- Ensure your database password is correct

**Permission Issues:**
- Use Service Role Key for backend operations
- Check your RLS (Row Level Security) policies in Supabase

**Installation Issues:**
- Make sure you're in the correct virtual environment
- Try upgrading pip: `pip install --upgrade pip`
