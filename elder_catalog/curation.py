"""Resource details copied from the PDF. Citations have not been checked.

Each row has a title, publication date, format, creators, publisher,
journal or series, identifiers, and suggested topics. P: means person;
O: means organization. Missing details stay empty.
"""

ROWS = [
    ("How to protect yourself from financial scams targeting older adults: Americans over 60 are losing billions of dollars to fraud, a far bigger threat than physical crime", "2026-03-12", "news_article", ["P:Ansberry, C."], "The Wall Street Journal", None, ["https://www.wsj.com/health/wellness/how-to-protect-yourself-from-financial-scams-targeting-older-adults-8bcffeda"], ["fraud_prevention"]),
    ("Older adults and scam awareness: Exploring vulnerability within geriatric oncology", "2020", "journal_article", ["P:Boyle, D. A."], None, "Clinical Journal of Oncology Nursing, 24(4), 434–438", ["https://doi.org/10.1188/20.CJON.434-438"], ["fraud_prevention", "health_scams"]),
    ("Examining older adults’ vulnerability to online health scams: Insights from routine activity theory", "2025", "journal_article", ["P:Chen, H.", "P:He, M.", "P:Xu, X.", "P:Atkin, D."], None, "Frontiers in Public Health, 13, 1585851", ["https://doi.org/10.3389/fpubh.2025.1585851"], ["health_scams", "internet_safety"]),
    ("The role of misinformation in elder fraud: A conceptual framework", "2026", "journal_article", ["P:Chen, J.", "P:Ono, M. P."], None, "Information Research, 31(iConf), 1054–1066", ["https://doi.org/10.47989/ir31iConf64186"], ["misinformation", "fraud_prevention"]),
    ("Protecting older adults from fraud and financial exploitation", "2026-03-10", "web_resource", ["O:Consumer Financial Protection Bureau"], None, None, ["https://www.consumerfinance.gov/consumer-tools/educator-tools/resources-for-older-adults/"], ["fraud_prevention"]),
    ("Elder fraud and financial exploitation: Application of routine activity theory", "2018", "journal_article", ["P:DeLiema, M."], None, "The Gerontologist, 58(4), 706–718", ["https://doi.org/10.1093/geront/gnw258"], ["fraud_prevention"]),
    ("Financial fraud and deception in aging", "2023", "journal_article", ["P:Ebner, N. C.", "P:Pehlivanoglu, D.", "P:Shoenfelt, A."], None, "Advances in Geriatric Medicine and Research, 5(3), e230007", ["https://doi.org/10.20900/agmr20230007"], ["fraud_prevention"]),
    ("iPhone 16 for Seniors: The Absolute Beginner’s Guide to Every Button, Icon, and Screen Explained in Plain English—with Large Print and Step-by-Step Instructions", "2026", "book", ["P:Ellery, M. J."], "Independently published", None, [], ["digital_literacy"]),
    ("Don’t Click That: A Senior’s 10-Day Guide to Staying Safe Online — Large", "2026", "book", ["P:Freeman, A."], None, None, [], ["internet_safety"]),
    ("Elder fraud", None, "web_resource", ["O:Federal Bureau of Investigation"], None, None, ["https://www.fbi.gov/how-we-can-help-you/common-frauds-and-scams/elder-fraud"], ["fraud_prevention"]),
    ("Inclusive interface design for seniors: Image-browsing for a health information context", "2007", "journal_article", ["P:Given, L. M.", "P:Ruecker, S.", "P:Simpson, H.", "P:Sadler, E.", "P:Ruskin, A."], None, "Journal of the American Society for Information Science & Technology, 58(11), 1610–1617", ["https://doi.org/10.1002/asi.20645"], ["accessible_design"]),
    ("The complete Windows 11 guide for seniors: An easy, step-by-step visual guide for beginners packed with clear pictures to master Windows 11 without frustration", "2025", "book", ["P:Grant, W."], "Independently published", None, [], ["digital_literacy"]),
    ("Fighting phishing: Everything you can do to fight social engineering and phishing", "2024", "book", ["P:Grimes, R. A."], "John Wiley & Sons", None, [], ["phishing", "social_engineering"]),
    ("Delphi study of risk to individuals who disclose personal information online", "2023", "journal_article", ["P:Haynes, D.", "P:Robinson, L."], None, "Journal of Information Science, 49(1), 93–106", ["https://doi.org/10.1177/0165551521992756"], ["internet_safety"]),
    ("Eldercare and aging: Online information for librarians and caregivers", "2009", "journal_article", ["P:Hudson, A."], None, "College & Research Libraries News, 70(9), 526–530", [], ["caregiving", "library_programming"]),
    ("BSAFE: Bankers and seniors against financial exploitation*", "2023", "brochure", ["O:Illinois Department on Aging"], None, None, ["https://ilaging.illinois.gov/content/dam/soi/en/web/aging/resources/newsandpublications/publications/documents/stop-senior-exploitation-bankers-b-safe-brochure.pdf"], ["fraud_prevention"]),
    ("How to block scam calls, the top source of fraud against older adults", "2023-01-12", "news_article", ["P:Jargon, J."], "The Wall Street Journal", None, ["https://www.wsj.com/articles/how-to-block-scam-calls-the-top-source-of-fraud-against-older-adults-11673051224"], ["phone_scams"]),
    ("The top 5 financial scams targeting older adults", "2026-08-07", "web_resource", ["P:Johnston, J."], "National Council on Aging", None, ["https://www.ncoa.org/article/top-5-financial-scams-targeting-older-adults/"], ["fraud_prevention"]),
    ("Help take action against online scams", None, "web_resource", ["O:National Council on Aging"], None, None, ["https://www.ncoa.org/page/ncoa-zelle-world-elder-abuse-awareness-day-social-media-toolkit/"], ["internet_safety"]),
    ("Fraud awareness and prevention for older adults and people with disabilities", "2026", "web_resource", ["O:National Library Service for the Blind and Print Disabled"], "Library of Congress", None, ["https://www.loc.gov/nls/services-and-resources/informational-publications/fraud-awareness-and-prevention-for-older-adults-and-people-with-disabilities/"], ["fraud_prevention", "accessibility"]),
    ("Preventing AI scams: Digital defense in an evolving online ecosystem", "2026-04-27", "web_resource", ["O:Northwestern University Information Technology"], "Northwestern University", None, ["https://www.it.northwestern.edu/about/news-events/2026/preventing-ai-scams-digital-defense-in-an-evolving-online-ecosystem.html"], ["ai_scams", "internet_safety"]),
    ("National Elder Fraud Hotline", None, "web_resource", ["O:Office for Victims of Crime"], "U.S. Department of Justice", None, ["https://ovc.ojp.gov/program/stop-elder-fraud/providing-help-restoring-hope"], ["reporting_support"]),
    ("Steer clear of the sweetheart scam", None, "fact_sheet", ["O:Office of the Illinois Attorney General"], None, None, ["https://illinoisattorneygeneral.gov/Page-Attachments/SweetheartScam.pdf"], ["romance_scams"]),
    ("Protecting your parents’ money: The essential guide to helping Mom and Dad navigate the finances of retirement", "2011", "book", ["P:Opdyke, J. D."], "HarperCollins", None, [], ["caregiving", "financial_services"]),
    ("A practical guide to elderly fraud", "2025", "book", ["P:Patten, J."], "Law Brief Publishing", None, ["https://www.lawbriefpublishing.com/product/elderlyfraud"], ["legal_recourse"]),
    ("Elder financial abuse and inheritance fraud: Prevention, detection and legal enforcement", "2025", "book", ["P:Rudy, M. D."], "Michael D. Rudy", None, [], ["legal_recourse", "fraud_prevention"]),
    ("Journal of Elder Abuse & Neglect", None, "journal", ["O:Taylor & Francis"], None, None, ["https://www.tandfonline.com/journals/wean20"], ["fraud_prevention"]),
    ("Get involved, get safe community presentations", "2025-01-17", "presentation_collection", ["O:U.S. Department of Justice"], None, None, ["https://www.justice.gov/elderjustice/get-involved-get-safe-community-presentations"], ["library_programming", "fraud_prevention"]),
    ("Websites and resources", None, "web_resource", ["O:U.S. Department of Justice"], None, "Elder Justice Initiative", ["https://www.justice.gov/elderjustice/websites-and-resources"], ["reporting_support"]),
    ("Elder fraud", None, "web_resource", ["O:United States Secret Service"], None, None, ["https://www.secretservice.gov/investigations/elderfraud"], ["fraud_prevention"]),
    ("The rise of predatory scams—and how to prevent them", "2021-06", "video", ["P:Walsh, J."], "TED Conferences", None, ["https://www.ted.com/talks/jane_walsh_the_rise_of_predatory_scams_and_how_to_prevent_them"], ["fraud_prevention"]),
    ("Dot con: The art of scamming a scammer", "2020", "book", ["P:Veitch, J."], "Grand Central Publishing", None, [], ["social_engineering"]),
    ("Here are ways you can avoid social media shopping scams", "2023-04-05", "video", ["O:AARP Live"], "YouTube", None, [], ["shopping_scams", "internet_safety"]),
    ("What Is Phishing? And How to Avoid the Bait", "2019-10-01", "video", ["P:Lamb, Mike"], "YouTube", None, ["https://www.youtube.com/watch?v=XsOWczwRVuc"], ["phishing"]),
    ("The Art of Social Engineering", None, "unknown", [], None, None, ["https://learning.oreilly.com/library/view/the-art-of/9781804613641/"], ["social_engineering"]),
    ("EASY MONEY: FINANCIAL SCAMS AND OLDER ADULTS - ClinicalKey", None, "unknown", [], None, None, ["https://www-clinicalkey-com.proxy2.library.illinois.edu/#!/content/journal/1-s2.0-S106474812030035X"], ["fraud_prevention"]),
    ("A Tour of Terrible Ads on Yahoo (Plus a Little Mild Scambaiting)", None, "video", ["O:Atomic Shrimp"], "YouTube", None, ["https://youtube.com/watch?v=VeD9dUUFl-E"], ["misinformation", "internet_safety"]),
    ("What is a reverse mortgage, and is it a good idea for you?", "2023-06-01", "video", ["O:Josh Denbeaux - Mortgage & Foreclosure Attorney"], "YouTube", None, ["https://www.youtube.com/watch?v=W_sBsBvGJLM"], ["financial_services"]),
    ("Fast cash, big risks: Spotting predatory lenders | It’s a money thing", "2017-08-25", "video", ["O:Red Canoe Credit Union"], "YouTube", None, ["https://www.youtube.com/watch?v=gHaX3ThW8I4"], ["predatory_lending"]),
    ("Elder fraud prevention: Spot the red flags before it’s too late | Long version", "2026-02-12", "video", ["O:sandiegoda"], "YouTube", None, ["https://www.youtube.com/watch?v=IljMX5h_GDE"], ["fraud_prevention"]),
    ("Phishing explained in 6 minutes | What is a phishing attack? | Phishing attack | Simplilearn", "2021-09-16", "video", ["O:Simplilearn"], "YouTube", None, ["https://www.youtube.com/watch?v=XBkzBrXlle0"], ["phishing"]),
    ("How to spot fake AI photos | Hany Farid | TED", "2025-07-18", "video", ["O:TED"], "YouTube", None, ["https://www.youtube.com/watch?v=q5_PrTvNypY"], ["ai_scams", "misinformation"]),
    ("Jane Walsh: The rise of predatory scams -- and how to prevent them | TED", "2022-02-05", "video", ["O:TED"], "YouTube", None, ["https://www.youtube.com/watch?v=eIRtcspIH4U"], ["fraud_prevention"]),
    ("How to tell what’s real and what’s AI-generated on social media", "2026-03-04", "video", ["O:TODAY"], "YouTube", None, ["https://www.youtube.com/watch?v=MtEe3NJnqQs"], ["ai_scams", "misinformation"]),
    ("Predatory lending: What to watch out for", "2021-01-01", "video", ["O:Yahoo Finance"], "YouTube", None, ["https://www.youtube.com/watch?v=4wj2daqQi9I"], ["predatory_lending"]),
    ("Small Talks for Big Change: Elder Fraud Prevention in a Digital Age", None, "podcast", ["P:Farrell, A."], None, None, ["https://d3deb460-a746-47fe-a802-c309230a46eb.libsyn.com/elder-fraud-prevention-in-a-digital-age"], ["fraud_prevention", "internet_safety"]),
    # The repeated website uses bibliography record #22.
    ("National Elder Fraud Hotline", None, "hotline_service", [], None, None, ["tel:+18333728311"], ["reporting_support"]),
    ("Romance/Sweetheart Scam Alert", None, "flyer", [], None, None, [], ["romance_scams"]),
    ("Illinois Department of Aging Flye", None, "flyer", [], None, None, [], []),
]

TOPICS = {
    "fraud_prevention": "Fraud prevention and awareness", "health_scams": "Health and Medicare scams",
    "internet_safety": "Internet safety", "misinformation": "Misinformation and deceptive advertising",
    "digital_literacy": "Digital literacy", "accessible_design": "Accessible interface design",
    "phishing": "Phishing", "social_engineering": "Social engineering", "caregiving": "Caregiving",
    "library_programming": "Library and community programming", "phone_scams": "Phone scams",
    "accessibility": "Disability access", "ai_scams": "AI impersonation and synthetic media",
    "reporting_support": "Reporting and victim support", "romance_scams": "Romance and sweetheart scams",
    "financial_services": "Financial services and retirement", "legal_recourse": "Legal recourse",
    "shopping_scams": "Online shopping scams", "predatory_lending": "Predatory lending",
    "grandchild_scams": "Grandchild scams", "tech_support_scams": "Tech support scams",
    "government_impersonation": "Government impersonation", "credit_card_fraud": "Credit card fraud",
    "mail_fraud": "Mail fraud", "tax_assistance": "Tax assistance",
}

AUDIENCES = {
    "older_adults": "Older adults", "caregivers": "Caregivers", "family": "Family and support groups",
    "library_staff": "Library staff", "community_organizations": "Community organizations",
    "social_workers": "Social workers", "healthcare_providers": "Healthcare providers",
    "people_with_disabilities": "People with disabilities",
}

# All citations need checking. These entries flag specific problems.
ISSUES = {
    8: [("inferred_format", "Book format inferred from title and publishing statement; verify edition and large-print claim.")],
    9: [("incomplete_title", "Citation ends at '— Large'; title and book format require review.")],
    16: [("unexplained_marker", "Title ends with an unexplained asterisk in the source.")],
    31: [("possible_duplicate", "May be the same talk as video #11 (r043); dates and platforms differ.")],
    35: [("ambiguous_format", "Listed under Videos, but URL points to an O’Reilly library item; format unverified.")],
    36: [("ambiguous_format", "Listed under Videos, but URL points to ClinicalKey journal content."), ("proxy_url", "Institution-specific proxy URL; no public URL inferred."), ("url_cleanup", "Removed trailing backslash and joined the wrapped URL; original retained.")],
    37: [("url_cleanup", "Added https scheme to the source's schemeless YouTube locator.")],
    43: [("possible_duplicate", "May be the same talk as bibliography #31 (r031); retained separately.")],
    47: [("service_details_unverified", "Telephone number is transcribed from the PDF; service hours, eligibility and operator are unknown.")],
    48: [("incomplete_citation", "Title only; may correspond to r023, but identity is unconfirmed.")],
    49: [("incomplete_citation", "Source title appears truncated; no author, date, or locator."), ("possible_duplicate", "Might refer to r016; title is insufficient to merge.")],
}

# These suggested links need review before any records are merged.
RELATIONS = [
    ("r031", "r043", "possible_same_work", "Same talk title and speaker; publication dates and platforms differ."),
    ("r048", "r023", "possible_same_work", "Both concern a sweetheart scam flyer; only one has an identifying URL."),
    ("r049", "r016", "possible_same_work", "Illinois aging flyer may refer to BSAFE; insufficient evidence."),
    ("r022", "r047", "describes_service", "Both source entries name the National Elder Fraud Hotline; operator not inferred."),
]
