# JanSahayak — External API & Integration Audit

**Audit Date**: October 18, 2026  
**Auditor**: Senior Full-Stack & DevOps Engineering Agent  
**Repository**: `https://github.com/ShivayAgarwal08/jansahayak`  
**Report Location**: `reports/EXTERNAL_API_AUDIT.md`  

---

## 1. Inventory of External Services & Providers

| Provider | Purpose | Code Location | Required Env Vars | Status | Live Test Result | Fallback Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Neon PostgreSQL** | Primary Production Relational Database | `backend/app/db/session.py` | `DATABASE_URL` | **VERIFIED & CONNECTED** | HTTP 200 via `/api/health/db`, dialect `postgresql` verified | Local SQLite development fallback |
| **Groq Cloud API** | Grounded LLM Chat (`llama-3.3-70b-versatile`) | `backend/app/services/ai/groq_service.py` | `GROQ_API_KEY`, `GROQ_MODEL` | **PENDING CREDENTIALS** | Unconfigured; verified deterministic passage synthesis fallback | Rule-grounded synthesis directly from top verified passages with portal links |
| **Bhashini (Digital India)** | Automatic Speech Recognition (ASR) & Neural Translation (NMT) | `backend/app/services/bhashini/bhashini_service.py` | `BHASHINI_USER_ID`, `BHASHINI_API_KEY`, `BHASHINI_PIPELINE_ENDPOINT` | **PENDING CREDENTIALS** | Unconfigured; endpoint `/api/voice/status` returns `awaiting_credentials` | Browser Web Speech API (`webkitSpeechRecognition`) for voice input |
| **Browser Web Speech API** | Client-Side Voice Recognition | `frontend/src/pages/AssistantPage.tsx` | N/A (Browser Native) | **VERIFIED (Client-side)** | Verified in Chrome/Edge on desktop/mobile for `en-IN` and `hi-IN` | Manual text typing input fallback |
| **Meta WhatsApp Cloud API** | Conversational WhatsApp Bot | `docs/api-integrations.md` (documented only) | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | **NOT IMPLEMENTED** | No backend routes, webhooks, or handlers exist in repository | Web app interface (`https://jansahayak-two.vercel.app`) |

---

## 2. Detailed Service Analyses

### 1. Neon Serverless PostgreSQL
- **Implementation**: [`backend/app/db/session.py`](file:///C:/Users/SHIVAY%20AGARWAL/Desktop/JANSAHAYAK/backend/app/db/session.py)
- **Driver**: Psycopg 3 (`psycopg[binary]>=3.1.18`) with fallback to Psycopg 2 (`psycopg2-binary>=2.9.9`).
- **Configuration**:
  - Automatically converts `postgres://` or `postgresql://` connection strings to `postgresql+psycopg://`.
  - Enforces `sslmode=require` for remote database hosts.
  - Connection pooling with `pool_pre_ping=True` and `pool_recycle=300` to prevent stale connection drops on serverless architectures.
- **Verification**:
  - Live query to `https://jansahayak-backend-kvuq.onrender.com/api/health/db` returns:
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "dialect": "postgresql"
    }
    ```
- **Cost / Limits**: Free tier provides 0.5 GiB storage and 100 CU hours, sufficient for production pilot.

---

### 2. Groq Cloud LLM Service
- **Implementation**: [`backend/app/services/ai/groq_service.py`](file:///C:/Users/SHIVAY%20AGARWAL/Desktop/JANSAHAYAK/backend/app/services/ai/groq_service.py)
- **Model**: `llama-3.3-70b-versatile` (configurable via `GROQ_MODEL`).
- **Endpoint**: `https://api.groq.com/openai/v1/chat/completions`.
- **System Prompt**: Enforces strict grounding inside `<VERIFIED_GOVERNMENT_EVIDENCE>` tags. Explicitly forbids hallucinating scheme rules or deadlines.
- **Current Runtime Status**:
  - In production and local environments, `GROQ_API_KEY` is not set.
  - The service executes lines 96–118 (Deterministic Non-Hallucinatory Fallback), which synthesizes information directly from retrieved verified scheme records.
  - When `GROQ_API_KEY` is configured, requests timeout after 20.0s and gracefully degrade to deterministic synthesis upon failure or rate limit.

---

### 3. Bhashini (National Language Translation Mission)
- **Implementation**: [`backend/app/services/bhashini/bhashini_service.py`](file:///C:/Users/SHIVAY%20AGARWAL/Desktop/JANSAHAYAK/backend/app/services/bhashini/bhashini_service.py)
- **API Endpoint**: `https://dhruva-api.bhashini.gov.in/services/inference/pipeline`.
- **Capabilities in Code**:
  - Automatic Speech Recognition (`taskType: "asr"` with WAV audio).
  - Neural Machine Translation (`taskType: "translation"`).
  - Supported Languages: 11 official Indian languages (en, hi, bn, ta, te, mr, gu, kn, ml, pa, or).
- **Gaps Identified**:
  - **Text-to-Speech (TTS) is not implemented** in `BhashiniService`.
  - **Bhojpuri (`bho`) is not included** in `SUPPORTED_LANGUAGES`.
  - Credentials (`BHASHINI_USER_ID`, `BHASHINI_API_KEY`) are unconfigured.
  - The frontend microphone button in `AssistantPage.tsx` invokes browser Web Speech API rather than sending audio payloads to `/api/voice/stt`.

---

### 4. Meta WhatsApp Cloud API
- **Current Status**: **NOT IMPLEMENTED**
- **Analysis**:
  - Mentioned in `docs/api-integrations.md` as an optional future channel.
  - No webhook endpoint (e.g. `/api/whatsapp` or `/webhook`) exists in the FastAPI router registrations.
  - No message dispatching client or signature verification logic (`X-Hub-Signature-256`) exists in the codebase.
