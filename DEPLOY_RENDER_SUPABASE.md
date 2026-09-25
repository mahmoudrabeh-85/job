# Deploy to Render + Supabase (Free, No Card for Render)

## Overview
- **Render**: Hosts the FastAPI backend (free tier, sleeps after 15min inactivity)
- **Supabase**: Hosts PostgreSQL database (free tier, 500MB, pauses after 1 week inactivity)
- **GitHub**: Source code repository (already pushed to `mahmoudrabeh-85/job`)

---

## Step 1: Create Supabase Project (2 minutes)

1. Go to **`supabase.com`** → Sign up with GitHub
2. Click **"New Project"**
   - Name: `job-hunt-db`
   - Database Password: **save this!** (you'll need it for DATABASE_URL)
   - Region: **EU West (Ireland)** or closest to you
   - Pricing Plan: **Free**
3. Wait ~2 minutes for provisioning

### Get Connection String
1. In Supabase Dashboard → **Settings** → **Database**
2. Scroll to **Connection string** → **URI** tab
3. Copy the URI (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with the password you set

### Run Schema
1. Go to **SQL Editor** in Supabase Dashboard
2. Copy contents of `supabase_schema.sql` from this repo
3. Paste and click **Run**

---

## Step 2: Deploy to Render (3 minutes)

### Option A: Using render.yaml (Recommended)
1. Go to **`dashboard.render.com`** → Sign up with GitHub
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repo: `mahmoudrabeh-85/job`
4. Render will detect `render.yaml` and show:
   - **Web Service**: `job-hunt-api` (free)
   - **PostgreSQL**: `job-hunt-db` (free) — **Skip this, we use Supabase**
5. Click **Apply** → Render creates the web service

### Option B: Manual Web Service
1. **New +** → **Web Service**
2. Connect `mahmoudrabeh-85/job`
3. Settings:
   - **Name**: `job-hunt-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. **Environment Variables** (add these):
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | Your Supabase connection string from Step 1 |
   | `CORS_ORIGINS` | `https://job-hunt-api.onrender.com,http://localhost:8767` |
   | `PORT` | `10000` |
   | `HOST` | `0.0.0.0` |
   | `PYTHON_VERSION` | `3.11.0` |
   | `ADZUNA_APP_ID` | *(optional)* |
   | `ADZUNA_APP_KEY` | *(optional)* |
5. Click **Create Web Service**

---

## Step 3: Update CORS (after first deploy)

1. Wait for deploy to finish (2-3 minutes)
2. Get your Render URL: `https://job-hunt-api.onrender.com` (or whatever name you chose)
3. Go to Render Dashboard → Your Web Service → **Environment**
3. Update `CORS_ORIGINS`:
   ```
   https://job-hunt-api.onrender.com,http://localhost:8767
   ```
4. Save → Render will auto-redeploy

---

## Step 4: Test

Visit your live URL:
- **Frontend**: `https://job-hunt-api.onrender.com/`
- **API Docs**: `https://job-hunt-api.onrender.com/api/docs`
- **Health Check**: `https://job-hunt-api.onrender.com/api/v1/health`

Expected health response:
```json
{
  "status": "ok",
  "db_exists": true,
  "db_backend": "postgresql",
  "version": "2.0.0"
}
```

---

## Important Notes

### Render Free Tier Limits
- ✅ 750 hours/month (enough for 24/7 if always active)
- ⚠️ **Spins down after 15 minutes of inactivity** — first request after sleep takes ~30-60 seconds
- ⚠️ 5GB bandwidth/month (plenty for this app)
- ⚠️ No persistent disk — **SQLite won't work** (that's why we use Supabase)

### Supabase Free Tier Limits
- ✅ 500MB database
- ✅ 50,000 monthly active users
- ⚠️ **Pauses after 1 week of inactivity** — wakes on first request
- ✅ Unlimited API requests

### Keeping Both Awake (Optional)
If you want to prevent spin-down:
- Set up a cron job (GitHub Actions, cron-job.org, or UptimeRobot) to ping `/api/v1/health` every 10 minutes
- Example GitHub Action (`.github/workflows/keep-alive.yml`):
  ```yaml
  name: Keep Alive
  on:
    schedule:
      - cron: '*/10 * * * *'  # Every 10 minutes
  jobs:
    ping:
      runs-on: ubuntu-latest
      steps:
        - run: curl -s https://job-hunt-api.onrender.com/api/v1/health > /dev/null
  ```

---

## Local Development

```bash
# 1. Clone repo
git clone https://github.com/mahmoudrabeh-85/job.git
cd job

# 2. Create .env (copy from .env.example)
cp .env.example .env
# Edit .env - leave DATABASE_URL empty for SQLite

# 3. Install deps
pip install -r requirements.txt

# 4. Run locally (uses SQLite)
uvicorn app.main:app --reload --port 8767
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `DATABASE_URL` not working | Check password special chars — URL-encode them (`%40` for `@`, etc.) |
| CORS errors | Ensure `CORS_ORIGINS` includes your exact Render URL |
| Jobs not loading | Verify Supabase schema ran successfully (check Table Editor) |
| App spins down too fast | Set up keep-alive ping (see above) |
| Supabase paused | Just visit the app — it auto-wakes |

---

## File Checklist (Already in Repo)

- ✅ `requirements.txt` — Python dependencies
- ✅ `render.yaml` — Render Blueprint config
- ✅ `.env.example` — Environment template
- ✅ `supabase_schema.sql` — Database schema
- ✅ `app/database_pg.py` — PostgreSQL layer
- ✅ `app/database_factory.py` — Auto-switches SQLite/PostgreSQL
- ✅ `app/main.py` — With lifespan handlers
- ✅ Updated routers for dual DB support

---

## Next Steps After Deploy

1. **Add custom domain** (Render Settings → Custom Domains)
2. **Set up monitoring** (UptimeRobot free tier)
3. **Add keep-alive** (GitHub Actions or cron-job.org)
4. **Enable Supabase backups** (Dashboard → Database → Backups)