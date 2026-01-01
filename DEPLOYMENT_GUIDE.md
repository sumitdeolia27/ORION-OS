# 🚀 ORION OS - Deployment Guide

## Deployment Options

There are several ways to deploy ORION OS. Choose the one that best fits your needs:

1. **Vercel (Frontend Only)** - Free, easy, recommended for demo
2. **Vercel + Railway (Full Stack)** - Free tier available, good for production
3. **Docker (Self-Hosted)** - Full control, host anywhere
4. **VPS/Cloud Server** - Complete control, professional deployment

---

## 🌐 Option 1: Vercel (Frontend Only) - EASIEST

### Prerequisites
- GitHub account
- Vercel account (free)

### Steps

#### 1. Prepare Your Code
```bash
# Make sure everything is committed
git init
git add .
git commit -m "Initial commit"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/orion-os.git
git push -u origin main
```

#### 2. Deploy to Vercel

**Via Vercel CLI:**
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# For production
vercel --prod
```

**Via Vercel Dashboard:**
1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: ./
   - **Build Command**: `npm run build`
   - **Output Directory**: .next
5. Add Environment Variables:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
6. Click "Deploy"

#### 3. Limitations
⚠️ **Frontend only** - Backend Python API won't work on Vercel
- AI Chat tab will work (uses frontend API route)
- Command console won't work (needs backend)
- System commands won't work (needs backend)

**Use this for:** Demo, portfolio, UI showcase

---

## 🚂 Option 2: Vercel + Railway (Full Stack) - RECOMMENDED

### Deploy Full Application with Both Frontend and Backend

#### Part A: Deploy Backend to Railway

1. **Sign up at Railway.app**
   - Go to https://railway.app
   - Sign up with GitHub (free $5/month credit)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your ORION-OS repository

3. **Configure Backend Service**

   Create a file: `railway.json`
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "python scripts/api_server.py",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

   Create a file: `Procfile`
   ```
   web: python scripts/api_server.py
   ```

   Create a file: `runtime.txt`
   ```
   python-3.11
   ```

4. **Set Environment Variables in Railway**
   ```
   ORION_DISABLE_TTS=1
   GEMINI_API_KEY=your_api_key_here
   PORT=5000
   ```

5. **Deploy**
   - Railway will auto-deploy
   - Get your backend URL: `https://your-app.railway.app`

#### Part B: Deploy Frontend to Vercel

1. **Deploy to Vercel** (same as Option 1)

2. **Add Environment Variable**
   ```
   GEMINI_API_KEY=your_api_key_here
   BACKEND_API_URL=https://your-app.railway.app
   ```

3. **Update CORS in Backend**

   Edit `scripts/api_server.py`:
   ```python
   from flask_cors import CORS

   app = Flask(__name__)
   CORS(app, origins=["https://your-vercel-app.vercel.app"])
   ```

4. **Redeploy Both Services**

### ✅ Result
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-app.railway.app`
- **Full functionality** - Everything works!

---

## 🐳 Option 3: Docker (Self-Hosted)

### Create Docker Configuration

#### 1. Create `Dockerfile.backend`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY scripts/ ./scripts/
COPY .env.local .env

# Expose port
EXPOSE 5000

# Disable TTS for stability
ENV ORION_DISABLE_TTS=1

# Run server
CMD ["python", "scripts/api_server.py"]
```

#### 2. Create `Dockerfile.frontend`
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install

# Copy application
COPY . .

# Build
RUN pnpm build

# Expose port
EXPOSE 3000

# Run
CMD ["pnpm", "start"]
```

#### 3. Create `docker-compose.yml`
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "5000:5000"
    environment:
      - ORION_DISABLE_TTS=1
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped
    networks:
      - orion-network

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - BACKEND_API_URL=http://backend:5000
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - orion-network

networks:
  orion-network:
    driver: bridge
```

#### 4. Deploy with Docker Compose
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### ✅ Result
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5000`
- **Portable** - Deploy anywhere Docker runs

---

## ☁️ Option 4: VPS/Cloud Server

### Deploy on DigitalOcean, AWS, Azure, etc.

#### 1. Provision Server
- **Recommended:** Ubuntu 22.04 LTS
- **Minimum:** 2GB RAM, 1 CPU, 20GB storage
- Open ports: 80, 443, 3000, 5000

#### 2. Install Dependencies
```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install pnpm
npm install -g pnpm

# Install Python
apt install -y python3.11 python3-pip

# Install PM2 (process manager)
npm install -g pm2
```

#### 3. Clone and Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/orion-os.git
cd orion-os

# Install frontend dependencies
pnpm install

# Install backend dependencies
pip3 install -r requirements.txt

# Create .env.local
nano .env.local
```

Add to `.env.local`:
```
GEMINI_API_KEY=your_api_key_here
BACKEND_API_URL=http://localhost:5000
ORION_DISABLE_TTS=1
```

#### 4. Build Frontend
```bash
pnpm build
```

#### 5. Setup PM2 Process Manager

Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: 'orion-backend',
      script: 'scripts/api_server.py',
      interpreter: 'python3',
      env: {
        ORION_DISABLE_TTS: '1',
        PORT: '5000'
      },
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: 'orion-frontend',
      script: 'npm',
      args: 'start',
      env: {
        PORT: '3000',
        NODE_ENV: 'production'
      }
    }
  ]
}
```

Start services:
```bash
# Start both services
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

#### 6. Setup Nginx (Optional but Recommended)

Install Nginx:
```bash
apt install -y nginx
```

Create `/etc/nginx/sites-available/orion`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/orion /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### 7. Setup SSL (Optional but Recommended)
```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal is setup automatically
```

### ✅ Result
- Access at: `https://your-domain.com`
- **Production ready** - Secure, scalable, professional

---

## 📊 Deployment Comparison

| Feature | Vercel Only | Vercel + Railway | Docker | VPS |
|---------|-------------|------------------|--------|-----|
| **Cost** | Free | Free tier | Server cost | Server cost |
| **Setup Time** | 5 min | 15 min | 30 min | 1 hour |
| **Full Features** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Backend** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Scalability** | High | High | Medium | Depends |
| **Control** | Low | Medium | High | Full |
| **Maintenance** | Zero | Low | Medium | High |

## 🎯 Recommendations

### For Portfolio/Demo
→ **Vercel Only** - Quick and free

### For Production (Small Scale)
→ **Vercel + Railway** - Best balance of ease and functionality

### For Production (Full Control)
→ **VPS with Docker** - Professional, scalable

### For Enterprise
→ **VPS with Kubernetes** - Maximum scalability

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Setup CORS properly
- [ ] Add rate limiting
- [ ] Setup monitoring
- [ ] Configure backups
- [ ] Add authentication (if needed)
- [ ] Review API key permissions
- [ ] Setup firewall rules

---

## 🐛 Common Deployment Issues

### Issue: "Module not found" errors
**Solution:** Make sure all dependencies are in `package.json` and `requirements.txt`

### Issue: Environment variables not working
**Solution:** Check deployment platform's environment variable settings

### Issue: Backend not connecting
**Solution:**
- Verify BACKEND_API_URL is correct
- Check CORS settings
- Ensure backend is running

### Issue: Port conflicts
**Solution:** Change ports in deployment config

---

## 📚 Additional Resources

- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **Docker Docs**: https://docs.docker.com
- **PM2 Docs**: https://pm2.keymetrics.io
- **Nginx Docs**: https://nginx.org/en/docs

---

## ✅ Post-Deployment

After successful deployment:

1. **Test all features** - AI chat, commands, system metrics
2. **Setup monitoring** - Uptime monitoring, error tracking
3. **Configure analytics** - Track usage (already has Vercel Analytics)
4. **Share your app** - Get the URL and share!

---

**Need help?** Check the troubleshooting section or review the logs on your deployment platform.

**Happy Deploying! 🚀**
