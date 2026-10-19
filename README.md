# Adera - Threat Intelligence & Scam Intelligence (Team Member 1)

**Developer:** Biruk  
**Role:** Team Member 1 - Threat Intelligence & Scam Intelligence  
**Project:** Adera Digital Payment Fraud Intelligence & Recipient-Risk Platform  

---

## 📌 Module Overview

As **Team Member 1**, Biruk establishes the **threat intelligence foundation** for Adera. This module defines:
1. **What Adera detects:** Complete scam taxonomy tailored for Ethiopia (CBE Birr, Telebirr, M-Pesa, Bank Transfer).
2. **What warning signals to track:** Fraud indicator registry, risk weights (+5 to +30), and evidence strength tiers (`STRONG` vs `WEAK`).
3. **How reports gain confidence:** Progressive confidence lifecycle (`UNKNOWN` → `REPORTED` → `SUSPICIOUS` → `HIGH_CONFIDENCE_RISK`).
4. **Synthetic data feed:** Rich JSON datasets powering the Risk Engine (Member 2), Database seeding (Member 3), and Backend API (Member 4).

---

## 📂 Deliverables Directory Structure

```
adera/
├── data/
│   ├── scam_types.json             # Hierarchical taxonomy of 6 primary scam categories & subtypes
│   ├── fraud_indicators.json       # Registry of 12 warning indicators with weights & evidence tiers
│   ├── synthetic_reports.json      # 9 synthetic victim reports (inc. demo target 0912345678)
│   └── synthetic_scam_cases.json   # Investigated fraud cases & multi-account scam clusters
├── docs/
│   ├── scam_taxonomy.md            # Comprehensive research report on scam TTPs, warning signs & evidence rules
│   └── indicator_definitions.md    # Technical dictionary for Risk Engine rule integration & thresholds
├── scripts/
│   └── generate_and_validate.py    # CLI validation tool to verify JSON integrity & statistics
└── README.md                       # Master module documentation
```

---

## 🚀 How Other Team Members Integrate Biruk's Intelligence

### 1. Team Member 2: Risk Engine & Fraud Detection
- **Input:** Read `data/fraud_indicators.json` for indicator IDs and risk weights.
- **Scoring:** Sum risk weights for observed indicators against thresholds defined in `docs/indicator_definitions.md`:
  - `0 – 24`: LOW
  - `25 – 49`: MODERATE
  - `50 – 74`: HIGH
  - `75 – 100`: CRITICAL

### 2. Team Member 3: Database & Fraud Intelligence
- **Seeding:** Use `data/synthetic_reports.json` and `data/synthetic_scam_cases.json` to populate PostgreSQL tables (`fraud_reports`, `scam_cases`).
- **Relational Schema:** Map `scam_type` string references to database FKs.

### 3. Team Member 4: Backend & API Developer
- **Endpoints:** Serve `GET /reports` and `GET /cases` using structured JSON schemas defined in `data/synthetic_reports.json` and `data/synthetic_scam_cases.json`.

---

## 🧪 Validation & Test Execution

Run the built-in validation script to verify schema integrity:

```bash
python scripts/generate_and_validate.py
```

**Output:**
- Confirms valid JSON syntax across all 4 data files.
- Verifies 100% reference integrity for scam types and indicator keys.
- Validates that target demo phone `0912345678` contains 7 reports aligned with Section 11 of the Adera project specification.
