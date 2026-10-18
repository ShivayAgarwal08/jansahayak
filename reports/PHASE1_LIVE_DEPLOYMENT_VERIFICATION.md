# JanSahayak — Phase 1 Live Deployment & Verification Report

**Verification Timestamp**: 2026-10-18T20:07:34+05:30  
**Target Environments**:
- **Backend**: Render Live Deployment (`https://jansahayak-backend-kvuq.onrender.com/api`)
- **Frontend**: Vercel Live Deployment (`https://jansahayak-two.vercel.app`)
- **Database**: Neon Serverless PostgreSQL (`postgresql+psycopg`)
- **Deployed Commit**: `28ad1dc` (`feat: implement Phase 1 SIH vision - fact extraction, grounded retrieval, eligibility & draft prefill`) on GitHub `main`.

---

## 1. Commit and Deployment Status

### GitHub Repository
- **Remote URL**: `https://github.com/ShivayAgarwal08/jansahayak.git`
- **Branch**: `main`
- **HEAD Commit**: `28ad1dc`
- **Status**: Clean working tree; remote `origin/main` synchronized.

### Render Backend Deployment
- **Deployed Service**: `jansahayak-backend-kvuq`
- **Active Commit**: `28ad1dc`
- **Verification Evidence**:
  - `GET /api/health` returned HTTP 200 with `service: "JanSahayak Civic Platform API"`, `version: "1.0.0"`.
  - `GET /api/health/db` returned HTTP 200 with `dialect: "postgresql"`, `database: "connected"`.
  - `POST /api/assistant/chat` returned Phase 1 payload schema including `extracted_profile`, `missing_criteria`, `follow_up_prompt`, `eligibility_results`, and `suggested_action`.
- **CORS Preflight**: OPTIONS to `/api/assistant/chat` from Origin `https://jansahayak-two.vercel.app` returned HTTP 200 with `Access-Control-Allow-Origin: https://jansahayak-two.vercel.app` and `Access-Control-Allow-Credentials: true`.

### Vercel Frontend Deployment
- **Domain**: `https://jansahayak-two.vercel.app`
- **Active Asset**: `/assets/index-SfhE3Hqd.js`
- **Verification Evidence**:
  - Main JS bundle contains Phase 1 strings: `'Extracted Citizen Facts'`, `'Prepare Application Draft for'`, `'Rule Engine Active'`, and `'Phase 1 Grounded RAG'`.
  - API base URL in bundle points to: `https://jansahayak-backend-kvuq.onrender.com`.

---

## 2. Live Verification Results Matrix

| Test Item | Endpoint / Flow | HTTP | Result | Empirical Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **Backend Health** | `GET /api/health` | 200 | **PASS** | `{"status": "healthy", "service": "JanSahayak Civic Platform API"}` |
| **Database Connectivity** | `GET /api/health/db` | 200 | **PASS** | `{"status": "healthy", "database": "connected", "dialect": "postgresql"}` |
| **Scheme Catalog** | `GET /api/schemes` | 200 | **PASS** | 8 verified schemes returned (PM-KISAN, PMAY-G, PM-JAY, etc.) |
| **Fact Extraction (Benchmark)** | `POST /api/assistant/chat` | 200 | **PASS** | Extracted: `state: Bihar`, `occupation: farmer`, `income: Rs. 150,000`, `landholding: 2 bigha(s)`, `children: 3`. |
| **Regional Land Handling** | `POST /api/assistant/chat` | 200 | **PASS** | Raw unit preserved (`2 bigha(s)`) with Bihar pucca bigha survey caveat (~0.62 acres). No erroneous silent conversion. |
| **Stopword & Ranking Filter** | `POST /api/assistant/chat` | 200 | **PASS** | PM-KISAN ranked #1. PMMVY & IGNOAPS successfully suppressed despite generic numbers ("two", "three", "children"). |
| **Deterministic Chat Eligibility**| `POST /api/assistant/chat` | 200 | **PASS** | PM-KISAN evaluated as `possibly_eligible` (requires income tax & govt employee verification). |
| **Follow-Up Question** | `POST /api/assistant/chat` | 200 | **PASS** | Generated: *"To confirm your eligibility under official scheme criteria, could you please clarify: Did you or anyone in your household pay income tax...?"* |
| **Application Prefill CTA** | `POST /api/assistant/chat` | 200 | **PASS** | Returns `suggested_action: {"action": "prepare_application", "scheme_slug": "pm-kisan", "prefill_data": {...}}`. |
| **Multi-Turn Fact Memory** | `POST /api/assistant/chat` | 200 | **PASS** | Second turn merged `pays_income_tax: False` and `is_govt_employee: False` with earlier facts; PM-KISAN updated to `eligible`. |
| **AI Fallback Transparency** | `POST /api/assistant/chat` | 200 | **PASS** | Explicitly returned `is_fallback: True`, `status: "fallback_grounded"`, `ai_provider: "none"`, and honest disclosure notice. |
| **Citizen Registration** | `POST /api/auth/register` | 200 | **PASS** | Successfully registered isolated test citizen; JWT access token issued. |
| **User Profile Isolation** | `GET /api/auth/me` | 200 | **PASS** | Returned authenticated user identity strictly matching issued token. |
| **Draft Creation & Privacy** | `POST /api/applications` | 201 | **PASS** | Created application draft using chat-extracted notes. Sensitive citizen data passed in POST body, **NOT in URLs or search params**. |
| **Draft Multi-Tenant Isolation** | `GET /api/applications` | 200 | **PASS** | Isolated list returned exactly 1 draft owned by the authenticated citizen. |
| **Direct Eligibility Engine** | `POST /api/eligibility/assess`| 200 | **PASS** | Evaluated PM-KISAN rules deterministically; included statutory non-guarantee disclaimer. |

---

## 3. Privacy, Security & Data Grounding Audits

1. **URL & Query Parameter Hygiene**:
   - Navigation from `/assistant` to `/apply` uses React Router `location.state` in-memory passing.
   - Citizen attributes (`annual_income`, `landholding`, `district`, `occupation`) do **NOT** appear in browser URL address bars, server query logs, or browser history caches.
2. **Multi-Tenant Data Separation**:
   - `ApplicationDraft` operations strictly enforce `user_id == current_user.id`. Citizens cannot inspect, modify, or delete drafts belonging to other accounts.
3. **Statutory Disclaimers & Grounding**:
   - Every eligibility result returns:
     > *"This automated assessment is rule-based informational guidance and does not constitute official sanction, approval, or guarantee of welfare benefits by the issuing government department."*
   - Application preparation forms explicitly state that drafting does not submit records to government portals.

---

## 4. Operational Status & Configuration Checklist

| Service | Environment Variable | Current Value / Status | Note |
| :--- | :--- | :--- | :--- |
| **Render** | `DATABASE_URL` | Neon PostgreSQL (Active) | Connection verified via `/api/health/db`. |
| **Render** | `FRONTEND_ORIGIN` | `https://jansahayak-two.vercel.app` | CORS preflight verified with credentials enabled. |
| **Render** | `GROQ_API_KEY` | *Unset / Optional* | Backend safely operates in verified deterministic fallback mode. Adding a Groq Cloud key immediately activates live `llama-3.3-70b-versatile` inference. |
| **Render** | `GROQ_MODEL` | `llama-3.3-70b-versatile` | Pre-configured in code. |
| **Vercel** | `VITE_API_BASE_URL` | `https://jansahayak-backend-kvuq.onrender.com/api` | Confirmed inside deployed JavaScript bundle. |

---

## 5. Verification Verdict

**Phase 1 Status: FULLY OPERATIONAL & VERIFIED ON LIVE HOSTS**  
- Local automated test suite: 24 passed, 1 skipped.  
- Live cloud test suite: 16 live API assertions passed against Render & Neon PostgreSQL.  
- Frontend bundle: compiled cleanly and serving verified Phase 1 components on Vercel.  
- Zero regressions introduced to existing authentication, dashboard, scheme directory, PDF generation, RTI, or Grievance workflows.
