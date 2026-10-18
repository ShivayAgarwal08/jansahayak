# JanSahayak Deployment Guide

Step-by-step instructions to deploy JanSahayak across Vercel (Frontend), Render (Backend), and Neon (Database).

---

## 1. Database Deployment (Neon PostgreSQL)

1. Sign up / Log in to [Neon.tech](https://neon.tech).
2. Create a project named `jansahayak-db`.
3. In the project dashboard, locate the **Connection Details** widget.
4. Select **Pooled Connection** (recommended for serverless environments) or **Direct Connection**.
5. Copy the connection string:
   ```text
   postgresql://[user]:[password]@[endpoint].neon.tech/neondb?sslmode=require
   ```
6. (Optional) Run the pgvector extension query in the Neon SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## 2. Backend Deployment (Render)

1. Sign up / Log in to [Render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository: `https://github.com/ShivayAgarwal08/jansahayak`.
4. Configure service settings:
   - **Name**: `jansahayak-api`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure Environment Variables in Render:
   - `DATABASE_URL`: Your Neon connection string (ensure `postgresql://` protocol).
   - `SECRET_KEY`: A strong random string (`openssl rand -hex 32`).
   - `ENVIRONMENT`: `production`
   - `FRONTEND_ORIGIN`: Your public Vercel domain (e.g., `https://jansahayak.vercel.app`).
   - `GROQ_API_KEY`: Your Groq API key.
   - `BHASHINI_USER_ID`: (Optional / when approved)
   - `BHASHINI_API_KEY`: (Optional / when approved)
6. Click **Deploy Web Service**.
7. Note down the assigned public backend URL: `https://jansahayak-api.onrender.com`.

---

## 3. Frontend Deployment (Vercel)

1. Sign up / Log in to [Vercel.com](https://vercel.com).
2. Click **Add New** -> **Project**.
3. Import your GitHub repository: `ShivayAgarwal08/jansahayak`.
4. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Environment Variables:
   - `VITE_API_BASE_URL`: The public backend URL (e.g., `https://jansahayak-api.onrender.com`).
6. Click **Deploy**.
7. Vercel automatically configures SSL and continuous deployment from the `main` branch.

---

## 4. Production Smoke Testing Checklist

- [ ] Open Vercel URL in mobile and desktop browsers.
- [ ] Verify homepage loads without console errors.
- [ ] Check `/api/health` returns `{"status": "healthy"}`.
- [ ] Test registration with a new citizen account.
- [ ] Perform a scheme search and filter by state/category.
- [ ] Run an eligibility check and verify deterministic rules breakdown.
- [ ] Create an application draft and download the generated PDF.
- [ ] Test RTI and Grievance drafting workflows and PDF export.
- [ ] Test login/logout and citizen data isolation.
