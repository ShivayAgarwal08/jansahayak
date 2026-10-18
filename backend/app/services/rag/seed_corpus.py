import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.document import KnowledgeDocument
from app.services.rag.ingestion import ingest_document

logger = logging.getLogger("jansahayak.rag.seed")

OFFICIAL_SCHEME_DOCUMENTS = [
    {
        "scheme_slug": "pm-kisan",
        "title": "PM-KISAN Operational Guidelines & Revised Scheme Document",
        "source_url": "https://pmkisan.gov.in/Documents_New/Revised_Operational_Guidelines_PM_KISAN.pdf",
        "authority": "Ministry of Agriculture and Farmers Welfare, Govt of India",
        "document_reference": "Order No. 1-1/2019-Credit-I",
        "doc_type": "pdf",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. OBJECTIVE & SCOPE OF PM-KISAN
The Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a Central Sector scheme with 100% funding from the Government of India. The scheme aims to augment the financial needs of all landholding farmer families across the country in procuring various inputs to ensure proper crop health and appropriate yields, commensurate with the anticipated farm income.
Under the revised scheme guidelines effective from 01-04-2019, the operational ambit of the scheme has been expanded to cover all landholding farmer families in the country irrespective of the size of their land holdings, subject to the prevailing exclusion criteria.
A 'Farmer Family' is defined as a family consisting of husband, wife, and minor children who own cultivable land as per the land records of the concerned State/UT."""
            ),
            (
                2,
                """2. FINANCIAL BENEFIT STRUCTURE & DIRECT BENEFIT TRANSFER
Under the PM-KISAN scheme, an income support of ₹6,000 per financial year is provided to all eligible landholding farmer families across the country. The financial benefit is payable in three equal four-monthly installments of ₹2,000 each:
- Period 1: April to July
- Period 2: August to November
- Period 3: December to March

The financial benefit is transferred directly into the bank accounts of the eligible beneficiaries through the Direct Benefit Transfer (DBT) mechanism. To prevent leakage and duplication, Aadhaar seeding of bank accounts is strictly mandatory. State/UT Governments are responsible for identifying eligible farmer families based on land revenue records."""
            ),
            (
                3,
                """3. EXCLUSION CRITERIA (MANDATORY INELIGIBILITY CONDITIONS)
The following categories of beneficiaries of higher economic status are strictly NOT eligible for benefit under the PM-KISAN scheme:
(a) All Institutional Landholders.
(b) Farmer families in which one or more of its members belong to following categories:
    i. Former and present holders of constitutional posts (Ministers, MPs, MLAs, MLCs, Mayors, Chairpersons of District Panchayats).
    ii. Former and present officers and employees of Central/State Government Ministries, Departments, and Public Sector Undertakings (PSUs), excluding Multi-Tasking Staff (MTS), Class IV, and Group D employees.
    iii. All superannuated/retired pensioners whose monthly pension is ₹10,000 or more (excluding MTS / Class IV / Group D).
    iv. All persons who paid Income Tax in the last assessment year.
    v. Professionals like Doctors, Engineers, Lawyers, Chartered Accountants, and Architects registered with professional bodies and carrying out active practice."""
            ),
            (
                4,
                """4. VERIFICATION, REVENUE RECORDS & GRIEVANCE REDRESSAL
Eligible farmers must provide:
1. Aadhaar Card (mandatory for identity verification).
2. Land ownership documents (Khatauni, Record of Rights - RoR, Patta, or registered title deed).
3. Active bank account details (IFSC and Account Number linked with Aadhaar).
4. Active mobile number for transaction notifications.

Farmers can register online via the PM-KISAN portal (https://pmkisan.gov.in) under 'Farmers Corner' or visit the nearest Common Service Centre (CSC). The State Nodal Officer and District Revenue Authorities verify land records. Grievances regarding non-credit of installments can be lodged via the PM-KISAN Helpdesk or State Portal."""
            )
        ]
    },
    {
        "scheme_slug": "pmay-g",
        "title": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G) Operational Guidelines",
        "source_url": "https://pmayg.nic.in/netiay/Pmay-G-Guidelines-En.pdf",
        "authority": "Ministry of Rural Development, Govt of India",
        "document_reference": "MoRD Notification No. J-11060/01/2016-RH",
        "doc_type": "pdf",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. INTRODUCTION & BENEFICIARY IDENTIFICATION UNDER PMAY-G
Pradhan Mantri Awas Yojana - Gramin (PMAY-G) aims to provide a pucca house with basic amenities to all houseless households and households living in kutcha or dilapidated houses in rural areas.
Beneficiary identification is strictly based on the housing deprivation parameters recorded in the Socio-Economic and Caste Census (SECC) 2011, validated by the Gram Sabha. Priority is given to households with zero-room, one-room, or two-room kutcha walls and kutcha roofs."""
            ),
            (
                2,
                """2. FINANCIAL ASSISTANCE & CONVERGENCE AMENITIES
Under PMAY-G, the unit assistance provided for construction of a pucca house is:
- ₹1,20,000 per unit in plain areas.
- ₹1,30,000 per unit in hilly states (North-Eastern States, Himachal Pradesh, Uttarakhand, Jammu & Kashmir, Ladakh) and Integrated Action Plan (IAP) districts.

In addition to the unit assistance:
- Beneficiary is entitled to 90 person-days (plain areas) or 95 person-days (hilly areas) of unskilled labor wages under MGNREGA (~₹18,000 to ₹25,000).
- Financial assistance of ₹12,000 for toilet construction through convergence with Swachh Bharat Mission - Gramin (SBM-G).
- Piped drinking water connection through Jal Jeevan Mission and electricity connection under Saubhagya."""
            ),
            (
                3,
                """3. EXCLUSION CRITERIA (13 AUTOMATIC EXCLUSION PARAMETERS)
A rural household having any of the following 13 assets or conditions is automatically EXCLUDED from PMAY-G assistance:
1. Motorized two-wheeler, three-wheeler, four-wheeler, or motorized fishing boat.
2. Mechanized three-wheeler or four-wheeler agricultural equipment.
3. Kisan Credit Card (KCC) with credit limit of ₹50,000 or above.
4. Household member who is a regular government employee.
5. Household with non-agricultural enterprises registered with the government.
6. Any member of the household earning more than ₹15,000 per month (revised Awas+ criteria).
7. Household paying income tax or professional tax.
8. Owning 2.5 acres or more of irrigated land with at least one irrigation equipment.
9. Owning 5 acres or more of un-irrigated land."""
            )
        ]
    },
    {
        "scheme_slug": "ayushman-bharat-pmjay",
        "title": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana Guidelines",
        "source_url": "https://pmjay.gov.in",
        "authority": "National Health Authority, Ministry of Health and Family Welfare",
        "document_reference": "NHA OM No. S.12019/02/2018-NHA",
        "doc_type": "guidelines",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. OVERVIEW & CASHLESS HOSPITALIZATION BENEFIT
Ayushman Bharat - PM-JAY is the world's largest government-funded health assurance scheme. It provides a health cover of ₹5,00,000 per family per year for secondary and tertiary care hospitalization across public and empanelled private hospitals in India.
Key features:
- Cashless and paperless treatment at the point of care.
- No restrictions on family size, age, or gender.
- Pre-existing conditions are covered from day one.
- Covers pre-hospitalization expenses up to 3 days and post-hospitalization expenses up to 15 days, including diagnostic tests and medicines."""
            ),
            (
                2,
                """2. UNIVERSAL SENIOR CITIZEN (AGE 70+) HEALTH PATHWAY
Under the landmark cabinet expansion in 2024, ALL senior citizens aged 70 years and above are eligible for health insurance coverage under PM-JAY, regardless of their family's economic status, annual income, or caste category.
- Seniors aged 70+ receive a distinct Ayushman Vay Vandana Card.
- An additional top-up cover of ₹5,00,000 per year is provided exclusively for the senior citizen(s) in the family.
- Senior citizens already covered under central government health schemes (such as CGHS, ECHS, or Ayushman CAPF) have the option to either retain their existing scheme or opt for PM-JAY."""
            ),
            (
                3,
                """3. EXCLUSIONS & NON-ELIGIBLE CATEGORIES
1. Families not meeting SECC deprivation criteria (D1 to D7) or NFSA ration card categories, unless qualifying under the age 70+ senior citizen universal pathway.
2. Beneficiaries already enrolled in and actively receiving comprehensive benefits from another central/state contributory government health insurance scheme (CGHS, ESI, Armed Forces Medical Services). Dual enrollment is not permitted."""
            )
        ]
    },
    {
        "scheme_slug": "pmmvy",
        "title": "Pradhan Mantri Matru Vandana Yojana (PMMVY) Operational Guidelines",
        "source_url": "https://pmmvy.wcd.gov.in",
        "authority": "Ministry of Women and Child Development, Govt of India",
        "document_reference": "MWCD Order No. 11-12/2021-PMMVY",
        "doc_type": "guidelines",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. OBJECTIVE & MATERNITY BENEFIT SCHEDULE
PMMVY is a conditional cash transfer scheme for pregnant women and lactating mothers (PW&LM). It provides partial compensation for wage loss in terms of cash incentives so that the mother can take adequate rest before and after delivery of the child.
Benefit structure:
- For the First Living Child: Total incentive of ₹5,000 provided in two installments:
  * Installment 1: ₹3,000 on registration of pregnancy and at least one Antenatal Check-up (ANC) within 6 months.
  * Installment 2: ₹2,000 after child birth registration and completion of first cycle of child vaccination.
- For the Second Child (Girl Child Incentive): Incentive of ₹6,000 in a single installment post-birth to deter female foeticide and promote the girl child."""
            ),
            (
                2,
                """2. ELIGIBILITY CRITERIA & EXCLUSIONS
Eligibility:
- Pregnant Women and Lactating Mothers who have conceived their first or second child.
- Age of the mother must be 19 years or above at the time of conception/LMP.

Exclusions:
- Women who are in regular employment with the Central Government, State Governments, or Public Sector Undertakings (PSUs).
- Women who are in receipt of similar maternity benefits under any other statutory law (such as the Maternity Benefit Act, 1961)."""
            )
        ]
    },
    {
        "scheme_slug": "ignoaps",
        "title": "National Social Assistance Programme (NSAP) Guidelines - IGNOAPS",
        "source_url": "https://nsap.nic.in",
        "authority": "Ministry of Rural Development, Govt of India",
        "document_reference": "MoRD NSAP Guidelines Section 2.1",
        "doc_type": "guidelines",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. INDIRA GANDHI NATIONAL OLD AGE PENSION SCHEME (IGNOAPS)
IGNOAPS is a non-contributory pension scheme under the National Social Assistance Programme (NSAP) providing social security to vulnerable elderly persons living Below the Poverty Line (BPL).

Eligibility Criteria:
1. Age: The applicant must be 60 years of age or older.
2. Poverty Status: The applicant must belong to a household living Below the Poverty Line (BPL) as verified by the State/UT government.

Pension Amounts:
- For persons aged 60 to 79 years: Central assistance of ₹200 per month (States add a matching or higher state contribution, typically totaling ₹500 to ₹1,500/month).
- For persons aged 80 years and above: Central assistance of ₹500 per month (total pension typically ₹1,000 to ₹2,500/month with state top-up)."""
            )
        ]
    },
    {
        "scheme_slug": "sukanya-samriddhi-yojana",
        "title": "Sukanya Samriddhi Account Rules, 2019",
        "source_url": "https://www.indiapost.gov.in",
        "authority": "Department of Economic Affairs, Ministry of Finance",
        "document_reference": "GSR 914(E), Gazette of India",
        "doc_type": "guidelines",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. SUKANYA SAMRIDDHI YOJANA (SSY) RULES & DEPOSIT TERMS
Sukanya Samriddhi Account is a dedicated small savings scheme backed by the Government of India as part of the 'Beti Bachao Beti Padhao' campaign.
Key Rules:
- Age Eligibility: The account can be opened by the natural or legal guardian in the name of a girl child from her birth up to the age of 10 years.
- Limit on Accounts: Only one account is permitted per girl child, and a maximum of two accounts per family (three permitted in case of twins/triplets in first or second birth).
- Deposit Amounts: Minimum deposit of ₹250 per financial year; maximum deposit of ₹1,50,000 per financial year.
- High Interest Rate & Tax Exemption: Offers attractive sovereign-backed interest rate with triple tax exemption (EEE) under Section 80C of the Income Tax Act."""
            )
        ]
    },
    {
        "scheme_slug": "pm-svanidhi",
        "title": "PM Street Vendor's AtmaNirbhar Nidhi Scheme Guidelines",
        "source_url": "https://pmsvanidhi.mohua.gov.in",
        "authority": "Ministry of Housing and Urban Affairs, Govt of India",
        "document_reference": "MoHUA Guidelines No. K-12015/01/2020-UPA-II",
        "doc_type": "guidelines",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. PM SVANIDHI - SPECIAL MICRO-CREDIT FACILITY FOR STREET VENDORS
PM SVANidhi is a Central Sector scheme launched to facilitate working capital loans to urban street vendors, hawkers, and thelawalas to restart their livelihoods.

Credit Tranches:
1. First Tranche: Collateral-free working capital loan up to ₹10,000 repayable in 1-year monthly installments.
2. Second Tranche: Up to ₹20,000 on timely repayment of the first loan.
3. Third Tranche: Up to ₹50,000 on timely repayment of the second loan.

Incentives:
- Interest Subsidy: An interest subsidy of 7% per annum is credited directly into the vendor's bank account on timely repayment.
- Digital Cashback: Monthly cashback up to ₹100 for conducting digital transactions (QR code receipts)."""
            )
        ]
    },
    {
        "scheme_slug": "pm-vishwakarma",
        "title": "PM Vishwakarma Central Sector Scheme Guidelines",
        "source_url": "https://pmvishwakarma.gov.in",
        "authority": "Ministry of Micro, Small & Medium Enterprises, Govt of India",
        "document_reference": "MSME Notification No. 1/1(1)/2023-P&G",
        "doc_type": "guidelines",
        "ocr_status": "not_needed",
        "pages": [
            (
                1,
                """1. PM VISHWAKARMA SCHEME - SCOPE, TRADES & BENEFITS
PM Vishwakarma is designed to provide holistic support to traditional artisans and craftspersons who work with their hands and traditional tools.

Eligible 18 Traditional Trades:
Carpenter (Suthar), Boat Maker, Armourer, Blacksmith (Lohar), Hammer & Tool Kit Maker, Locksmith, Sculptor (Moortikar/Stone Carver), Goldsmith (Sonar), Potter (Kumhaar), Cobbler (Charmakar), Mason (Rajmistri), Basket/Mat/Broom Maker, Doll & Toy Maker, Barber (Naai), Garland Maker (Malakaar), Washerman (Dhobi), Tailor (Darzi), Fishing Net Maker.

Scheme Benefits:
- PM Vishwakarma Certificate and ID Card.
- Skill Upgradation: 5-7 days Basic Training with ₹500 per day stipend.
- Modern Toolkit Incentive: Grant of ₹15,000 in electronic vouchers for acquiring modern quality tools.
- Enterprise Credit: Collateral-free enterprise development loans up to ₹3,00,000 in two tranches (₹1,00,000 first tranche, ₹2,00,000 second tranche) at a concessional interest rate of 5%."""
            )
        ]
    }
]

def seed_official_documents_corpus(db: Session) -> Dict[str, Any]:
    """
    Seed the official government scheme document corpus into KnowledgeDocument and DocumentChunk tables.
    Fully idempotent: inspects each document individually to prevent duplicate records or chunks
    on restarts, redeployments, or partial initial states.
    """
    from app.models.scheme import Scheme
    ingested_count = 0
    total_chunks = 0
    skipped_count = 0

    for doc_data in OFFICIAL_SCHEME_DOCUMENTS:
        scheme = db.query(Scheme).filter(Scheme.slug == doc_data["scheme_slug"]).first()
        if not scheme:
            logger.warning(f"Scheme with slug '{doc_data['scheme_slug']}' not found in database. Skipping document.")
            continue

        existing_doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.scheme_id == scheme.id,
            KnowledgeDocument.source_url == doc_data["source_url"]
        ).first()

        if existing_doc and len(existing_doc.chunks) > 0:
            skipped_count += 1
            continue

        res = ingest_document(
            db=db,
            scheme_slug=doc_data["scheme_slug"],
            title=doc_data["title"],
            source_url=doc_data["source_url"],
            authority=doc_data["authority"],
            document_reference=doc_data.get("document_reference"),
            doc_type=doc_data.get("doc_type", "guidelines"),
            pages=doc_data.get("pages"),
            ocr_status=doc_data.get("ocr_status", "not_needed")
        )
        ingested_count += 1
        total_chunks += res.get("chunks_count", 0)

    logger.info(f"Official corpus seeding complete: {ingested_count} ingested, {skipped_count} skipped, {total_chunks} chunks.")
    return {
        "status": "completed",
        "documents_ingested": ingested_count,
        "documents_skipped": skipped_count,
        "chunks_created": total_chunks
    }
