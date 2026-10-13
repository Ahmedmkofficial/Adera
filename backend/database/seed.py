"""Seed Adera's database with FICTIONAL demo data.

Run from the project root, with the virtual environment active:

    python -m backend.database.seed            # first time (empty database)
    python -m backend.database.seed --reset    # wipe ALL rows, then reload

Everything below is invented. Never put real customer or banking information
in this file.
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.models import (
    AccountRelationship,
    Alert,
    FraudReport,
    PaymentAccount,
    RelationshipType,
    RiskAssessment,
    ScamCase,
    Transaction,
    User,
    scam_case_accounts,
    scam_case_reports,
)

# The project stores naive UTC datetimes, so the seed does too.
NOW = datetime.now(timezone.utc).replace(tzinfo=None)
PLACEHOLDER_HASH = "SEED-ONLY-NOT-A-REAL-PASSWORD-HASH"

FAKE_JOB = "Fake job offer"
ADVANCE_FEE = "Advance-fee request"
ROMANCE = "Romance scam"
INVESTMENT = "Fake investment scheme"
PHISHING = "Phishing / impersonation"

# risk_assessments.recommendation is limited to 50 characters
RECOMMENDATIONS = {
    "LOW": "Allow",
    "MODERATE": "Allow with sender warning",
    "HIGH": "Hold payment and request analyst review",
    "CRITICAL": "Block payment and escalate to analyst",
}


def ago(days: float = 0, hours: float = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours)


def level_for(score: int) -> str:
    # Illustrative thresholds only. The real ones belong to the risk engine.
    if score < 25:
        return "LOW"
    if score < 60:
        return "MODERATE"
    if score < 80:
        return "HIGH"
    return "CRITICAL"


def reset(db: Session) -> None:
    """Delete every row, children first so foreign keys are never violated."""
    db.execute(delete(Alert))
    db.execute(delete(RiskAssessment))
    db.execute(delete(scam_case_reports))
    db.execute(delete(scam_case_accounts))
    db.execute(delete(ScamCase))
    db.execute(delete(AccountRelationship))
    db.execute(delete(FraudReport))
    db.execute(delete(Transaction))
    db.execute(delete(PaymentAccount))
    db.execute(delete(User))
    db.commit()


def seed(db: Session) -> None:
    rng = random.Random(42)  # fixed seed: everyone gets identical demo data

    # ------------------------------------------------------------------
    # 1. USERS: ten people who send money and file reports
    # ------------------------------------------------------------------
    reporter_names = [
        "Alex Morgan", "Sam Rivera", "Jordan Lee", "Taylor Kim", "Casey Nguyen",
        "Riley Patel", "Jamie Cruz", "Morgan Diaz", "Avery Stone", "Quinn Foster",
    ]
    reporters = []
    for i, name in enumerate(reporter_names, start=1):
        user = User(phone=f"09110000{i:02d}", name=name, password_hash=PLACEHOLDER_HASH)
        db.add(user)
        reporters.append(user)

    def holder(phone: str, name: str) -> User:
        user = User(phone=phone, name=name, password_hash=PLACEHOLDER_HASH)
        db.add(user)
        return user

    # ------------------------------------------------------------------
    # 2. ACCOUNTS
    # ------------------------------------------------------------------
    # PaymentAccount.user_id is required, so the users need ids first.
    db.flush()
    for i, user in enumerate(reporters, start=1):
        db.add(PaymentAccount(
            user_id=user.id, account_number=f"20000000{i:02d}",
            provider="DemoBank", phone_number=user.phone,
        ))

    def recipient(number: str, holder_name: str, provider: str = "DemoWallet") -> PaymentAccount:
        owner = holder(number, holder_name)
        db.flush()
        acct = PaymentAccount(
            user_id=owner.id, account_number=number,
            provider=provider, phone_number=number,
        )
        db.add(acct)
        return acct

    acct_a = recipient("0912345678", "Demo Holder A")   # main scam example
    acct_b = recipient("0923456789", "Demo Holder B")   # normal account
    acct_c = recipient("0934567890", "Demo Holder C")   # receives money from A
    acct_d = recipient("0945678901", "Demo Holder D")   # related to A
    acct_e = recipient("0956789012", "Demo Holder E")   # 3 reports, 1 reporter
    acct_f = recipient("0967890123", "Demo Holder F")   # fake investment group
    acct_g = recipient("0978901234", "Demo Holder G")   # shares a device with F
    acct_h = recipient("0989012345", "Demo Shop H")     # ordinary shop
    db.flush()

    def sender_user(i: int) -> User:
        return reporters[i - 1]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def payment(sender_id: int, to_phone: str, amount: int, days_ago: float,
                status: str = "COMPLETED") -> Transaction:
        txn = Transaction(
            sender_id=sender_id, recipient_phone=to_phone,
            amount=Decimal(amount), status=status, timestamp=ago(days=days_ago),
        )
        db.add(txn)
        return txn

    def report(reporter_no: int, to_phone: str, scam_type: str, text: str,
               days_ago: float, status: str = "PENDING") -> FraudReport:
        fr = FraudReport(
            reporter_id=sender_user(reporter_no).id, recipient_phone=to_phone,
            scam_type=scam_type, description=text, status=status,
            created_at=ago(days=days_ago),
        )
        db.add(fr)
        return fr

    def assess(phone: str, score: int, when: datetime, alert_status: str | None = None,
               alert_message: str = "") -> None:
        level = level_for(score)
        db.add(RiskAssessment(
            recipient_phone=phone, score=score, level=level,
            recommendation=RECOMMENDATIONS[level], created_at=when,
        ))
        if alert_status:
            db.add(Alert(
                recipient_phone=phone, message=alert_message, severity=level,
                status=alert_status, created_at=when + timedelta(minutes=1),
            ))

    def link(src: PaymentAccount, dst: PaymentAccount, kind: str, days_ago: float):
        db.add(AccountRelationship(
            source_account_id=src.id, target_account_id=dst.id,
            relationship_type=kind, created_at=ago(days=days_ago),
        ))

    # ------------------------------------------------------------------
    # 3. SCAMS, ACCOUNT A (0912345678): 7 reports from 7 different people.
    #    Each victim pays, then reports a day later.
    # ------------------------------------------------------------------
    A = acct_a.phone_number
    a_plan = [  # (reporter, report age in days, scam type, amount, text, status)
        (1, 19, ADVANCE_FEE, 1500, "Told I had won a scholarship placement and had to pay a processing fee first. Never heard back after paying.", "RESOLVED"),
        (2, 11, ADVANCE_FEE, 3200, "Asked to send a 'release fee' to receive a parcel that did not exist.", "RESOLVED"),
        (3, 6, FAKE_JOB, 800, "Offered a data-entry job abroad and asked to pay a registration fee to the recruiter.", "UNDER_REVIEW"),
        (4, 5, FAKE_JOB, 5000, "Same job offer by phone call. The recruiter pressured me to pay the same day.", "UNDER_REVIEW"),
        (5, 3, FAKE_JOB, 1200, "Paid a 'uniform and training deposit' for a job that was never confirmed.", "PENDING"),
        (6, 2, FAKE_JOB, 2500, "Recruiter sent a fake offer letter and asked for a visa processing fee.", "PENDING"),
        (7, 1, FAKE_JOB, 4000, "Contacted on a messaging app about a remote job, then asked for a security deposit.", "PENDING"),
    ]
    a_txns, a_reports = [], []
    for reporter_no, age, scam, amount, text, status in a_plan:
        a_txns.append(payment(sender_user(reporter_no).id, A, amount, age + 1))
        a_reports.append(report(reporter_no, A, scam, text, age, status))
    a_txns[6].status = "HELD"  # latest payment held after the CRITICAL score
    # A passes some of the money on to C
    payment(acct_a.user_id, acct_c.phone_number, 6000, 1)

    # ------------------------------------------------------------------
    # 4. ACCOUNT C: 3 reports
    # ------------------------------------------------------------------
    C = acct_c.phone_number
    c_plan = [
        (8, 8, FAKE_JOB, 900, "Paid a registration fee for a job. The recruiter's details matched another report."),
        (9, 4, FAKE_JOB, 2000, "Asked for an 'interview slot fee' by text message, then blocked me."),
        (10, 1, PHISHING, 1400, "Someone pretending to be a bank officer asked me to 'verify' my account by sending a deposit."),
    ]
    c_txns = []
    for reporter_no, age, scam, amount, text in c_plan:
        c_txns.append(payment(sender_user(reporter_no).id, C, amount, age + 1))
        report(reporter_no, C, scam, text, age)

    # ------------------------------------------------------------------
    # 5. ACCOUNT D (related to A): 1 report
    # ------------------------------------------------------------------
    D = acct_d.phone_number
    payment(sender_user(9).id, D, 2200, 6)
    report(9, D, ADVANCE_FEE, "Asked to pay a 'customs clearance fee' to receive a gift package.", 5)

    # ------------------------------------------------------------------
    # 6. ACCOUNT E: ONE person filed 3 reports (3 reports, 1 reporter)
    # ------------------------------------------------------------------
    E = acct_e.phone_number
    for age, amount, text in [
        (9, 700, "Met online, was asked for money for a 'medical emergency'."),
        (3, 1100, "Asked again for money for a 'flight ticket to visit me'."),
        (2, 900, "Asked a third time, now for 'customs fees'. I think this is a romance scam."),
    ]:
        payment(sender_user(5).id, E, amount, age + 1)
        report(5, E, ROMANCE, text, age)

    # ------------------------------------------------------------------
    # 7. ACCOUNT F: 4 reports about a fake investment group
    # ------------------------------------------------------------------
    F = acct_f.phone_number
    f_plan = [
        (3, 6, 6000, "Promised 40% weekly returns if I joined a 'private trading group'."),
        (4, 2, 3500, "Added to a chat group where members posted fake profit screenshots."),
        (6, 2, 8000, "Told to deposit more to 'unlock' my earnings, then could not withdraw."),
        (7, 1, 5000, "Same investment group. The organiser stopped replying after payment."),
    ]
    f_reports = []
    for reporter_no, age, amount, text in f_plan:
        payment(sender_user(reporter_no).id, F, amount, age + 1)
        f_reports.append(report(reporter_no, F, INVESTMENT, text, age))

    # ------------------------------------------------------------------
    # 8. NORMAL activity: B, G and H have no scam reports
    # ------------------------------------------------------------------
    B, G, H = acct_b.phone_number, acct_g.phone_number, acct_h.phone_number
    payment(sender_user(1).id, B, 250, 40)
    payment(sender_user(2).id, B, 400, 25)
    payment(sender_user(10).id, B, 120, 10)
    payment(sender_user(7).id, B, 600, 3)
    payment(acct_b.user_id, H, 150, 30)
    payment(acct_b.user_id, H, 200, 12)
    payment(sender_user(2).id, G, 300, 20)
    payment(sender_user(1).id, G, 150, 8)
    for _ in range(8):  # a small shop receiving everyday payments
        payment(sender_user(rng.randint(1, 10)).id, H, rng.randint(2, 30) * 10, rng.randint(1, 60))

    db.flush()  # the reports need ids before cases can link to them

    # ------------------------------------------------------------------
    # 9. SCAM CASES: investigations grouping reports and accounts
    # ------------------------------------------------------------------
    db.add(ScamCase(
        title="Fake job offer ring: 0912345678", scam_type=FAKE_JOB,
        description="Five recent reports of fake job offers asking for upfront fees. Account A has passed money on to account C.",
        status="INVESTIGATING", priority=1, created_at=ago(days=3), updated_at=ago(days=1),
        reports=a_reports[2:], accounts=[acct_a, acct_c],
    ))
    db.add(ScamCase(
        title="Advance-fee payment requests", scam_type=ADVANCE_FEE,
        description="Two earlier advance-fee reports linked to account A and a related account. Closed after the accounts were warned.",
        status="RESOLVED", priority=3, created_at=ago(days=10), updated_at=ago(days=7),
        reports=a_reports[:2], accounts=[acct_a, acct_d],
    ))
    db.add(ScamCase(
        title="Fake investment group", scam_type=INVESTMENT,
        description="Four reports of a 'private trading group' promising guaranteed returns. Accounts F and G share a device.",
        status="OPEN", priority=2, created_at=ago(days=1), updated_at=ago(hours=6),
        reports=f_reports, accounts=[acct_f, acct_g],
    ))

    # ------------------------------------------------------------------
    # 10. RELATIONSHIPS: connections between accounts
    # ------------------------------------------------------------------
    link(acct_a, acct_d, RelationshipType.RELATED_ACCOUNT, 7)
    link(acct_a, acct_c, RelationshipType.TRANSACTION, 1)
    link(acct_f, acct_g, RelationshipType.SHARED_DEVICE, 1)

    # ------------------------------------------------------------------
    # 11. RISK HISTORY and ALERTS
    # ------------------------------------------------------------------
    # Account A: risk climbs 32 -> 48 -> 82; the last one raises an OPEN alert
    assess(A, 32, ago(days=12) + timedelta(hours=2))
    assess(A, 48, ago(days=6) + timedelta(hours=2))
    assess(A, 82, ago(days=2) + timedelta(hours=2), "OPEN",
           "7 independent reports in 20 days; payment held. Review required.")
    assess(B, 8, ago(days=25))
    assess(B, 6, ago(days=3))
    assess(C, 44, ago(days=7))
    assess(C, 68, ago(days=1), "UNDER_REVIEW", "3 reports; receives funds from a high-risk account.")
    assess(D, 41, ago(days=5))
    assess(E, 52, ago(days=2))
    assess(F, 61, ago(days=2))
    assess(F, 74, ago(days=1), "OPEN", "4 reports of a fake investment group in 6 days.")
    assess(G, 18, ago(days=5))
    assess(H, 5, ago(days=2))


def print_summary(db: Session) -> None:
    print("Seed complete. Rows now in the database:")
    for model in (User, PaymentAccount, Transaction, FraudReport, ScamCase,
                  AccountRelationship, RiskAssessment, Alert):
        count = db.scalar(select(func.count()).select_from(model))
        print(f"  {model.__tablename__:<24}{count}")
    print("Try: 0912345678 (CRITICAL, 7 reports) and 0923456789 (LOW, 0 reports)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load fictional Adera demo data.")
    parser.add_argument("--reset", action="store_true",
                        help="delete ALL existing rows before loading the demo data")
    args = parser.parse_args()

    with SessionLocal() as db:
        has_data = db.scalar(select(func.count()).select_from(User)) > 0
        if has_data and not args.reset:
            sys.exit("The database already contains data. "
                     "Run again with --reset to wipe it and reload the demo data.")
        if has_data:
            reset(db)
        seed(db)
        db.commit()
        print_summary(db)


if __name__ == "__main__":
    main()
