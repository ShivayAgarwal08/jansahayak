from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.scheme import Scheme, SchemeSource
from app.models.user import User
from app.core.security import hash_password

VERIFIED_SCHEMES = [
    {
        "slug": "pm-kisan",
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "name_hi": "प्रधानमंत्री किसान सम्मान निधि (पीएम-किसान)",
        "summary": "Income support scheme providing ₹6,000 annually in three equal four-monthly installments directly into the bank accounts of all landholding farmer families.",
        "summary_hi": "सभी भूमिधारक किसान परिवारों के बैंक खातों में सीधे ₹6,000 प्रति वर्ष तीन समान किस्तों में प्रदान करने वाली आय सहायता योजना।",
        "department": "Department of Agriculture & Farmers Welfare",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "agriculture",
        "beneficiary_types": ["farmers", "small_marginal_farmers"],
        "benefits_summary": "₹6,000 per financial year in three equal installments of ₹2,000 directly transferred via Aadhaar-seeded bank account.",
        "eligibility_rules": {
            "min_age": 18,
            "occupation": ["farmer", "agriculture"],
            "landholding_required": True,
            "max_landholding_acres": None,  # Extended to all landholding farmers
            "income_tax_payer": False,
            "is_govt_employee": False
        },
        "exclusions": [
            "Institutional landholders",
            "Farmer families holding constitutional posts (former/present)",
            "Former and present Ministers, MPs, MLAs, MLCs, Mayors, District Panchayat Chairpersons",
            "Serving or retired officers and employees of Central/State Govt Ministries/Offices/PSUs (excluding Multi-Tasking Staff / Class IV / Group D)",
            "Professionals like Doctors, Engineers, Lawyers, Chartered Accountants, and Architects",
            "All persons who paid Income Tax in the last assessment year",
            "Pensioners receiving monthly pension of ₹10,000 or more (excluding Class IV/Group D)"
        ],
        "required_documents": [
            {"name": "Aadhaar Card", "mandatory": True, "alternatives": []},
            {"name": "Land Ownership Record (Khatauni / RoR / Patta)", "mandatory": True, "alternatives": ["Land Title Deed", "Revenue Record Copy"]},
            {"name": "Bank Account Details (Aadhaar Seeded)", "mandatory": True, "alternatives": ["Cancelled Cheque", "Passbook Copy"]},
            {"name": "Active Mobile Number", "mandatory": True, "alternatives": []}
        ],
        "application_steps": [
            "Visit the official PM-KISAN portal (pmkisan.gov.in) or visit nearest Common Service Centre (CSC).",
            "Click on 'New Farmer Registration' under Farmers Corner.",
            "Enter Rural or Urban Farmer Registration, Aadhaar Number, and Mobile Number.",
            "Select State, District, Sub-District, Block, and Village.",
            "Enter land details (Survey/Khata No., Khasra No., Area in Hectares) and upload land record copy.",
            "Submit application. The state nodal officer verifies revenue records for final approval."
        ],
        "official_portal_url": "https://pmkisan.gov.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "PM-KISAN Operational Guidelines & Revised Scheme Document",
                "source_url": "https://pmkisan.gov.in/Documents_New/Revised_Operational_Guidelines_PM_KISAN.pdf",
                "issuing_authority": "Ministry of Agriculture and Farmers Welfare, Govt of India",
                "document_reference": "Order No. 1-1/2019-Credit-I"
            }
        ]
    },
    {
        "slug": "pmay-g",
        "name": "Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)",
        "name_hi": "प्रधानमंत्री आवास योजना - ग्रामीण (पीएमएवाई-जी)",
        "summary": "Flagship rural housing scheme providing financial grant to houseless families and those living in kutcha/dilapidated houses to construct a durable pucca house.",
        "summary_hi": "बेघर और कच्चे/जीर्ण-शीर्ण घरों में रहने वाले ग्रामीण परिवारों को पक्का मकान बनाने के लिए वित्तीय सहायता प्रदान करने वाली योजना।",
        "department": "Ministry of Rural Development",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "housing",
        "beneficiary_types": ["rural_households", "low_income", "sc_st", "women"],
        "benefits_summary": "₹1,20,000 financial assistance in plain areas; ₹1,30,000 in hilly/difficult/IAP areas, plus ₹18,000+ for 90-95 days unskilled labour under MGNREGS, and ₹12,000 for toilet construction under Swachh Bharat Mission.",
        "eligibility_rules": {
            "min_age": 18,
            "area_type": ["rural"],
            "housing_status": ["houseless", "kutcha_house", "dilapidated"],
            "owns_pucca_house": False,
            "owns_motorized_vehicle": False,
            "is_govt_employee": False
        },
        "exclusions": [
            "Households owning a pucca house anywhere in India",
            "Households owning motorized two/three/four-wheelers, fishing boats, or mechanized agricultural equipment",
            "Households with any member as a government employee",
            "Households paying Income Tax or Professional Tax",
            "Households possessing Kisan Credit Card with credit limit of ₹50,000 or above"
        ],
        "required_documents": [
            {"name": "Aadhaar Card of Applicant and Family Members", "mandatory": True, "alternatives": []},
            {"name": "MGNREGA Job Card Number", "mandatory": True, "alternatives": []},
            {"name": "Bank Account Details (Aadhaar linked)", "mandatory": True, "alternatives": ["Passbook"]},
            {"name": "Land/House Site Certificate", "mandatory": True, "alternatives": ["Panchayat Gram Sabha Certification"]}
        ],
        "application_steps": [
            "Beneficiary selection is done transparently through Gram Sabha based on SECC 2011 / Awaas+ list.",
            "Contact your Gram Panchayat Secretary or Block Development Office (BDO).",
            "Panchayat officials register eligible beneficiaries on the AwaasSoft portal.",
            "Geo-tagging of existing kutcha house / site is performed before first installment release.",
            "Funds are credited directly to beneficiary bank account in three inspection-linked stages."
        ],
        "official_portal_url": "https://pmayg.nic.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "PMAY-G Framework for Implementation",
                "source_url": "https://pmayg.nic.in/netiwas/uploaded/English_Book_Final.pdf",
                "issuing_authority": "Rural Housing Division, Ministry of Rural Development",
                "document_reference": "MoRD Notification G-20011/01/2015-RH"
            }
        ]
    },
    {
        "slug": "ayushman-bharat-pmjay",
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "name_hi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना (पीएम-जय)",
        "summary": "World's largest government-financed health assurance scheme providing up to ₹5 lakh per family per year for secondary and tertiary hospital care without cash payments.",
        "summary_hi": "प्रति परिवार प्रति वर्ष ₹5 लाख तक का कैशलेस स्वास्थ्य कवर प्रदान करने वाली देश की सबसे बड़ी स्वास्थ्य सुरक्षा योजना।",
        "department": "National Health Authority, Ministry of Health and Family Welfare",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "health",
        "beneficiary_types": ["low_income", "rural_households", "urban_workers", "senior_citizens"],
        "benefits_summary": "Cashless in-patient health cover up to ₹5,00,000 per family per year across 28,000+ empanelled hospitals covering 1,949 medical and surgical procedures. Universal coverage for all senior citizens aged 70+.",
        "eligibility_rules": {
            "secc_deprived_or_vulnerable": True,
            "senior_citizen_70_plus": True  # Special pathway: all 70+ citizens eligible regardless of income
        },
        "exclusions": [
            "Households holding government health insurance schemes (e.g. CGHS, ESI, Defence)",
            "Families owning mechanized four-wheelers or high-income urban brackets (except 70+ senior citizens who qualify under universal senior citizen expansion)"
        ],
        "required_documents": [
            {"name": "Aadhaar Card", "mandatory": True, "alternatives": []},
            {"name": "Ration Card / Family ID", "mandatory": True, "alternatives": ["PMAY/PM-JAY Beneficiary Letter", "PMJAY Family Card"]},
            {"name": "Active Mobile Number", "mandatory": True, "alternatives": []}
        ],
        "application_steps": [
            "Check eligibility on official portal (beneficiary.nha.gov.in) using Mobile number or Family ID.",
            "Visit any nearest Empanelled Health Care Provider (EHCP) or Ayushman Arogya Mandir or CSC.",
            "Meet the Pradhan Mantri Arogya Mitra (PMAM) at the Ayushman Helpdesk.",
            "Complete e-KYC using Aadhaar biometric authentication.",
            "Download your Ayushman PVC Card or digital Ayushman Card."
        ],
        "official_portal_url": "https://pmjay.gov.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "PM-JAY Guidelines on Beneficiary Identification and Hospital Empanelment",
                "source_url": "https://pmjay.gov.in/sites/default/files/2018-09/Guidelines_on_Process_of_Beneficiary_Identification.pdf",
                "issuing_authority": "National Health Authority, Govt of India",
                "document_reference": "NHA OM No. S-12012/12/2021-NHA"
            }
        ]
    },
    {
        "slug": "pmmvy",
        "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "name_hi": "प्रधानमंत्री मातृ वंदना योजना (पीएमएमवीवाई)",
        "summary": "Maternity benefit cash incentive program compensating for wage loss and encouraging health-seeking behavior during pregnancy and lactation.",
        "summary_hi": "गर्भवती और स्तनपान कराने वाली माताओं के लिए मातृत्व लाभ और पोषण सहायता योजना।",
        "department": "Ministry of Women and Child Development",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "women_children",
        "beneficiary_types": ["women", "mothers"],
        "benefits_summary": "₹5,000 for the first child (₹3,000 on registration & antenatal checkup, ₹2,000 after child birth & vaccination). Additional ₹6,000 in single installment if the second child is a girl child.",
        "eligibility_rules": {
            "min_age": 19,
            "gender": "female",
            "is_pregnant_or_lactating": True,
            "is_regular_govt_employee": False,
            "social_economic_category": ["sc_st", "bpl", "e-shram", "annual_income_under_8_lakh", "divyangjan"]
        },
        "exclusions": [
            "Women who are in regular employment with Central or State Government, Public Sector Undertakings (PSUs)",
            "Women who are in receipt of similar maternity benefits under any other statutory law"
        ],
        "required_documents": [
            {"name": "Mother and Child Protection (MCP) Card", "mandatory": True, "alternatives": []},
            {"name": "Aadhaar Card of Mother", "mandatory": True, "alternatives": []},
            {"name": "Bank Account Passbook (Aadhaar seeded)", "mandatory": True, "alternatives": []},
            {"name": "Proof of Social/Economic Category (E-Shram / Ration Card / Income Certificate)", "mandatory": True, "alternatives": ["SC/ST Certificate", "BPL Card"]}
        ],
        "application_steps": [
            "Register at the local Anganwadi Centre (AWC) or approved health facility within 570 days from LMP date.",
            "Fill Form 1-A (for first installment) with Anganwadi Worker (AWW) / ASHA.",
            "Submit MCP card showing at least one Antenatal Check-up (ANC).",
            "Fill Form 1-B after childbirth registration and primary vaccinations (BCG, OPV, DPT, Hepatitis B).",
            "Benefit amounts are transferred directly via DBT to beneficiary bank account."
        ],
        "official_portal_url": "https://pmmvy.wcd.gov.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "PMMVY Scheme Guidelines - Mission Shakti",
                "source_url": "https://wcd.nic.in/sites/default/files/PMMVY%20Scheme%20Guidelines.pdf",
                "issuing_authority": "Ministry of Women and Child Development, Govt of India",
                "document_reference": "WCD Notification No. 15-2/2021-PMMVY"
            }
        ]
    },
    {
        "slug": "ignoaps",
        "name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)",
        "name_hi": "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना (आईजीएनओएपीएस)",
        "summary": "Monthly social security pension for destitute senior citizens belonging to Below Poverty Line (BPL) households.",
        "summary_hi": "गरीबी रेखा से नीचे (बीपीएल) परिवारों के वरिष्ठ नागरिकों के लिए मासिक सामाजिक सुरक्षा पेंशन।",
        "department": "Department of Rural Development, Ministry of Rural Development",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "social_security",
        "beneficiary_types": ["senior_citizens", "low_income"],
        "benefits_summary": "Monthly pension of ₹200 (60–79 years) or ₹500 (80+ years) Central contribution, combined with state top-up providing total monthly pension ranging from ₹500 to ₹2,500 depending on state.",
        "eligibility_rules": {
            "min_age": 60,
            "bpl_household": True
        },
        "exclusions": [
            "Citizens whose household is not included in the verified BPL category",
            "Persons receiving pension from government or autonomous statutory retirement systems"
        ],
        "required_documents": [
            {"name": "Age Proof (Aadhaar / Voter ID / Birth Certificate)", "mandatory": True, "alternatives": ["School Leaving Certificate", "Medical Officer Age Certificate"]},
            {"name": "BPL Ration Card or BPL Certificate", "mandatory": True, "alternatives": ["SECC BPL Identification"]},
            {"name": "Bank / Post Office Savings Account Passbook", "mandatory": True, "alternatives": []},
            {"name": "Passport Size Photographs", "mandatory": True, "alternatives": []}
        ],
        "application_steps": [
            "Obtain Application Form from Block Development Office (BDO) / Municipal Office or NSAP portal (nsap.nic.in).",
            "Attach attested copies of age proof, BPL card, and bank passbook.",
            "Submit to Gram Panchayat Officer (rural) or Sub-Divisional Magistrate/Municipal Officer (urban).",
            "Verification conducted by Social Welfare Department / Revenue Inspector.",
            "Sanction order issued and monthly pension credited directly via DBT."
        ],
        "official_portal_url": "https://nsap.nic.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "National Social Assistance Programme (NSAP) Guidelines",
                "source_url": "https://nsap.nic.in/guidelines.html",
                "issuing_authority": "Ministry of Rural Development, Govt of India",
                "document_reference": "NSAP-MoRD Guidelines 2014 & Gaz. Notif."
            }
        ]
    },
    {
        "slug": "sukanya-samriddhi-yojana",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "name_hi": "सुकन्या समृद्धि योजना (एसएसवाई)",
        "summary": "Government-backed savings scheme for the girl child under 'Beti Bachao Beti Padhao', offering highest sovereign interest and triple tax benefits (EEE).",
        "summary_hi": "'बेटी बचाओ बेटी पढ़ाओ' अभियान के तहत बालिकाओं की उच्च शिक्षा और विवाह के लिए विशेष बचत योजना।",
        "department": "Department of Economic Affairs, Ministry of Finance",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "women_children",
        "beneficiary_types": ["students", "women", "children"],
        "benefits_summary": "8.2% annual interest compounded yearly. Tax exemption on deposit (Section 80C), tax-free interest, and tax-free maturity amount. Account matures after 21 years from opening date or on marriage after age 18.",
        "eligibility_rules": {
            "gender": "female",
            "max_age_years": 10,
            "max_accounts_per_family": 2  # Exception allowed for twins/triplets
        },
        "exclusions": [
            "Girl child older than 10 years at time of account opening",
            "Non-resident Indians (NRI) or if girl child loses Indian citizenship",
            "More than 2 accounts per family (except verified triplets/twins)"
        ],
        "required_documents": [
            {"name": "Birth Certificate of Girl Child", "mandatory": True, "alternatives": ["Hospital Discharge Summary with DoB"]},
            {"name": "Identity Proof of Parent / Legal Guardian (Aadhaar / Voter ID / PAN)", "mandatory": True, "alternatives": []},
            {"name": "Address Proof of Guardian", "mandatory": True, "alternatives": ["Electricity Bill", "Ration Card"]},
            {"name": "Passport Size Photographs", "mandatory": True, "alternatives": []}
        ],
        "application_steps": [
            "Visit nearest Post Office branch or authorized commercial bank (SBI, PNB, BoB, etc.).",
            "Collect Sukanya Samriddhi Account Opening Form (Form-1).",
            "Attach girl child birth certificate and guardian KYC documents.",
            "Deposit initial minimum opening amount (minimum ₹250, maximum ₹1,50,000 per year).",
            "Receive SSY Passbook recording account number and deposited balance."
        ],
        "official_portal_url": "https://www.indiapost.gov.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "Sukanya Samriddhi Account Rules, 2019",
                "source_url": "https://www.indiapost.gov.in/Financial/Pages/Content/Sukanya-Samriddhi-Account.aspx",
                "issuing_authority": "Ministry of Finance, Department of Economic Affairs",
                "document_reference": "G.S.R. 914(E) Gazette Notification"
            }
        ]
    },
    {
        "slug": "pm-svanidhi",
        "name": "PM SVANidhi (PM Street Vendor's AtmaNirbhar Nidhi)",
        "name_hi": "पीएम स्वनिधि (प्रधानमंत्री स्ट्रीट वेंडर्स आत्मनिर्भर निधि)",
        "summary": "Special micro-credit facility providing affordable collateral-free working capital loans to urban and peri-urban street vendors to resume and expand livelihoods.",
        "summary_hi": "शहरी और ग्रामीण सीमावर्ती रेहड़ी-पटरी और फेरी लगाने वाले स्ट्रीट वेंडरों के लिए सस्ती कार्यशील पूंजी ऋण योजना।",
        "department": "Ministry of Housing and Urban Affairs",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "employment",
        "beneficiary_types": ["urban_workers", "street_vendors", "low_income"],
        "benefits_summary": "1st loan up to ₹10,000 (12-month tenure), 2nd loan up to ₹20,000, 3rd loan up to ₹50,000. 7% per annum interest subsidy on timely repayment and up to ₹1,200 annual cashback on digital transactions.",
        "eligibility_rules": {
            "min_age": 18,
            "occupation": ["street_vendor", "hawker", "vendor"],
            "has_vending_certificate_or_lor": True
        },
        "exclusions": [
            "Individuals not engaged in vending activities prior to cutoff dates without Urban Local Body recommendation",
            "Willful defaulters under formal banking system"
        ],
        "required_documents": [
            {"name": "Certificate of Vending / ID Card issued by ULB", "mandatory": True, "alternatives": ["Letter of Recommendation (LoR) from Town Vending Committee"]},
            {"name": "Aadhaar Card", "mandatory": True, "alternatives": []},
            {"name": "Bank Account Details", "mandatory": True, "alternatives": []},
            {"name": "Active Mobile Number linked to Aadhaar", "mandatory": True, "alternatives": []}
        ],
        "application_steps": [
            "Check mobile registration on PMSVANidhi portal (pmsvanidhi.mohua.gov.in) or mobile app.",
            "Verify vending status using Urban Local Body (ULB) survey number or request Letter of Recommendation (LoR).",
            "Fill online loan application form selecting preferred lending institution (Lending Bank / NBFC / MFI).",
            "Upload KYC documents and submit.",
            "Lending institution verifies application and disburses loan directly to bank account within 10-15 working days."
        ],
        "official_portal_url": "https://pmsvanidhi.mohua.gov.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "PM SVANidhi Operational Guidelines",
                "source_url": "https://pmsvanidhi.mohua.gov.in/Schemes/SchemeGuideline",
                "issuing_authority": "Ministry of Housing and Urban Affairs, Govt of India",
                "document_reference": "MoHUA OM K-12019(11)/1/2020-UPA-II"
            }
        ]
    },
    {
        "slug": "pm-vishwakarma",
        "name": "PM Vishwakarma Scheme",
        "name_hi": "पीएम विश्वकर्मा योजना",
        "summary": "Holistic support scheme for traditional artisans and craftspeople providing recognition, skill training, toolkits, and collateral-free enterprise credit at concessional 5% interest.",
        "summary_hi": "पारंपरिक कारीगरों और दस्तकारों (विश्वकर्माओं) के कौशल, उपकरण और व्यवसाय विस्तार के लिए समग्र सहायता योजना।",
        "department": "Ministry of Micro, Small and Medium Enterprises",
        "scope": "central",
        "applicable_states": ["ALL"],
        "category": "employment",
        "beneficiary_types": ["artisans", "craftspeople", "workers"],
        "benefits_summary": "PM Vishwakarma Certificate & ID card, 5-7 days basic skill training with ₹500/day stipend, ₹15,000 modern toolkit incentive e-voucher, and collateral-free credit support up to ₹1,00,000 (1st tranche) and ₹2,00,000 (2nd tranche) at concessional 5% interest.",
        "eligibility_rules": {
            "min_age": 18,
            "occupation": [
                "carpenter", "blacksmith", "goldsmith", "potter", "sculptor", "cobbler", 
                "mason", "basket_maker", "doll_maker", "barber", "garland_maker", 
                "washerman", "tailor", "fishing_net_maker", "boat_builder", "armourer", "locksmith", "toolmaker"
            ],
            "family_members_benefitted": 0,
            "is_govt_employee": False
        },
        "exclusions": [
            "Persons who have availed credit under PMEGP, PM SVANidhi, or Mudra in last 5 years with outstanding balance",
            "Government servants and their family members (spouse and unmarried children)"
        ],
        "required_documents": [
            {"name": "Aadhaar Card with Biometric Verification", "mandatory": True, "alternatives": []},
            {"name": "Active Mobile Number linked to Aadhaar", "mandatory": True, "alternatives": []},
            {"name": "Bank Account Details", "mandatory": True, "alternatives": []},
            {"name": "Ration Card (for family verification)", "mandatory": True, "alternatives": ["Panchayat Family Verification Letter"]}
        ],
        "application_steps": [
            "Visit any Common Service Centre (CSC) with Aadhaar and active mobile.",
            "Complete biometric Aadhaar authentication.",
            "Select trade from the 18 eligible traditional family crafts.",
            "Panchayat / Urban Local Body conducts three-tier verification (Gram Panchayat / ULB level, District Screening Committee, State Implementation Committee).",
            "Upon approval, receive PM Vishwakarma digital certificate and undergo basic skill training."
        ],
        "official_portal_url": "https://pmvishwakarma.gov.in",
        "verification_status": "verified",
        "sources": [
            {
                "source_title": "PM Vishwakarma Scheme Guidelines",
                "source_url": "https://pmvishwakarma.gov.in/Home/Guidelines",
                "issuing_authority": "Ministry of Micro, Small & Medium Enterprises, Govt of India",
                "document_reference": "MSME Notification No. 1/1(1)/2023-P&G"
            }
        ]
    }
]

def seed_database(db: Session):
    """
    Populate database with initial verified government schemes and default admin user idempotently.
    """
    for data in VERIFIED_SCHEMES:
        data_copy = dict(data)
        sources_data = data_copy.pop("sources", [])
        
        existing_scheme = db.query(Scheme).filter(Scheme.slug == data_copy["slug"]).first()
        if not existing_scheme:
            scheme = Scheme(**data_copy)
            db.add(scheme)
            db.flush()

            for s in sources_data:
                source = SchemeSource(
                    scheme_id=scheme.id,
                    source_title=s["source_title"],
                    source_url=s["source_url"],
                    issuing_authority=s["issuing_authority"],
                    document_reference=s.get("document_reference")
                )
                db.add(source)
            db.commit()

    # Check for default admin user
    admin_user = db.query(User).filter(User.email == "admin@jansahayak.gov.in").first()
    if not admin_user:
        admin = User(
            full_name="JanSahayak Nodal Officer",
            email="admin@jansahayak.gov.in",
            phone="9876543210",
            hashed_password=hash_password("JanSahayakAdmin@2026"),
            role="admin",
            preferred_language="en",
            state="Delhi",
            is_active=True
        )
        db.add(admin)
        db.commit()
