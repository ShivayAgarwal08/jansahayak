# JanSahayak Data Verification & Scheme Provenance

## 1. Principles of Truth and Provenance

JanSahayak enforces a strict policy against synthetic, fabricated, or unverified welfare information.
Every scheme stored and presented in JanSahayak must satisfy:
1. **Official Authority**: Issued by an authorized Central Ministry, State Department, or Statutory Welfare Board.
2. **Traceable URLs**: The scheme must link directly to an active `.gov.in`, `.nic.in`, or designated state government portal.
3. **Verification Timestamp**: The exact date when the scheme guidelines, eligibility rules, and application links were verified.
4. **Separation of Verified vs. Draft Data**: No unverified or experimental record can be labeled as verified.

---

## 2. Initial Verified Seed Schemes Catalogue

| Scheme Name | Ministry / Department | Scope | Official Portal | Verification Date |
| :--- | :--- | :--- | :--- | :--- |
| **PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)** | Ministry of Agriculture & Farmers Welfare | Central | [pmkisan.gov.in](https://pmkisan.gov.in) | 2026-03-01 |
| **PMAY-G (Pradhan Mantri Awaas Yojana - Gramin)** | Ministry of Rural Development | Central | [pmayg.nic.in](https://pmayg.nic.in) | 2026-03-01 |
| **Ayushman Bharat (PM-JAY)** | National Health Authority (MoHFW) | Central / States | [pmjay.gov.in](https://pmjay.gov.in) | 2026-03-01 |
| **PMMVY (Pradhan Mantri Matru Vandana Yojana)** | Ministry of Women & Child Development | Central | [pmmvy.wcd.gov.in](https://pmmvy.wcd.gov.in) | 2026-03-01 |
| **IGNOAPS (National Old Age Pension Scheme)** | Ministry of Rural Development | Central / States | [nsap.nic.in](https://nsap.nic.in) | 2026-03-01 |
| **Sukanya Samriddhi Yojana (SSY)** | Ministry of Finance / Women & Child | Central | [indiapost.gov.in](https://www.indiapost.gov.in) | 2026-03-01 |
| **PM SVANidhi (Street Vendor's AtmaNirbhar Nidhi)** | Ministry of Housing and Urban Affairs | Central | [pmsvanidhi.mohua.gov.in](https://pmsvanidhi.mohua.gov.in) | 2026-03-01 |
| **PM Vishwakarma Yojana** | Ministry of Micro, Small & Medium Enterprises | Central | [pmvishwakarma.gov.in](https://pmvishwakarma.gov.in) | 2026-03-01 |

---

## 3. Scheme Record Schema Structure

Every scheme record in the database maintains:
- `slug`: Human-readable unique identifier (e.g., `pm-kisan`).
- `name`: Official title in English and regional scripts.
- `summary`: Plain-language description avoiding bureaucratic jargon.
- `department`: Official issuing department.
- `scope`: `central` or `state`.
- `applicable_states`: Array of supported states (`["ALL"]` or specific state names).
- `beneficiary_types`: Target categories (e.g., `farmers`, `women`, `senior_citizens`, `students`, `artisans`).
- `benefits_summary`: Concrete financial, physical, or insurance benefits.
- `eligibility_criteria`: Structured rule objects evaluated by the deterministic engine.
- `exclusions`: Specific disqualifying factors (e.g., institutional landholders, income tax payees).
- `required_documents`: Mandatory documents and verified acceptable alternatives.
- `application_steps`: Clear procedural steps for submission.
- `official_portal_url`: Genuine government application/tracking portal.
- `verification_status`: `verified`, `under_review`, or `deprecated`.
- `last_verified_at`: ISO timestamp.
