# JanSahayak API Integrations & External Services Guide

This document explains every external service used or supported by JanSahayak, its purpose, cost tiers, configuration requirements, and fallback mechanisms.

---

## 1. Groq Cloud (Language Model Provider)

### What it does
Provides ultra-low latency LLM inference using open models (e.g., `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) to synthesize clear, citizen-friendly explanations grounded in verified government scheme passages.

### Why JanSahayak needs it
Enables conversational assistance and answers to complex citizen questions in natural language, citing exact verified source paragraphs.

### Account & Credentials
- **Where to create account**: [https://console.groq.com](https://console.groq.com)
- **Where to obtain key**: API Keys section in Groq Console.
- **Environment Variable**: `GROQ_API_KEY` (Backend only, NEVER expose to frontend).
- **Free Tier**: Free tier available with generous rate limits (TPM/RPM) suitable for standard usage.

### Fallback Behavior
If `GROQ_API_KEY` is not provided or the service is temporarily unreachable:
- JanSahayak does **not** crash or fabricate an answer.
- The assistant falls back to deterministic scheme keyword search and directly returns the verified scheme summary, official eligibility points, and clickable government links.
- An alert is displayed indicating that the assistant is operating in standard mode.

---

## 2. Bhashini (Government of India AI Language Platform)

### What it does
National Language Translation Mission (NLTM) initiative under MeitY providing:
1. **ASR (Speech-to-Text)**: Converts Indian regional language audio into text.
2. **NMT (Machine Translation)**: Translates text across 22 scheduled Indian languages.
3. **TTS (Text-to-Speech)**: Synthesizes natural sounding speech in regional languages.

### Why JanSahayak needs it
Eliminates the linguistic and digital literacy barrier for rural citizens and non-English/Hindi speakers.

### Account & Credentials
- **Where to register**: [https://bhashini.gov.in](https://bhashini.gov.in) (ULCA / Bhashini Ecosystem)
- **Environment Variables**:
  - `BHASHINI_USER_ID`
  - `BHASHINI_API_KEY`
  - `BHASHINI_PIPELINE_ENDPOINT`
- **Pricing**: Free for civic, research, and approved government ecosystem applications; request-based access for developers.

### Fallback Behavior
- When credentials are not yet entered, the UI transparently shows the Bhashini service status as `Awaiting Configuration`.
- Browser-native Web Speech API (`webkitSpeechRecognition` / `SpeechSynthesis`) is available as an instant client-side fallback where supported.
- Typing in any language is always supported as the primary reliable mode.

---

## 3. Neon PostgreSQL (Serverless Database)

### What it does
Serverless PostgreSQL database with support for standard SQL, full-text search, and `pgvector` for semantic document embeddings.

### Account & Credentials
- **Where to create account**: [https://neon.tech](https://neon.tech)
- **Where to obtain key**: Connection Details in the Neon Dashboard (`postgresql://user:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require`).
- **Environment Variable**: `DATABASE_URL` (Backend only).
- **Free Tier**: Free tier includes 0.5 GB storage, serverless autoscaling down to zero.

### Fallback Behavior
- In local development or during unit testing, if `DATABASE_URL` is unset or points to `sqlite:///./jansahayak.db`, the application smoothly initializes an embedded SQLite database with identical schema mappings.

---

## 4. Meta WhatsApp Cloud API (Optional Future Channel)

### What it does
Provides conversational WhatsApp access for citizens to check scheme eligibility on feature phones or basic smartphones without opening a web browser.

### Configuration
- Documented and preserved for Phase 9 after web application stability is confirmed.
- Kept disabled by default until WhatsApp Business Account and Meta developer credentials are provided.
