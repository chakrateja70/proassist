# Proassist Backend (FastAPI)

## Setup

1. Create virtual env and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill values.
3. Run API:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Notes

- Tables are created automatically on startup for local development.
- OAuth callback path must match `GOOGLE_REDIRECT_URI`.
- Session token is stored in `proassist_session` cookie.
- Worker endpoint requires `X-Worker-Secret` header.

## Key Endpoints

- `POST /auth/google/start`
- `GET /auth/google/callback`
- `GET /me`
- `PUT /profile`
- `POST /resumes/upload`
- `GET /resumes`
- `POST /jobs`
- `POST /drafts/generate`
- `PATCH /drafts/{draft_id}`
- `POST /sends`
- `GET /history`
- `POST /internal/worker/run-due-jobs`
