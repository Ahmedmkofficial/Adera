"""Focused tests for offline threat-intelligence data validation."""

import copy
import json
import subprocess
import sys
from pathlib import Path

from scripts.generate_and_validate import DATA_FILES, validate_data_dir, validate_documents


def valid_documents():
    return {
        "taxonomy": {"$schema": "schema", "version": "1", "domain": "test", "categories": [{"id": "impersonation", "name": "Impersonation", "description": "Description", "severity": "HIGH", "subtypes": [{"id": "family_impersonation", "name": "Family impersonation", "description": "Description", "common_channels": ["SMS"], "typical_indicators": ["urgent_request"]}]}]},
        "indicators": {"$schema": "schema", "version": "1", "indicators": [{"id": "urgent_request", "name": "Urgency", "category": "BEHAVIORAL", "default_risk_weight": 10, "evidence_strength": "WEAK", "confidence_impact": "LOW", "description": "Description", "eval_rule": "Rule"}]},
        "reports": {"$schema": "schema", "description": "Test reports", "reports": [{"report_id": "REP-2026-0001", "reporter_phone": "0911111111", "recipient_phone": "0922222222", "recipient_name": "Recipient", "scam_type": "impersonation", "scam_subtype": "family_impersonation", "amount_etb": 100, "timestamp": "2026-10-08T14:30:00Z", "status": "UNVERIFIED", "confidence_level": "REPORTED", "indicators_observed": ["urgent_request"], "victim_narrative": "A sufficiently detailed synthetic report.", "evidence_attachment": None}]},
        "cases": {"$schema": "schema", "description": "Test cases", "cases": [{"case_id": "CASE-0001", "case_title": "Example case", "primary_target_phone": "0922222222", "primary_target_name": "Recipient", "scam_type": "impersonation", "scam_subtype": "family_impersonation", "confidence_level": "SUSPICIOUS", "total_reports": 1, "recent_reports_7days": 1, "suspicious_connected_accounts": 0, "linked_phones": ["0922222222"], "linked_report_ids": ["REP-2026-0001"], "total_victim_loss_etb": 100, "status": "OPEN", "assigned_analyst": "Analyst", "first_detected": "2026-10-08T14:30:00Z", "last_activity": "2026-10-08T14:30:00Z", "analyst_notes": "Synthetic test case."}]},
    }


def validate(documents):
    return validate_documents(documents["taxonomy"], documents["indicators"], documents["reports"], documents["cases"])


def test_valid_documents_have_no_errors_or_warnings():
    assert validate(valid_documents()) == ([], [])


def test_duplicate_report_id_and_conflicting_metadata_are_reported():
    documents = valid_documents()
    duplicate = copy.deepcopy(documents["reports"]["reports"][0])
    duplicate["victim_narrative"] = "Different record metadata."
    documents["reports"]["reports"].append(duplicate)

    errors, _ = validate(documents)

    assert any("conflicting metadata" in error for error in errors)


def test_duplicate_indicator_and_case_ids_are_reported():
    documents = valid_documents()
    documents["indicators"]["indicators"].append(copy.deepcopy(documents["indicators"]["indicators"][0]))
    documents["cases"]["cases"].append(copy.deepcopy(documents["cases"]["cases"][0]))

    errors, _ = validate(documents)

    assert any("fraud_indicators.json.indicators[1].id: duplicate record" in error for error in errors)
    assert any("synthetic_scam_cases.json.cases[1].case_id: duplicate record" in error for error in errors)


def test_unknown_taxonomy_indicator_and_case_report_link_are_reported():
    documents = valid_documents()
    documents["taxonomy"]["categories"][0]["subtypes"][0]["typical_indicators"].append("missing_signal")
    documents["cases"]["cases"][0]["linked_report_ids"] = ["REP-2099-9999"]

    errors, _ = validate(documents)

    assert any("unknown indicator 'missing_signal'" in error for error in errors)
    assert any("unknown report ID 'REP-2099-9999'" in error for error in errors)


def test_malformed_field_types_return_record_level_errors():
    documents = valid_documents()
    documents["taxonomy"]["categories"][0]["name"] = 42
    documents["reports"]["reports"][0]["amount_etb"] = "100"

    errors, _ = validate(documents)

    assert any("scam_taxonomy.json.categories[0].name: expected str" in error for error in errors)
    assert any("synthetic_reports.json.reports[0].amount_etb: expected int or float" in error for error in errors)


def test_report_id_year_mismatch_and_case_total_mismatch_are_reported():
    documents = valid_documents()
    documents["reports"]["reports"][0]["timestamp"] = "2025-10-08T14:30:00Z"
    documents["cases"]["cases"][0]["total_reports"] = 2

    errors, warnings = validate(documents)

    assert any("conflicts with report ID year" in error for error in errors)
    assert any("declares 2, but lists 1 linked reports" in warning for warning in warnings)


def test_case_count_discrepancy_is_warning_not_error():
    documents = valid_documents()
    documents["cases"]["cases"][0]["total_reports"] = 2

    errors, warnings = validate(documents)

    assert errors == []
    assert len(warnings) == 1
    assert "declares 2, but lists 1 linked reports" in warnings[0]


def test_validation_does_not_modify_input_documents():
    documents = valid_documents()
    original = copy.deepcopy(documents)

    validate(documents)

    assert documents == original


def test_validation_does_not_modify_source_files(tmp_path):
    documents = valid_documents()
    source_data = {
        "scam_taxonomy.json": documents["taxonomy"],
        "fraud_indicators.json": documents["indicators"],
        "synthetic_reports.json": documents["reports"],
        "synthetic_scam_cases.json": documents["cases"],
    }
    for filename in DATA_FILES:
        (tmp_path / filename).write_text(json.dumps(source_data[filename]), encoding="utf-8")
    original_bytes = {filename: (tmp_path / filename).read_bytes() for filename in DATA_FILES}

    errors, warnings = validate_data_dir(tmp_path)

    assert errors == []
    assert warnings == []
    assert {filename: (tmp_path / filename).read_bytes() for filename in DATA_FILES} == original_bytes


def test_cli_exits_nonzero_when_repository_data_has_validation_errors():
    repository_root = Path(__file__).resolve().parents[1]
    validator = repository_root / "scripts" / "generate_and_validate.py"

    result = subprocess.run(
        [sys.executable, str(validator)],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "[ERROR]" in result.stdout
    assert "[WARNING]" in result.stdout