from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models.fraud_report import FraudReport
from backend.models.payment_account import PaymentAccount
from backend.models.relationship import AccountRelationship
from backend.models.scam_case import ScamCase
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.services.fraud_intelligence import get_recipient_intelligence
from backend.services.risk_engine import calculate_risk


def _profile_for_phone(db: Session, phone: str) -> tuple[dict, dict]:
    intelligence = get_recipient_intelligence(db, phone)
    risk = calculate_risk(
        report_count=intelligence["total_reports"],
        recent_report_count=intelligence["recent_reports"],
        related_case_count=intelligence["previous_scam_cases"],
        suspicious_connection_count=intelligence["suspicious_relationships"],
        independent_report_count=intelligence["independent_reporters"],
        repeated_scam_pattern=intelligence["repeated_scam_pattern"],
        unusual_transaction=False,
        transaction_amount=0,
    )
    return intelligence, risk


def _later(current: datetime | None, candidate: datetime | None) -> datetime | None:
    if candidate is None:
        return current
    if current is None or candidate.timestamp() > current.timestamp():
        return candidate
    return current


def build_recipient_graph(db: Session, recipient: User) -> dict:
    root_id = f"subject-{recipient.id}"
    root_accounts = {
        account_id
        for (account_id,) in db.query(PaymentAccount.id)
        .filter(PaymentAccount.user_id == recipient.id)
        .all()
    }

    relationships = []
    if root_accounts:
        relationships = (
            db.query(AccountRelationship)
            .filter(
                or_(
                    AccountRelationship.source_account_id.in_(root_accounts),
                    AccountRelationship.target_account_id.in_(root_accounts),
                )
            )
            .order_by(AccountRelationship.id)
            .all()
        )

    linked_account_ids = {
        relation.target_account_id
        if relation.source_account_id in root_accounts
        else relation.source_account_id
        for relation in relationships
    } - root_accounts
    linked_accounts = {}
    if linked_account_ids:
        linked_accounts = {
            account.id: (account, user)
            for account, user in db.query(PaymentAccount, User)
            .join(User, User.id == PaymentAccount.user_id)
            .filter(PaymentAccount.id.in_(linked_account_ids))
            .all()
        }

    transactions = (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.sender_id == recipient.id,
                Transaction.recipient_phone == recipient.phone,
            )
        )
        .order_by(Transaction.id)
        .all()
    )
    sender_ids = {txn.sender_id for txn in transactions if txn.sender_id != recipient.id}
    senders = (
        {
            user.id: user
            for user in db.query(User).filter(User.id.in_(sender_ids)).all()
        }
        if sender_ids
        else {}
    )
    outgoing_phones = {
        txn.recipient_phone
        for txn in transactions
        if txn.sender_id == recipient.id and txn.recipient_phone != recipient.phone
    }
    outgoing_users = (
        {
            user.phone: user
            for user in db.query(User).filter(User.phone.in_(outgoing_phones)).all()
        }
        if outgoing_phones
        else {}
    )

    peer_users = {}
    peer_last_activity = {}
    relationship_edges = []
    for relation in relationships:
        linked_account_id = (
            relation.target_account_id
            if relation.source_account_id in root_accounts
            else relation.source_account_id
        )
        account_and_user = linked_accounts.get(linked_account_id)
        if account_and_user is None:
            continue
        _, user = account_and_user
        if user.id == recipient.id:
            continue
        peer_users[user.phone] = user
        peer_last_activity[user.phone] = _later(
            peer_last_activity.get(user.phone), relation.created_at
        )
        peer_id = f"account-{user.id}"
        source, target = (
            (root_id, peer_id)
            if relation.source_account_id in root_accounts
            else (peer_id, root_id)
        )
        relationship_edges.append(
            {
                "id": f"relationship-{relation.id}",
                "source": source,
                "target": target,
                "type": relation.relationship_type,
            }
        )

    transaction_edges = []
    for txn in transactions:
        if txn.sender_id == recipient.id:
            peer_phone = txn.recipient_phone
            peer_user = outgoing_users.get(peer_phone)
        else:
            peer_user = senders.get(txn.sender_id)
            if peer_user is None:
                continue
            peer_phone = peer_user.phone

        if peer_phone == recipient.phone:
            continue
        if peer_user is not None:
            peer_users[peer_phone] = peer_user
        peer_last_activity[peer_phone] = _later(
            peer_last_activity.get(peer_phone), txn.created_at
        )
        peer_id = f"account-{peer_user.id}" if peer_user else f"account-phone-{peer_phone}"
        source, target = (
            (root_id, peer_id)
            if txn.sender_id == recipient.id
            else (peer_id, root_id)
        )
        transaction_edges.append(
            {
                "id": f"transaction-{txn.id}",
                "source": source,
                "target": target,
                "type": "TRANSACTION",
            }
        )

    reports = (
        db.query(FraudReport)
        .filter(FraudReport.recipient_phone == recipient.phone)
        .order_by(FraudReport.id)
        .all()
    )
    latest_report_activity = None
    report_nodes = []
    report_edges = []
    for report in reports:
        latest_report_activity = _later(latest_report_activity, report.created_at)
        report_node_id = f"report-{report.id}"
        report_nodes.append(
            {
                "id": report_node_id,
                "kind": "report",
                "report_id": report.id,
                "created_at": report.created_at,
                "scam_type": report.scam_type,
                "summary": report.description,
            }
        )
        report_edges.append(
            {
                "id": f"report-edge-{report.id}",
                "source": root_id,
                "target": report_node_id,
                "type": "REPORT",
            }
        )

    peer_phones = set(peer_users) | set(peer_last_activity)
    if peer_phones:
        report_activity = (
            db.query(FraudReport.recipient_phone, FraudReport.created_at)
            .filter(FraudReport.recipient_phone.in_(peer_phones))
            .all()
        )
        for phone, created_at in report_activity:
            peer_last_activity[phone] = _later(peer_last_activity.get(phone), created_at)

        case_activity = (
            db.query(ScamCase.recipient_phone, ScamCase.created_at)
            .filter(ScamCase.recipient_phone.in_(peer_phones))
            .all()
        )
        for phone, created_at in case_activity:
            peer_last_activity[phone] = _later(peer_last_activity.get(phone), created_at)

    root_last_activity = latest_report_activity
    for txn in transactions:
        root_last_activity = _later(root_last_activity, txn.created_at)
    for relation in relationships:
        root_last_activity = _later(root_last_activity, relation.created_at)

    _, root_risk = _profile_for_phone(db, recipient.phone)
    nodes = [
        {
            "id": root_id,
            "kind": "subject",
            "phone": recipient.phone,
            "level": root_risk["level"],
            "score": root_risk["score"],
            "report_count": len(reports),
            "last_activity": root_last_activity,
        }
    ]

    for phone in sorted(peer_phones):
        peer = peer_users.get(phone)
        peer_intelligence, peer_risk = _profile_for_phone(db, phone)
        nodes.append(
            {
                "id": f"account-{peer.id}" if peer else f"account-phone-{phone}",
                "kind": "account",
                "phone": phone,
                "level": peer_risk["level"],
                "score": peer_risk["score"],
                "report_count": peer_intelligence["total_reports"],
                "last_activity": peer_last_activity.get(phone),
            }
        )

    nodes.extend(report_nodes)
    return {
        "phone": recipient.phone,
        "reports_total": len(reports),
        "nodes": nodes,
        "edges": relationship_edges + transaction_edges + report_edges,
    }
