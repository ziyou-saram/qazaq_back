# Deployment Workflow

## Quick Deploy to Railway (Recommended for Start)

### Prerequisites
- GitHub account
- Railway account (free tier available)
- AWS S3 bucket configured

### Steps

1. **Push code to GitHub:**
   ```bash
   cd /Users/alikhanzhumabayev/Downloads/qazaq_full_project/backend
   git init
   git add .
   git commit -m "Initial backend commit"
   git remote add origin your-github-repo-url
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python and deploy

3. **Add PostgreSQL:**
   - In your Railway project, click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable

4. **Configure Environment Variables:**
   Go to your service settings and add:
   ```
   SECRET_KEY=generate-a-secure-random-string-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   BACKEND_CORS_ORIGINS=["https://your-frontend-url.com"]
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   AWS_S3_BUCKET=qazaq
   AWS_REGION=eu-north-1
   PROJECT_NAME=Qazaq Platform
   VERSION=1.0.0
   ```

5. **Initialize Database:**
   - Railway will run `alembic upgrade head` automatically (via Procfile)
   - To create admin user, use Railway's shell or run locally against production DB

6. **Get your URL:**
   - Railway provides a URL like `https://your-app.up.railway.app`
   - Use this URL for your frontend API calls

---

## Docker Deployment (VPS)

### Prerequisites
- VPS with Docker installed (Ubuntu 22.04 recommended)
- Domain name (optional but recommended)

### Steps

1. **On your VPS:**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo apt install docker-compose -y
   ```

2. **Clone and configure:**
   ```bash
   git clone your-repo
   cd backend
   
   # Create .env file
   cp .env.example .env
   nano .env  # Edit with production values
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database:**
   ```bash
   docker-compose exec backend python -c "from app.db.init_db import init_db; init_db()"
   ```

5. **Setup Nginx (optional, for custom domain):**
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## Post-Deployment Checklist

- [ ] Verify API is accessible: `curl https://your-api-url/docs`
- [ ] Test authentication endpoints
- [ ] Create admin user
- [ ] Test S3 file upload
- [ ] Update frontend API URL
- [ ] Setup monitoring (optional: Sentry, LogRocket)
- [ ] Setup backups for PostgreSQL
- [ ] Configure CDN for S3 (optional: CloudFront)

---

## Monitoring & Maintenance

### Health Check Endpoint
Add to `app/main.py`:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
```

### Logs
- **Railway:** Built-in logs viewer
- **Docker:** `docker-compose logs -f backend`

### Database Backups
```bash
# Railway: Use Railway's backup feature
# Docker: 
docker-compose exec db pg_dump -U qazaq qazaq > backup.sql
```
