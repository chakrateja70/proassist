# Proassist Monorepo

This repository contains:

- `backend/` FastAPI API with Neon Postgres, Google OAuth/Gmail/Drive, OpenAI draft generation.
- run background: uvicorn main:app --reload
- `frontend/` Next.js client for onboarding, profile, generation, review, and history.

## Quick Start

1. Configure backend:
   - `cd backend`
   - `pip install -r requirements.txt`
   - copy `.env.example` to `.env` and fill Google/OpenAI/Neon values
   - `uvicorn app.main:app --reload --port 8000`
2. Configure frontend:
   - `cd frontend`
   - `npm install`
   - copy `.env.local.example` to `.env.local`
   - `npm run dev`

## Cron Worker

Call:

`POST /internal/worker/run-due-jobs`

with header:

`X-Worker-Secret: <WORKER_SECRET>`

from a scheduler to process due emails.
