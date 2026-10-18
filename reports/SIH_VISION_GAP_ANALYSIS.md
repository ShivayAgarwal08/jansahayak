# JanSahayak (जनसहायक) — Original SIH Vision vs. Actual Implementation Gap Analysis

**Date**: October 18, 2026  
**Auditor**: Senior Full-Stack & DevOps Engineering Agent  
**Original Vision Statement**:  
> *"A citizen can describe their situation in their own Indian language by voice or text. The system understands their situation, retrieves genuine official government scheme documents, evaluates eligibility using explicit rules, explains the result with evidence, prepares an application draft, and helps draft an RTI or grievance when needed."*

---

## 1. Executive Summary: Vision vs. Reality

| Core Dimension | Original SIH Vision | Current Reality in Codebase | Verdict |
| :--- | :--- | :--- | :---: |
| **Input Modality** | Spoken or typed in regional Indian languages & dialects (e.g. Bhojpuri, Maithili, Awadhi) | Web typing in any language; voice input uses Chrome/Edge browser Web Speech API (`hi-IN`, `en-IN` only) | **PARTIAL** |
| **NLU & Fact Extraction** | Conversational slot-filling extracting occupation, income, land, family; regional unit normalization (`bigha`, `katha`) | No entity extraction or slot-filling; raw query string is passed directly into token regex search | **MISSING** |
| **LLM Reasoning** | Grounded LLM reasoning explaining eligibility and answering questions | Groq Llama 3.3 client implemented with strict prompt fences, but **currently dormant** (no API key configured); operates via deterministic text fallback | **PARTIALLY IMPLEMENTED (DORMANT)** |
| **Document Retrieval & RAG** | Vector embeddings over official government scheme PDFs/guidelines with semantic search | In-memory token-substring scoring over 8 manually seeded scheme records in PostgreSQL; no PDF crawler, vector DB, or embeddings model | **SIMULATED / PARTIAL** |
| **Eligibility Evaluation** | Traceable, deterministic rules engine evaluating user profile against criteria | Pure Python deterministic rules engine covering 8 national schemes with `satisfied`, `unsatisfied`, and `unknown` condition tracking | **FULLY IMPLEMENTED (FORM-BASED)** |
| **Bhashini Integration** | Official Digital India Bhashini pipeline for ASR, NMT, and TTS across Indian languages | Client code written for ASR and NMT; **TTS missing**; **Bhojpuri not in language list**; credentials unconfigured; `/api/voice/status` returns `awaiting_credentials` | **PARTIAL (AWAITING CREDENTIALS)** |
| **Application & Legal Drafting** | AI-generated application kits, RTI petitions, and grievance drafts based on conversational state | Form-based wizards with pre-canned templates; generates downloadable ReportLab PDFs; user data from chat/eligibility does not auto-populate | **PARTIALLY IMPLEMENTED** |
| **WhatsApp Channel** | Direct citizen interaction via WhatsApp bot for rural accessibility | Documented as future concept in `docs/api-integrations.md`; **zero code, webhooks, or endpoints exist** | **NOT IMPLEMENTED** |

---

## 2. Requirement 1 — Natural-Language Citizen Understanding

### Test Scenario
We submitted the benchmark query:
> *"A farmer from Bihar speaks in Bhojpuri and says they have three children, two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"*

### Observed Execution & Code Path
1. **Entry Point**: `POST /api/assistant/chat` (`backend/app/api/assistant.py`).
2. **Retrieval**: Query passed into `retrieve_grounded_passages(query, db)` in [`backend/app/services/rag/retrieval.py`](file:///C:/Users/SHIVAY%20AGARWAL/Desktop/JANSAHAYAK/backend/app/services/rag/retrieval.py).
3. **Token Extraction**:
   ```python
   query_tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
   ```
   Tokens extracted: `['farmer', 'from', 'bihar', 'speaks', 'bhojpuri', 'and', 'says', 'they', 'have', 'three', 'children', 'two', 'bighas', 'land', 'annual', 'income', 'around', 'lakh', 'which', 'government', 'schemes', 'might', 'qualify', 'for']`.
4. **Scoring**: Loop checks substring occurrences across hardcoded text blocks for the 8 schemes.
5. **Retrieved Result**:
   - Passage 1: *Pradhan Mantri Matru Vandana Yojana (PMMVY)* — Maternity benefit!
   - Passage 2: *PMMVY Overview*
   - Passage 3: *Indira Gandhi National Old Age Pension Scheme (IGNOAPS)* — Senior citizen pension!
   - Passage 4: *PMMVY Eligibility*
   *(PM-KISAN was not even retrieved because tokens like "two", "three", "children", "qualify" scored higher in PMMVY text).*
6. **Fallback Output**: Synthesized text explaining maternal pregnancy benefits for a male farmer with land!

### Specific Capability Audit
- **Language Identification**: **MISSING**. No language identification library (`fasttext`, `langdetect`) or prompt classifier is present.
- **Semantic Understanding**: **MISSING**. System counts raw word occurrences; it does not understand that the speaker is a farmer seeking agricultural welfare.
- **Entity & Fact Extraction**: **NOT IMPLEMENTED**. Does not extract:
  - `occupation: "farmer"`
  - `state: "Bihar"`
  - `landholding: "2 bighas"`
  - `income: 150000`
  - `family_size: 5`
- **Currency & Numeric Normalization**: **MISSING**. "₹1.5 lakh" is not converted to `150,000`.
- **Regional Land Conversion**: **MISSING**. A *bigha* in Bihar is ~20 katthas (~0.62 acres or 2,529 m²), whereas in Western UP it is ~0.20 acres, and in Assam ~0.33 acres. The system has zero knowledge of regional land conversions and cannot map "two bighas in Bihar" to acres for PM-KISAN.
- **Follow-up Interaction**: **MISSING**. The assistant does not identify missing facts (e.g. asking "Do you or your family pay income tax?" or "Is the land registered in your name?").
- **Status**: **FAILED / NOT IMPLEMENTED**.

---

## 3. Requirement 2 — Real LLM Integration

### Code Inspection: `backend/app/services/ai/groq_service.py`
```python
if settings.GROQ_API_KEY:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={"model": settings.GROQ_MODEL, ...}
            )
```

### Observations
1. **Configured Provider**: Groq Cloud API.
2. **Configured Model**: `llama-3.3-70b-versatile` (specified in `backend/app/core/config.py`).
3. **Current Runtime Status**:
   - In both local and deployed Render environments, `GROQ_API_KEY` is currently `None`.
   - The condition `if settings.GROQ_API_KEY:` evaluates to `False`.
   - The code falls through to the deterministic fallback, which dumps the first retrieved passage.
4. **Resilience & Safe Fallbacks**:
   - Timeout (20.0s), network failure, and missing key scenarios are safely caught.
   - The system does not crash when the key is absent.
5. **Grounded Prompting**:
   - System prompt explicitly enforces: *"Base your answer EXCLUSIVELY on the verified government evidence provided... DO NOT hallucinate, assume, or invent schemes..."*
6. **Status**: **PARTIALLY IMPLEMENTED (DORMANT AWAITING API KEY)**.

---

## 4. Requirement 3 — Genuine RAG & Official Government Documents

### Inspection of the Retrieval Pipeline
1. **Document Source**:
   - Documents are **not** crawled, downloaded, or parsed from government portals.
   - All knowledge resides in [`backend/app/db/seed_data.py`](file:///C:/Users/SHIVAY%20AGARWAL/Desktop/JANSAHAYAK/backend/app/db/seed_data.py) as 8 curated dictionaries in `VERIFIED_SCHEMES`.
2. **Provenance & Attribution**:
   - Official URLs (e.g. `https://pmkisan.gov.in/Documents_New/Revised_Operational_Guidelines_PM_KISAN.pdf`, `https://pmayg.nic.in/netiay/Pmay-G-Guidelines-En.pdf`) are recorded in the `scheme_sources` database table.
   - However, the underlying PDF binaries are **never downloaded, OCR'd, or stored**.
3. **Vector Database & Embeddings**:
   - `pgvector`, ChromaDB, Qdrant, and FAISS are **not used**.
   - No embedding model (e.g. OpenAI `text-embedding-3`, BGE, or MiniLM) is integrated.
   - Retrieval is implemented as token matching in Python memory.
4. **Citation Reliability**:
   - Citations return the official scheme URLs and issuing ministries stored in the database.
   - However, citations point to the whole scheme guideline rather than specific page numbers or clauses in an extracted document corpus.
5. **Status**: **SIMULATED RAG / PARTIAL**.

---

## 5. Requirement 4 — Actual Scheme Eligibility Engine

### Inspection: `backend/app/services/eligibility/engine.py`
The deterministic rules engine is one of the strongest implementations in the repository:
1. **Traceable Criteria**:
   - Pure Python rule evaluation; zero hallucination.
   - Evaluates:
     - `State Residency` (geographical scope).
     - `Non-Government Employee Exclusion`.
     - `Income Tax Payee Exclusion`.
     - Scheme-specific rules: Cultivable landownership (`PM-KISAN`), Kutcha/houseless dwelling & rural area (`PMAY-G`), Age 70+ universal senior pathway or BPL/SECC (`Ayushman Bharat`), Maternity & age 19+ (`PMMVY`), Age 60+ and BPL (`IGNOAPS`), Girl child age <= 10 (`Sukanya Samriddhi`), Street vending occupation (`PM SVANidhi`), 18 traditional crafts (`PM Vishwakarma`).
2. **Outcome Tri-Partition**:
   - `eligible`: All conditions satisfied.
   - `possibly_eligible`: One or more conditions missing/unknown.
   - `ineligible`: One or more hard exclusion conditions failed.
3. **Disclaimers**:
   - Automatically attaches official legal disclaimer stating that automated rule assessments are informational and do not constitute government sanction.
4. **Gaps Identified**:
   - Only 8 schemes are codified.
   - Rules are hardcoded in `engine.py` Python functions rather than dynamically evaluated from the database JSON rule column.
   - The engine is decoupled from the chat assistant; a citizen cannot assess eligibility via natural conversation without manually filling out the `/eligibility` form.
5. **Status**: **FULLY IMPLEMENTED (FORM-BASED, LIMITED TO 8 SCHEMES)**.

---

## 6. Requirement 5 — Bhashini & Multilingual Voice

### Inspection: `backend/app/services/bhashini/bhashini_service.py` & `frontend/src/pages/AssistantPage.tsx`
1. **Bhashini ASR & NMT**:
   - Code structures payloads for Dhruva inference endpoint (`https://dhruva-api.bhashini.gov.in/services/inference/pipeline`).
   - Requires `BHASHINI_USER_ID` and `BHASHINI_API_KEY`.
   - Currently unconfigured; endpoint `/api/voice/status` returns `{"configured": false, "status": "awaiting_credentials"}`.
2. **Text-to-Speech (TTS)**:
   - **NOT IMPLEMENTED**. `bhashini_service.py` has no TTS method or audio synthesis pipeline.
3. **Dialect Support (Bhojpuri)**:
   - **NOT SUPPORTED**. Supported language array contains 11 languages (`en, hi, bn, ta, te, mr, gu, kn, ml, pa, or`). Bhojpuri (`bho`) is not in the array and is not handled by the fallback.
4. **Client-Side Voice Behavior**:
   - Microphone button in `AssistantPage.tsx` uses browser `SpeechRecognition` API.
   - Hardcoded to `hi-IN` or `en-IN`.
   - On browsers without Web Speech API (or non-Chrome/Edge), voice input fails and prompts user to type.
5. **Status**: **PARTIAL (AWAITING CREDENTIALS, TTS MISSING, BHOJPURI MISSING)**.

---

## 7. Requirement 6 — Application, RTI & Grievance Assistance

### Inspection: Application, RTI, and Grievance Pages & PDF Generators
1. **Draft Preparation**:
   - Citizen can select a scheme, review required documents, check off prepared papers, and save drafts.
   - Citizen can draft RTI requests with 30-day timeline guidance.
   - Citizen can draft public grievance representations with previous complaint token references.
2. **PDF Generation**:
   - Verified ReportLab PDF generators in [`backend/app/services/documents/pdf_generator.py`](file:///C:/Users/SHIVAY%20AGARWAL/Desktop/JANSAHAYAK/backend/app/services/documents/pdf_generator.py).
   - Generates clean, professional citizen dossiers with watermarks and official portal links.
3. **Multi-Tenant Isolation**:
   - Verified across database queries: User A cannot read, edit, or download User B's drafts.
4. **Disclaimers**:
   - Prominently states that generating a kit or petition is for citizen preparation and does not constitute official submission to government portals.
5. **Gaps Identified**:
   - **No Conversational Auto-Prefill**: Details collected during an AI chat or eligibility assessment do not flow into the application or RTI forms. The citizen must re-enter their details manually.
   - **Templates are Static**: RTI and Grievance drafts use static starter text rather than LLM-customized legal representations tailored to the citizen's specific grievance narrative.
6. **Status**: **PARTIALLY IMPLEMENTED (MANUAL FORM DRIVEN)**.

---

## 8. Requirement 7 — WhatsApp Integration

### Codebase Audit
- Search for `whatsapp`, `meta`, `twilio`, `webhook`, `phone_number_id`:
  - Found only 1 documentation reference in `docs/api-integrations.md`: *"Meta WhatsApp Cloud API (Optional Future Channel) ... Kept disabled by default"*.
- **Backend**: Zero routers, zero webhooks, zero message verification handlers (`hub.verify_token`, `hub.challenge`), and zero WhatsApp message sending logic.
- **Frontend**: Zero WhatsApp integration components.
- **Status**: **NOT IMPLEMENTED**.

---

## 9. End-to-End Integration Journey Audit

Testing the 11-step journey outlined in the original SIH Vision:

| Step | Vision Milestone | Actual Implementation State | Status | Evidence |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Citizen speaks or types vernacular query | Web chat accepts typing; mic uses browser Web Speech (Hindi/English) | **PARTIAL** | Tested in `AssistantPage.tsx` |
| **2** | System understands regional language | No language detector; regex token search only; fails on complex dialect | **FAIL** | Bhojpuri benchmark returned PMMVY |
| **3** | Citizen facts extracted into structured fields | No slot-filling or entity extractor exists in assistant pipeline | **NOT IMPLEMENTED** | Chat input treated as unstructured string |
| **4** | System asks follow-up questions for missing facts | Chat is single-turn retrieval; does not prompt for missing income/land | **NOT IMPLEMENTED** | No multi-turn state machine |
| **5** | Official scheme evidence retrieved | Keyword search over 8 curated scheme summaries in PostgreSQL | **PARTIAL** | `retrieve_grounded_passages()` in `retrieval.py` |
| **6** | Eligibility rules evaluated | Evaluated only if user manually visits `/eligibility` form | **PARTIAL** | Decoupled from chat interface |
| **7** | Outcome explained with source citations | Eligibility report and chat both link to official government portal URLs | **PASS** | Citation pills rendered in UI |
| **8** | Citizen chooses a scheme | Citizen can click "Prepare Application" from scheme detail or catalogue | **PASS** | Navigates to `/applications?scheme=slug` |
| **9** | Application draft populated | Scheme is preselected, but citizen facts are not carried over from chat | **PARTIAL** | User re-enters applicant name/notes |
| **10** | Citizen reviews & downloads draft | Reviewable checklist, saves to PostgreSQL, downloads ReportLab PDF | **PASS** | Valid `%PDF-1.4` binary generated |
| **11** | RTI or Grievance draft created | Structured templates available, editable, saved to DB, PDF export | **PASS** | Valid `%PDF-1.4` petition generated |

**Overall E2E Journey Verdict**: **PARTIAL (DISCONNECTED ISLANDS)**.  
The platform has a functional Scheme Directory, Eligibility Engine, Application Prep tool, RTI Drafter, Grievance Drafter, and RAG Chat Assistant. However, they currently operate as **separate, independent modules** rather than a unified conversational journey.

---

## 10. Prioritized Implementation Roadmap

### Phase P0: Correctness, Security & Data Foundations (Immediate)
1. **Conversational Land & Currency Normalizer**:
   - Add unit conversion utility for regional Indian land measurements:
     - `1 Bigha (Bihar) = 0.62 acres`
     - `1 Bigha (UP West) = 0.20 acres`
     - `1 Bigha (UP East) = 0.67 acres`
     - `1 Bigha (Assam/Bengal) = 0.33 acres`
     - `1 Katha = 0.031 acres`
     - `1 Guntha = 0.025 acres`
   - Add currency parser normalizing `lakh`, `crore`, `k` into standard integer values (`₹1.5 lakh` -> `150,000`).
2. **Prevent Negative Keyword Retrieval**:
   - Improve `retrieval.py` to stop matching stop-words like "two", "three", "which", "qualify" that cause maternity schemes to be returned for male farmers.

---

### Phase P1: Core AI, Real RAG & Conversational Eligibility (High Priority)
1. **Activate Groq LLM in Production**:
   - Configure `GROQ_API_KEY` on Render to transition the assistant from static synthesis fallback to dynamic reasoning.
2. **Conversational Entity Extraction**:
   - Use LLM structured JSON output (`pydantic` schema) to parse conversational text into a structured `CitizenProfile` (`age`, `gender`, `occupation`, `state`, `land_acres`, `income`).
3. **Bridge Chat Assistant Directly to Eligibility Engine**:
   - Once structured facts are extracted from chat, automatically pass them to `evaluate_scheme_eligibility()` and present the evaluated eligibility card directly inside the chat window.
4. **Interactive Follow-Up Slot Filling**:
   - If `engine.py` reports `unknown_conditions`, prompt the LLM to ask targeted follow-up questions (e.g. *"To confirm if you qualify for PM-KISAN, is the land registered in your name?"*).
5. **Government Document Ingestion Pipeline**:
   - Store official scheme guideline PDFs in an object repository.
   - Implement PDF chunking and semantic vector retrieval (using pgvector on Neon or ChromaDB) to supplement keyword search.

---

### Phase P2: Multilingual Voice & Cross-Module Auto-Fill (Medium Priority)
1. **Activate Bhashini Credentials**:
   - Obtain official `BHASHINI_USER_ID` and `BHASHINI_API_KEY` from Digital India.
   - Wire backend `/api/voice/stt` and `/api/voice/translate` into the frontend voice input.
2. **Add Text-to-Speech (TTS)**:
   - Implement TTS synthesis so rural or illiterate citizens can listen to the eligibility explanation spoken aloud in their regional language.
3. **Add Bhojpuri and Regional Dialects**:
   - Map Bhojpuri queries to Hindi ASR/NMT models where native Bhojpuri engines are unavailable, preserving semantic intent.
4. **Cross-Module Context Bridge**:
   - Automatically carry forward citizen profile facts from the chat/eligibility session into `/applications`, `/rti`, and `/grievances` so citizens never have to re-type their information.

---

### Phase P3: Omnichannel Access (WhatsApp Bot) (Future Extension)
1. **Meta WhatsApp Cloud API Webhook**:
   - Implement `/api/whatsapp/webhook` with `hub.verify_token` challenge.
   - Handle incoming text and audio voice notes (`.ogg` audio).
   - Route WhatsApp audio through Bhashini ASR -> Groq RAG -> WhatsApp reply.
