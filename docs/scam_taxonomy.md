# Adera Scam Taxonomy & Threat Intelligence Research

**Author:** Biruk (Team Member 1: Threat Intelligence & Scam Intelligence)  
**System:** Adera Digital Payment Fraud Intelligence & Recipient-Risk Platform  
**Target Region / Context:** Ethiopian Digital Financial Services (CBE Birr, Telebirr, M-Pesa, Bank Transfer Interfaces)

---

## 1. Executive Summary

Digital payment adoption in Ethiopia has grown rapidly with platforms like **CBE Birr, Telebirr, M-Pesa, and mobile banking apps**. However, the vast majority of consumer financial losses do not stem from cryptographic breaches or payment infrastructure hacks. Instead, attackers use **social engineering** to trick victims into self-authorizing payment transfers.

From the financial institution's perspective, the transaction appears legitimate because it was authorized by the actual account holder. **Adera** solves this by evaluating recipient risk and payment signals *before* the customer presses "Confirm", providing transparent, explainable warnings.

This research document defines the **Scam Taxonomy**, attacker Tactics, Techniques, and Procedures (TTPs), warning signals, evidence evaluation guidelines, and report confidence lifecycles.

---

## 2. Adera Scam Taxonomy Hierarchy

```
SCAM TYPES
├── 1. Impersonation Scams
│   ├── 1.1 Friend / Family Emergency Impersonation
│   ├── 1.2 Employee / Boss Impersonation (CEO Fraud)
│   ├── 1.3 Bank / Telecom Official Impersonation
│   └── 1.4 Organization / NGO / Church Impersonation
│
├── 2. Fake Seller & E-commerce Fraud
│   ├── 2.1 Advance Payment for Goods (Electronics / Vehicles)
│   └── 2.2 Fake Social Media Boutique / Store Page
│
├── 3. Investment & Ponzi Schemes
│   ├── 3.1 Pyramid / Ponzi Multi-Level Scam
│   └── 3.2 Online Task / Freelance Deposit Scam
│
├── 4. Urgent & Pressure Scams
│   ├── 4.1 Fake Accidental Transfer Refund
│   └── 4.2 Hospital / Police Emergency Hoax
│
├── 5. Fake Prize & Giveaway Scams
│   └── 5.1 Telecom Lottery / Car Giveaway Fee
│
└── 6. Account Takeover & OTP Harvesting
    └── 6.1 SMS OTP / PIN Solicitation
```

---

## 3. Deep-Dive Analysis of Primary Scam Vectors

### 3.1 Impersonation Scams

#### A. Friend / Family Emergency Impersonation
- **How it works:** Attacker compromises or clones a Telegram/WhatsApp account or calls from a new number, claiming to be a close relative or friend in immediate crisis (police detention, medical emergency, stranded travel).
- **What Victim Sees:** A message or panicked call from a familiar name asking for urgent funds (e.g., 3,000 – 10,000 ETB).
- **What Attacker Does:** Uses high emotional urgency, claims their primary bank account is inaccessible, and provides a third-party recipient phone number for payment.
- **Warning Signs:** Refusal to answer voice/video calls, change of payment recipient number, extreme deadline ("send within 5 minutes").
- **Transaction Pattern:** Immediate transfer to an unfamiliar recipient phone number never previously transacted with.
- **Strong Evidence:** Multiple independent user reports against recipient phone within 24–48 hours; recipient connected to known scam cluster.
- **Weak Evidence:** A single unverified report without corroborating graph connections or account age data.

#### B. Bank / Telecom Official Impersonation
- **How it works:** Attacker calls victim posing as a CBE, Telebirr, or Ethio Telecom customer service agent claiming the victim's wallet will be blocked or upgraded.
- **What Victim Sees:** A phone call from an ordinary mobile number claiming to be official support.
- **What Attacker Does:** Asks victim for their PIN or the SMS OTP code sent to their phone to "verify identity".
- **Strong Evidence:** Report detailing explicit request for OTP / PIN codes.

---

### 3.2 Fake Seller & E-Commerce Fraud

- **How it works:** Attacker creates attractive Telegram channels or TikTok pages offering discounted electronics, clothes, or vehicles.
- **What Victim Sees:** Pictures of high-end items at 40-50% below market value.
- **What Attacker Does:** Demands 50% to 100% advance deposit via mobile payment before shipping. Once paid, victim is blocked.
- **Warning Signs:** Unverified individual wallet payment (no merchant account), prices significantly below market average, pressure to pay immediately.
- **Transaction Pattern:** Multiple incoming payments from diverse senders followed immediately by cash-out withdrawals.

---

### 3.3 Investment & Ponzi Schemes

- **How it works:** Fraudulent investment groups promise high daily or weekly passive income (e.g., 10% daily return) via crypto or task platforms.
- **What Victim Sees:** Telegram groups showing fake payout screenshots and luxury lifestyles.
- **What Attacker Does:** Pays early small withdrawals to build trust, then freezes funds when large deposits accumulate.
- **Transaction Pattern:** Recipient wallet receives dozens of incoming transfers daily from unique senders.

---

### 3.4 Urgent & Pressure Scams (Accidental Transfer Refund)

- **How it works:** Attacker sends a forged SMS formatted to mimic a bank credit alert, then calls claiming they accidentally sent money to the victim's account.
- **What Victim Sees:** Fake SMS alert + immediate phone call demanding a refund transfer.
- **What Attacker Does:** Exploits victim's honesty to send real money without checking actual bank balance.
- **Strong Evidence:** Sender balance statement showing no actual incoming transfer; report of fake SMS.

---

## 4. Evidence Classification: Strong vs. Weak Evidence

Adera must **never** treat one unverified report as conclusive proof of criminality. Evidence must be evaluated in tiers:

| Evidence Tier | Signal Examples | Weight Rationale |
| :--- | :--- | :--- |
| **CRITICAL / STRONG** | • OTP / PIN harvesting report<br>• 3+ independent fraud reports<br>• Graph connection to known scam cluster<br>• Formal law enforcement / analyst case flag | High statistical probability of malicious intent. Immediately elevates risk score to HIGH or CRITICAL. |
| **MODERATE** | • Recent report spike (2 reports in 7 days)<br>• Newly registered account (<30 days old)<br>• Rapid incoming funds cash-out behavior | Indicates potential anomaly or emerging threat requiring warning. |
| **WEAK (Unverified)** | • Single unverified report<br>• First-time transfer between sender/recipient<br>• High payment amount alone | Normal user activity can trigger weak signals. Must NOT block account based on weak evidence alone. |

---

## 5. Fraud Report Confidence Life-Cycle

Adera applies a progressive confidence model to ensure fairness and prevent false positives:

```
[ UNKNOWN ]
    │
    ▼ (1 unverified report submitted)
[ REPORTED ]
    │
    ▼ (Corroborated by 2-3 reports OR recent activity)
[ SUSPICIOUS ]
    │
    ▼ (Multiple independent reports + scam case linkage + analyst review)
[ HIGH-CONFIDENCE RISK ]
```

1. **UNKNOWN:** Recipient has no report history. Risk relies strictly on behavioral/transactional signals.
2. **REPORTED:** Single user report registered. Treated as low confidence; warning shown only if transaction amount is unusually high.
3. **SUSPICIOUS:** Multiple reports or recent cluster activity detected. Triggers MODERATE risk warning (Score 25–49).
4. **HIGH-CONFIDENCE RISK:** Corroborated multi-report history or formal investigation link. Triggers HIGH/CRITICAL warning modal with explicit reason breakdown (Score 50–100).
