# Adera Fraud Indicator Dictionary & Weight Rationale

**Author:** Biruk (Team Member 1: Threat Intelligence & Scam Intelligence)  
**Target Module:** Adera Risk Engine & Backend Integration

> **Runtime boundary:** The indicator weights and evaluation guidance below are
> threat-intelligence metadata and proposals; they are not automatically applied
> by the current risk engine. The active scoring weights, thresholds, levels,
> recommendations, and inputs are defined in [risk-scoring.md](risk-scoring.md).
> Do not infer a runtime scoring change from this registry.

---

## 1. Indicator Registry Summary Table

| Indicator ID | Category | Default Risk Weight | Evidence Strength | Confidence Level |
| :--- | :--- | :---: | :---: | :---: |
| `multiple_fraud_reports` | REPORTS | +25 | STRONG | HIGH |
| `recent_reports` | REPORTS | +20 | STRONG | HIGH |
| `suspicious_connections` | GRAPH_RELATIONSHIP | +15 | STRONG | MEDIUM |
| `previous_scam_cases` | HISTORICAL | +15 | STRONG | HIGH |
| `otp_solicitation` | SECURITY | +30 | CRITICAL | CRITICAL |
| `fake_sms_notification` | SECURITY | +25 | STRONG | HIGH |
| `urgent_request` | BEHAVIORAL | +15 | WEAK | LOW |
| `identity_claim` | BEHAVIORAL | +15 | WEAK | LOW |
| `advance_payment_demand` | BEHAVIORAL | +15 | WEAK | LOW |
| `new_recipient` | HISTORICAL | +10 | WEAK | LOW |
| `unusual_payment_amount` | TRANSACTIONAL | +10 | WEAK | LOW |
| `newly_created_account` | ACCOUNT_PROFILE | +10 | WEAK | LOW |

---

## 2. Detailed Indicator Rationale & Evaluation Rules

### 1. `multiple_fraud_reports`
- **Definition:** The recipient phone number has accumulated 3 or more independent user reports of fraud.
- **Risk Weight:** `+25`
- **Evidence Strength:** `STRONG`
- **Evaluation Logic:** `COUNT(fraud_reports WHERE status != 'DISMISSED') >= 3`
- **False-Positive Guard:** Require reports to originate from distinct reporter phone numbers to prevent abuse by a single disgruntled user.

---

### 2. `recent_reports`
- **Definition:** The recipient has received 2 or more reports within the past 7 days.
- **Risk Weight:** `+20`
- **Evidence Strength:** `STRONG`
- **Evaluation Logic:** `COUNT(fraud_reports WHERE timestamp >= NOW() - 7 DAYS) >= 2`
- **Rationale:** Indicates an ongoing, active scam campaign. Recent reports are given higher weight than older historical reports.

---

### 3. `suspicious_connections`
- **Definition:** Recipient account shares graph relationships (shared bank accounts, device IDs, or rapid money hops) with known fraudulent wallets.
- **Risk Weight:** `+15`
- **Evidence Strength:** `STRONG`
- **Evaluation Logic:** `COUNT(graph_connected_flagged_entities within 2 hops) >= 1`
- **Rationale:** Detects scam syndicates that rotate phone numbers while reusing underlying payout accounts.

---

### 4. `previous_scam_cases`
- **Definition:** Recipient phone number or associated identity is linked to an investigated scam case in `synthetic_scam_cases.json`.
- **Risk Weight:** `+15`
- **Evidence Strength:** `STRONG`
- **Evaluation Logic:** `COUNT(scam_cases WHERE primary_target_phone = recipient OR recipient IN linked_phones) >= 1`

---

### 5. `otp_solicitation`
- **Definition:** Communication or report logs show recipient requested an SMS OTP code or PIN.
- **Risk Weight:** `+30`
- **Evidence Strength:** `CRITICAL`
- **Rationale:** Legitimate transactions never require sharing SMS OTP codes. Triggering this indicator immediately pushes transaction into `HIGH` or `CRITICAL` risk.

---

### 6. `urgent_request` & `identity_claim`
- **Definition:** Pressure tactic or unverified claim of relationship/authority (e.g. friend emergency, boss request).
- **Risk Weight:** `+15` each
- **Evidence Strength:** `WEAK`
- **Rationale:** These indicators describe behavioral signals from the victim. Combined with strong indicators, they explain *why* the user should verify the recipient before proceeding.

---

## 3. Suggested Risk Thresholds (Not the Current Runtime Contract)

The following table records a suggested interpretation of these indicator
weights for discussion. The current runtime risk engine does **not** consume
these weighted indicators directly; it uses the separate scoring contract in
[risk-scoring.md](risk-scoring.md). These suggestions do not change runtime
scores or recommendations.

| Risk Score Range | Risk Level | System Recommendation | Action in UI |
| :---: | :---: | :---: | :---: |
| **0 – 24** | **LOW** | `PROCEED` | Show subtle green checkmark ("Recipient appears low risk") |
| **25 – 49** | **MODERATE** | `VERIFY_DETAILS` | Show yellow caution banner ("Review details before proceeding") |
| **50 – 74** | **HIGH** | `WARN_USER` | Show orange warning modal with line-item reasons |
| **75 – 100** | **CRITICAL** | `STOP_AND_VERIFY` | Show prominent red warning modal ("High risk detected. Verify before sending money.") |

---

## 4. Reason Generation Format (Explainability Specification)

The Risk Engine must return human-readable reason strings matching the indicators triggered. For example, for recipient `0912345678`:

```json
{
  "score": 82,
  "level": "CRITICAL",
  "recommendation": "STOP_AND_VERIFY",
  "reasons": [
    "7 fraud reports registered against this recipient",
    "3 recent fraud reports in the last 7 days",
    "3 suspicious connected accounts in fraud graph",
    "Previous impersonation scam cases on record"
  ]
}
```
