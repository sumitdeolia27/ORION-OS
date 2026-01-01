# ⚡ Quick Deploy - ORION OS

Choose your deployment method and follow the steps below:

---

## 🚀 Method 1: Vercel (5 Minutes) - EASIEST

Perfect for demos and portfolios. Frontend only.

### Steps:
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy
vercel

# 4. When prompted:
#    - Set up and deploy? Y
#    - Which scope? Select your account
#    - Link to existing project? N
#    - Project name? orion-os (or your choice)
#    - Directory? ./
#    - Override settings? N

# 5. Add environment variable
vercel env add GEMINI_API_KEY
# Paste your API key when prompted

# 6. Deploy to production
vercel --prod
```

**Done!** Visit the URL Vercel gives you.

**Note:** Backend features won't work. AI Chat works, but system commands don't.

---

## 🐳 Method 2: Docker (10 Minutes) - RECOMMENDED

Full features, works anywhere Docker runs.

### Prerequisites:
- Docker installed
- Docker Compose installed

### Steps:
```bash
# 1. Create .env file with your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 2. Build and run
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f
```

**Done!** Visit:
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

### To Stop:
```bash
docker-compose down
```

### To Rebuild:
```bash
docker-compose up -d --build
```

---

## 🚂 Method 3: Railway (15 Minutes) - FULL STACK

Free tier, full features, automatic HTTPS.

### Backend:
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables:
   ```
   ORION_DISABLE_TTS=1
   GEMINI_API_KEY=your_api_key_here
   ```
6. Deploy - Railway gives you a URL like `https://orion-backend.railway.app`

### Frontend:
1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository
4. Add environment variables:
   ```
   GEMINI_API_KEY=your_api_key_here
   NEXT_PUBLIC_BACKEND_API_URL=https://orion-backend.railway.app
   ```
5. Deploy

**Done!** Both services are live with HTTPS!

---

## 🖥️ Method 4: VPS/Server (30 Minutes)

Full control, production ready.

### Prerequisites:
- Ubuntu server (DigitalOcean, AWS, etc.)
- Domain name (optional but recommended)

### Quick Setup:
```bash
# SSH into your server
ssh root@your-server-ip

# Run automated setup
curl -o- https://raw.githubusercontent.com/YOUR_USERNAME/orion-os/main/scripts/deploy.sh | bash

# Or manual setup:

# 1. Install dependencies
apt update && apt upgrade -y
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs python3.11 python3-pip nginx
npm install -g pnpm pm2

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/orion-os.git
cd orion-os

# 3. Install dependencies
pnpm install
pip3 install -r requirements.txt

# 4. Create .env.local
cat > .env.local << EOF
GEMINI_API_KEY=your_api_key_here
BACKEND_API_URL=http://localhost:5000
ORION_DISABLE_TTS=1
EOF

# 5. Build frontend
pnpm build

# 6. Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 7. Setup Nginx (optional)
# See DEPLOYMENT_GUIDE.md for Nginx config
```

**Done!** Visit your server IP or domain.

---

## 📦 One-Click Deploy Buttons

Add these to your README.md:

### Deploy Frontend to Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/orion-os)

### Deploy Backend to Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/YOUR_USERNAME/orion-os)

---

## ✅ Post-Deployment Checklist

After deploying:

- [ ] Test AI chat functionality
- [ ] Test system commands (if backend deployed)
- [ ] Verify environment variables are set
- [ ] Check that HTTPS is working
- [ ] Test on mobile devices
- [ ] Setup monitoring (optional)
- [ ] Configure custom domain (optional)

---

## 🐛 Troubleshooting

### Frontend builds but shows errors
- Check environment variables in deployment platform
- Verify BACKEND_API_URL is correct
- Check browser console for errors

### Backend not connecting
- Verify backend is deployed and running
- Check CORS settings in api_server.py
- Ensure ports are open (5000)

### "Module not found" errors
- Make sure all dependencies are in package.json
- Try rebuilding with `--force` flag

### API key not working
- Double-check the key in environment variables
- Ensure key has proper permissions
- Verify key is not expired

---

## 🆘 Need Help?

- Full guide: See `DEPLOYMENT_GUIDE.md`
- Issues: Check GitHub issues
- Logs: Check deployment platform logs

---

## 🎉 Success!

Once deployed, share your ORION OS with the world!

**Don't forget to:**
- Add your deployed URL to README.md
- Share on social media
- Star the repository ⭐

Happy deploying! 🚀
