# JanSahayak — Phase 1 SIH Vision Implementation Report

**Date**: 2026-10-18  
**Scope**: Connect natural-language citizen chat to structured fact extraction, grounded scheme retrieval, the existing deterministic eligibility engine, and application-draft prefill.  
**Branch**: `main`  
**Git Commit Target**: Phase 1 Core Completion  

---

## 1. Executive Summary

Phase 1 bridges the critical gap between conversational natural language and JanSahayak's deterministic civic infrastructure. In the previous baseline, conversational queries were matched using naive whitespace token splitting, resulting in unrelated maternal or pension schemes appearing for working farmers, while citizen facts (income, land, occupation) were lost and never evaluated against eligibility rules.

With Phase 1 complete:
1. **Conversational Citizen Profile Extraction**: Natural language inputs are parsed for state, district, occupation, age, gender, annual income, landholding, housing, and BPL status without hallucination.
2. **Indian Currency Normalization**: Formats like `₹1.5 lakh`, `1.5 lakhs`, `50k`, and `2 crore` are normalized to exact rupee integers.
3. **Regional Landholding Awareness**: Regional land units (e.g., *bigha*) are preserved with regional caveats rather than silently converted using erroneous standard acreage conversions.
4. **Domain-Intent Grounded Retrieval**: An extensive stopword filter and domain weighting ensure generic numbers (e.g., *"two"*, *"three"*) do not cause PMMVY or IGNOAPS to rank above PM-KISAN.
5. **Deterministic Rules Integration**: The assistant directly evaluates citizen profiles against the verified rules engine and returns explicit criteria breakdowns (`eligible`, `possibly_eligible`, `ineligible`).
6. **Application Draft Prefill**: When a citizen qualifies, an actionable CTA allows them to transfer confirmed facts into the Application Preparation Workspace with one click.
7. **Transparent AI Status**: The system honestly reports whether answers are generated via Groq (`llama-3.3-70b-versatile`) or synthesized via the rule engine fallback when credentials are offline.

---

## 2. Actual Files Changed & Created

### Backend Changes
1. **`backend/app/services/ai/profile_extractor.py`** *(NEW)*:
   - Implements `extract_citizen_profile(text)` extracting 15+ verified civic facts.
   - Implements `normalize_indian_currency(text)` handling lakhs, crores, thousands, and raw numbers.
   - Implements `parse_landholding(text, state)` preserving regional bigha variations without silent conversions.
   - Implements `generate_profile_followups(profile, schemes)` asking focused clarification questions for missing eligibility fields.
   - Implements negation-first logic for tax payee and government employee detection.

2. **`backend/app/services/rag/retrieval.py`** *(MODIFIED)*:
   - Added comprehensive civic and conversational `STOPWORDS` list.
   - Added `DOMAIN_INTENTS` mapping keywords and domain boosts for all 8 seeded schemes.
   - Added penalty filters preventing maternity/pension false positives for agricultural queries.
   - Annotated passages with `match_reasons` and `is_seeded_record` provenance metadata.

3. **`backend/app/services/ai/groq_service.py`** *(MODIFIED)*:
   - Grounded prompt updated to include `<CITIZEN_EXTRACTED_PROFILE>` and `<DETERMINISTIC_ELIGIBILITY_EVALUATION>`.
   - Honest fallback disclosure: returns `is_fallback: True`, `status: "fallback_grounded"`, and `ai_provider: "none"` when `GROQ_API_KEY` is unset or unreachable.
   - Never fabricates AI success when in fallback mode.

4. **`backend/app/schemas/assistant.py`** *(MODIFIED)*:
   - Expanded `AssistantChatRequest` with `existing_profile` for multi-turn conversational memory.
   - Expanded `AssistantChatResponse` with `extracted_profile`, `missing_criteria`, `follow_up_prompt`, `eligibility_results`, and `suggested_action`.

5. **`backend/app/api/assistant.py`** *(MODIFIED)*:
   - Orchestrates profile extraction $\rightarrow$ grounded retrieval $\rightarrow$ deterministic scheme evaluation $\rightarrow$ follow-up generation $\rightarrow$ application prefill generation $\rightarrow$ grounded answer synthesis.

6. **`backend/tests/test_phase1_sih_vision.py`** *(NEW)*:
   - 13 comprehensive automated unit, integration, and end-to-end tests covering currency normalization, bigha handling, the Bihar farmer benchmark query, retrieval ranking, follow-ups, deterministic evaluation, mocked Groq success, Groq offline fallback, and multi-turn session memory.

### Frontend Changes
1. **`frontend/src/types/index.ts`** *(MODIFIED)*:
   - Added `ExtractedProfile` and `SuggestedAction` interfaces.
   - Expanded `AssistantResponse` with Phase 1 rich fields.

2. **`frontend/src/services/api.ts`** *(MODIFIED)*:
   - Updated `chatAssistant` to pass `existingProfile` in multi-turn chats.

3. **`frontend/src/pages/AssistantPage.tsx`** *(MODIFIED)*:
   - Added Extracted Facts Card displaying confirmed attributes (State, Occupation, Income, Land).
   - Added Follow-Up Clarification Prompt highlighting missing criteria required for qualification.
   - Added "Prepare Application Draft for [Scheme]" CTA navigating directly to `/apply` with prefilled state.
   - Added AI provider transparency disclosure banner (Rule-Grounded Mode vs. Groq Llama-3.3-70B).

4. **`frontend/src/pages/ApplicationPrepPage.tsx`** *(MODIFIED)*:
   - Reads `location.state.prefill` and pre-populates applicant details and notes from conversation.
   - Added notification banner informing citizen of pre-filled data.

---

## 3. Automated Test Results

### Backend Test Suite
Executed via `pytest backend/tests`:
```text
backend\tests\test_auth_and_api.py ........                              [ 32%]
backend\tests\test_eligibility.py ....                                   [ 48%]
backend\tests\test_phase1_sih_vision.py ............s                    [100%]

================= 24 passed, 1 skipped, 10 warnings in 7.11s ==================
```
- **24 tests passed (100% pass rate)**.
- **1 test skipped**: `test_live_groq_smoke_test_if_configured` (cleanly skipped because `GROQ_API_KEY` is not present in local development environment).

### Benchmark Query Verification
- **Input**: *"A farmer from Bihar speaks in Bhojpuri and says they have three children, two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"*
- **Extraction**:
  - Occupation: `"farmer"`
  - State: `"Bihar"`
  - Income: `150000.0`
  - Landholding: `"2.0 bigha(s)"` (with Bihar pucca bigha caveat ~0.62 acres preserved)
  - Children: `3`
  - Missing facts flagged: Income tax status, Government employee status.
- **Retrieval**:
  - Top 1: **PM-KISAN** (`pm-kisan`)
  - Excluded: PMMVY and IGNOAPS successfully suppressed.
- **Eligibility Engine**:
  - PM-KISAN status: `possibly_eligible` (requires tax and employment clarification).
- **Suggested Action**:
  - Action: `prepare_application` for `pm-kisan` with prefilled income, state, and landholding.

### Frontend Compilation & Typecheck
Executed via `tsc -b && vite build` in `frontend/`:
```text
vite v8.3.4 building client environment for production...
transforming...
✓ 1952 modules transformed.
dist/index.html                   1.19 kB │ gzip:   0.67 kB
dist/assets/index-Jn1EjaOC.css   29.56 kB │ gzip:   6.09 kB
dist/assets/index-Ds0Gh0kt.js   424.77 kB │ gzip: 117.47 kB
✓ built in 3.28s
```
- Zero TypeScript compiler errors.
- Clean production bundle generated.

---

## 4. Known Limitations & Next Steps

1. **Seeded Scheme Catalog Size**:
   - The deterministic engine and retrieval currently cover 8 central/state welfare schemes. Expanding to 50+ schemes is scheduled for subsequent phases.
2. **Groq API Key on Render**:
   - Groq inference (`llama-3.3-70b-versatile`) is fully implemented in code. In production, Render currently has `GROQ_API_KEY` unset, so the backend safely runs in transparent deterministic rule fallback mode. Once an API key is added to Render environment settings, the assistant will automatically activate live Groq LLM responses without code modifications.
3. **Bhashini Voice Services**:
   - Browser Web Speech API (`hi-IN`, `en-IN`) is active on the client. Bhashini ASR/NMT endpoints remain ready for activation once MeitY credentials (`BHASHINI_USER_ID`, `BHASHINI_API_KEY`) are supplied.

---

## 5. Deployment Configuration Checklist

| Service | Environment Variable | Current Value / Status | Action Required |
| :--- | :--- | :--- | :--- |
| **Render (Backend)** | `DATABASE_URL` | Neon PostgreSQL (Active) | No change required (Preserved) |
| **Render (Backend)** | `SECRET_KEY` | Set (Production) | No change required |
| **Render (Backend)** | `FRONTEND_ORIGIN` | `https://jansahayak-two.vercel.app` | No change required |
| **Render (Backend)** | `GROQ_API_KEY` | *Optional* | Add Groq Cloud API key in Render Dashboard to enable live LLM generation |
| **Render (Backend)** | `GROQ_MODEL` | `llama-3.3-70b-versatile` | Pre-configured default |
| **Vercel (Frontend)** | `VITE_API_BASE_URL` | `https://jansahayak-backend-kvuq.onrender.com/api` | No change required |
