# JanSahayak Security and Privacy Charter

## 1. Privacy by Design Commitments

1. **No Sensitive Identifiers Required**:
   - JanSahayak **never** asks for, records, or stores Aadhaar numbers, biometric data, bank account numbers, or debit/credit card PINs.
   - Eligibility checks only ask for abstract qualifying parameters (e.g., age bracket, state, general income range, landholding status).

2. **Citizen Data Isolation**:
   - Every database query for saved schemes, application drafts, RTI petitions, or grievance drafts is scoped strictly to `current_user.id`.
   - Citizens can never view, mutate, or delete another citizen's records.

3. **Data Minimization & Deletion Rights**:
   - Citizens have full control to view all their saved records and delete individual drafts or request complete account deletion at any time.

4. **Zero AI Training on Citizen Documents**:
   - Citizen inputs are processed ephemerally for eligibility evaluation or LLM synthesis and are never used to train third-party AI models.

---

## 2. Technical Security Safeguards

1. **Password Hashing**:
   - Passwords are securely hashed using PBKDF2 with SHA-256 (or bcrypt), utilizing unique per-user cryptographic salts and thousands of iterations.
   - Plaintext passwords are never logged, stored, or returned in any API response.

2. **Session & Token Management**:
   - Secure JWT tokens containing user ID, role, and expiration timestamp.
   - Supported via `Authorization: Bearer <token>` headers as well as HTTP-only cookies where applicable.

3. **Input Validation & Sanitization**:
   - Strict Pydantic V2 schemas for every backend route.
   - Frontend validation using Zod and React Hook Form.
   - SQL queries are executed exclusively through SQLAlchemy parameterized queries, preventing SQL injection vulnerabilities.

4. **CORS & Origin Protections**:
   - Configurable origins via `FRONTEND_ORIGIN` environment variable.
   - Prevents unauthorized cross-origin requests in production.

5. **Defense Against Prompt Injection**:
   - In RAG workflows, retrieved government document text is treated as untrusted data.
   - Strict system prompt fencing prevents document text from altering the assistant's instructions or revealing internal system configurations.
