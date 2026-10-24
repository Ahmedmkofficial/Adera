#!/usr/bin/env python3
"""Validate Adera's offline threat-intelligence JSON datasets."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_FILES = (
    "scam_taxonomy.json",
    "fraud_indicators.json",
    "synthetic_reports.json",
    "synthetic_scam_cases.json",
)
REPORT_ID_PATTERN = re.compile(r"^REP-(\d{4})-\d{4}$")


def _unique_ids(records: list[Any], id_field: str, label: str, errors: list[str]) -> set[str]:
    seen: dict[str, Any] = {}
    for index, record in enumerate(records):
        location = f"{label}[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{location}: expected an object")
            continue
        record_id = record.get(id_field)
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{location}.{id_field}: required non-empty string")
            continue
        if record_id in seen:
            detail = "conflicting metadata" if seen[record_id] != record else "duplicate record"
            errors.append(f"{location}.{id_field}: {detail} for {record_id!r}")
        else:
            seen[record_id] = record
    return set(seen)


def _required_fields(
    record: dict[str, Any], fields: dict[str, type | tuple[type, ...]], location: str, errors: list[str]
) -> None:
    for field, expected_type in fields.items():
        value = record.get(field)
        if value is None:
            errors.append(f"{location}.{field}: required field is missing")
        elif not isinstance(value, expected_type) or (
            expected_type is int and isinstance(value, bool)
        ):
            if isinstance(expected_type, tuple):
                expected = " or ".join(item.__name__ for item in expected_type)
            else:
                expected = expected_type.__name__
            errors.append(f"{location}.{field}: expected {expected}")


def validate_documents(
    taxonomy: Any, indicators_data: Any, reports_data: Any, cases_data: Any
) -> tuple[list[str], list[str]]:
    """Return deterministic validation errors and warnings for parsed documents."""
    errors: list[str] = []
    warnings: list[str] = []
    documents = (
        ("scam_taxonomy.json", taxonomy, "categories", {"$schema": str, "version": str, "domain": str}),
        ("fraud_indicators.json", indicators_data, "indicators", {"$schema": str, "version": str}),
        ("synthetic_reports.json", reports_data, "reports", {"$schema": str, "description": str}),
        ("synthetic_scam_cases.json", cases_data, "cases", {"$schema": str, "description": str}),
    )
    arrays: dict[str, list[Any]] = {}
    for filename, document, key, metadata_fields in documents:
        if not isinstance(document, dict):
            errors.append(f"{filename}: top-level JSON value must be an object")
            arrays[key] = []
            continue
        _required_fields(document, metadata_fields, filename, errors)
        values = document.get(key)
        if not isinstance(values, list):
            errors.append(f"{filename}.{key}: required array")
            arrays[key] = []
            continue
        if not values:
            errors.append(f"{filename}.{key}: must not be empty")
        arrays[key] = values

    categories = arrays["categories"]
    category_ids = _unique_ids(categories, "id", "scam_taxonomy.json.categories", errors)
    subtype_ids: set[str] = set()
    taxonomy_subtype_categories: dict[str, str] = {}
    for cat_index, category in enumerate(categories):
        if not isinstance(category, dict):
            continue
        cat_location = f"scam_taxonomy.json.categories[{cat_index}]"
        _required_fields(category, {"name": str, "description": str, "severity": str, "subtypes": list}, cat_location, errors)
        subtypes = category.get("subtypes")
        if not isinstance(subtypes, list):
            continue
        for subtype_index, subtype in enumerate(subtypes):
            if not isinstance(subtype, dict):
                continue
            subtype_id = subtype.get("id")
            if isinstance(subtype_id, str) and subtype_id.strip():
                if subtype_id in taxonomy_subtype_categories:
                    errors.append(f"{cat_location}.subtypes[{subtype_index}].id: duplicate subtype ID {subtype_id!r}")
                else:
                    subtype_ids.add(subtype_id)
                    taxonomy_subtype_categories[subtype_id] = category.get("id", "")
        for subtype_index, subtype in enumerate(subtypes):
            if not isinstance(subtype, dict):
                continue
            location = f"{cat_location}.subtypes[{subtype_index}]"
            _required_fields(subtype, {"name": str, "description": str, "common_channels": list, "typical_indicators": list}, location, errors)
            channels = subtype.get("common_channels")
            if isinstance(channels, list) and any(not isinstance(channel, str) for channel in channels):
                errors.append(f"{location}.common_channels: entries must be strings")
            refs = subtype.get("typical_indicators")
            if isinstance(refs, list):
                for ref_index, ref in enumerate(refs):
                    if not isinstance(ref, str):
                        errors.append(f"{location}.typical_indicators[{ref_index}]: expected string")

    indicators = arrays["indicators"]
    indicator_ids = _unique_ids(indicators, "id", "fraud_indicators.json.indicators", errors)
    for index, indicator in enumerate(indicators):
        if isinstance(indicator, dict):
            _required_fields(
                indicator,
                {"name": str, "category": str, "default_risk_weight": int, "evidence_strength": str,
                 "confidence_impact": str, "description": str, "eval_rule": str},
                f"fraud_indicators.json.indicators[{index}]", errors,
            )
    for cat_index, category in enumerate(categories):
        if not isinstance(category, dict) or not isinstance(category.get("subtypes"), list):
            continue
        for subtype_index, subtype in enumerate(category["subtypes"]):
            if not isinstance(subtype, dict) or not isinstance(subtype.get("typical_indicators"), list):
                continue
            for ref_index, indicator_id in enumerate(subtype["typical_indicators"]):
                if isinstance(indicator_id, str) and indicator_id not in indicator_ids:
                    errors.append(
                        f"scam_taxonomy.json.categories[{cat_index}].subtypes[{subtype_index}]."
                        f"typical_indicators[{ref_index}]: unknown indicator {indicator_id!r}; "
                        "add it to fraud_indicators.json or correct the reference"
                    )

    reports = arrays["reports"]
    report_ids = _unique_ids(reports, "report_id", "synthetic_reports.json.reports", errors)
    report_fields = {
        "reporter_phone": str, "recipient_phone": str, "recipient_name": str,
        "scam_type": str, "scam_subtype": str, "amount_etb": (int, float),
        "timestamp": str, "status": str, "confidence_level": str,
        "indicators_observed": list, "victim_narrative": str,
    }
    for index, report in enumerate(reports):
        if not isinstance(report, dict):
            continue
        location = f"synthetic_reports.json.reports[{index}]"
        _required_fields(report, report_fields, location, errors)
        report_id, timestamp = report.get("report_id"), report.get("timestamp")
        if isinstance(report_id, str) and isinstance(timestamp, str):
            match = REPORT_ID_PATTERN.fullmatch(report_id)
            if not match:
                errors.append(f"{location}.report_id: expected REP-YYYY-NNNN format")
            else:
                try:
                    parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{location}.timestamp: invalid ISO 8601 timestamp {timestamp!r}")
                else:
                    if int(match.group(1)) != parsed_timestamp.year:
                        errors.append(
                            f"{location}.timestamp: year {parsed_timestamp.year} conflicts with "
                            f"report ID year {match.group(1)}"
                        )
        scam_type = report.get("scam_type")
        if isinstance(scam_type, str) and scam_type not in category_ids:
            errors.append(f"{location}.scam_type: unknown taxonomy category {scam_type!r}")
        scam_subtype = report.get("scam_subtype")
        if isinstance(scam_subtype, str) and scam_subtype not in subtype_ids:
            errors.append(f"{location}.scam_subtype: unknown taxonomy subtype {scam_subtype!r}")
        elif isinstance(scam_type, str) and isinstance(scam_subtype, str):
            if taxonomy_subtype_categories.get(scam_subtype) != scam_type:
                errors.append(f"{location}.scam_subtype: subtype {scam_subtype!r} does not belong to {scam_type!r}")
        observed = report.get("indicators_observed")
        if isinstance(observed, list):
            for ref_index, indicator_id in enumerate(observed):
                if not isinstance(indicator_id, str):
                    errors.append(f"{location}.indicators_observed[{ref_index}]: expected string")
                elif indicator_id not in indicator_ids:
                    errors.append(f"{location}.indicators_observed[{ref_index}]: unknown indicator {indicator_id!r}")

    cases = arrays["cases"]
    _unique_ids(cases, "case_id", "synthetic_scam_cases.json.cases", errors)
    case_fields = {
        "case_title": str, "primary_target_phone": str, "primary_target_name": str,
        "scam_type": str, "scam_subtype": str, "confidence_level": str,
        "total_reports": int, "recent_reports_7days": int,
        "suspicious_connected_accounts": int, "linked_phones": list,
        "linked_report_ids": list, "total_victim_loss_etb": (int, float),
        "status": str, "assigned_analyst": str, "first_detected": str,
        "last_activity": str, "analyst_notes": str,
    }
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        location = f"synthetic_scam_cases.json.cases[{index}]"
        _required_fields(case, case_fields, location, errors)
        scam_type = case.get("scam_type")
        scam_subtype = case.get("scam_subtype")
        if isinstance(scam_type, str) and scam_type not in category_ids:
            errors.append(f"{location}.scam_type: unknown taxonomy category {scam_type!r}")
        if isinstance(scam_subtype, str) and scam_subtype not in subtype_ids:
            errors.append(f"{location}.scam_subtype: unknown taxonomy subtype {scam_subtype!r}")
        elif isinstance(scam_type, str) and isinstance(scam_subtype, str):
            if taxonomy_subtype_categories.get(scam_subtype) != scam_type:
                errors.append(f"{location}.scam_subtype: subtype {scam_subtype!r} does not belong to {scam_type!r}")
        for field in ("first_detected", "last_activity"):
            value = case.get(field)
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{location}.{field}: invalid ISO 8601 timestamp {value!r}")
        linked_ids = case.get("linked_report_ids")
        if isinstance(linked_ids, list):
            for link_index, linked_id in enumerate(linked_ids):
                if not isinstance(linked_id, str):
                    errors.append(f"{location}.linked_report_ids[{link_index}]: expected string")
                elif linked_id not in report_ids:
                    errors.append(f"{location}.linked_report_ids[{link_index}]: unknown report ID {linked_id!r}")
            total = case.get("total_reports")
            if isinstance(total, int) and not isinstance(total, bool) and total != len(linked_ids):
                warnings.append(
                    f"{location}.total_reports: declares {total}, but lists {len(linked_ids)} linked reports; "
                    "confirm whether linked_report_ids is a complete list"
                )
    return errors, warnings


def validate_data_dir(data_dir: Path) -> tuple[list[str], list[str]]:
    documents: dict[str, Any] = {}
    for filename in DATA_FILES:
        try:
            with (data_dir / filename).open(encoding="utf-8") as source:
                documents[filename] = json.load(source)
        except FileNotFoundError:
            return [f"{filename}: file not found"], []
        except json.JSONDecodeError as exc:
            return [f"{filename}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"], []
        except OSError as exc:
            return [f"{filename}: cannot read file: {exc}"], []
    return validate_documents(
        documents["scam_taxonomy.json"], documents["fraud_indicators.json"],
        documents["synthetic_reports.json"], documents["synthetic_scam_cases.json"],
    )


def main() -> int:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    errors, warnings = validate_data_dir(data_dir)
    for warning in warnings:
        print(f"[WARNING] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        print(f"Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1
    print(f"Threat-intelligence datasets validated with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
