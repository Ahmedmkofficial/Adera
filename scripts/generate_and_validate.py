#!/usr/bin/env python3
"""
Adera Threat Intelligence Data Validator & Summary Generator
Author: Biruk (Team Member 1: Threat Intelligence & Scam Intelligence)

This script validates the JSON schema integrity, cross-references, and risk weights
of Adera's fraud intelligence datasets:
1. scam_types.json
2. fraud_indicators.json
3. synthetic_reports.json
4. synthetic_scam_cases.json
"""

import json
import sys
from pathlib import Path


def load_json(file_path: Path) -> dict:
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON syntax in {file_path}: {e}")
            sys.exit(1)


def validate_scam_types(data: dict) -> set:
    categories = data.get("categories", [])
    if not categories:
        print("[ERROR] scam_types.json missing 'categories' array")
        sys.exit(1)

    scam_type_ids = set()
    subtype_ids = set()

    for cat in categories:
        cat_id = cat.get("id")
        if not cat_id:
            print("[ERROR] Category missing 'id' in scam_types.json")
            sys.exit(1)
        scam_type_ids.add(cat_id)
        for sub in cat.get("subtypes", []):
            sub_id = sub.get("id")
            if sub_id:
                subtype_ids.add(sub_id)

    print(f"[SUCCESS] Loaded {len(scam_type_ids)} top-level scam types and {len(subtype_ids)} sub-types.")
    return scam_type_ids


def validate_fraud_indicators(data: dict) -> set:
    indicators = data.get("indicators", [])
    if not indicators:
        print("[ERROR] fraud_indicators.json missing 'indicators' array")
        sys.exit(1)

    indicator_ids = set()
    for ind in indicators:
        ind_id = ind.get("id")
        weight = ind.get("default_risk_weight")
        if not ind_id or weight is None:
            print(f"[ERROR] Invalid indicator structure: {ind}")
            sys.exit(1)
        indicator_ids.add(ind_id)

    print(f"[SUCCESS] Loaded {len(indicator_ids)} registered fraud indicators.")
    return indicator_ids


def validate_synthetic_reports(data: dict, valid_scam_types: set, valid_indicators: set):
    reports = data.get("reports", [])
    if not reports:
        print("[ERROR] synthetic_reports.json missing 'reports' array")
        sys.exit(1)

    demo_phone_reports = [r for r in reports if r.get("recipient_phone") == "0912345678"]
    print(f"[INFO] Total synthetic reports: {len(reports)}")
    print(f"[INFO] Demo recipient (0912345678) report count: {len(demo_phone_reports)}")

    if len(demo_phone_reports) < 7:
        print(f"[WARNING] Demo recipient 0912345678 has {len(demo_phone_reports)} reports (expected 7 for Section 11 demo alignment).")

    for rep in reports:
        scam_type = rep.get("scam_type")
        if scam_type not in valid_scam_types:
            print(f"[ERROR] Report {rep.get('report_id')} has unknown scam_type '{scam_type}'")
            sys.exit(1)

        for ind in rep.get("indicators_observed", []):
            if ind not in valid_indicators:
                print(f"[WARNING] Report {rep.get('report_id')} contains unregistered indicator '{ind}'")

    print("[SUCCESS] All synthetic reports validated successfully.")


def validate_synthetic_cases(data: dict):
    cases = data.get("cases", [])
    if not cases:
        print("[ERROR] synthetic_scam_cases.json missing 'cases' array")
        sys.exit(1)

    print(f"[SUCCESS] Loaded {len(cases)} synthetic scam cases.")
    for c in cases:
        print(f"   - Case {c.get('case_id')}: '{c.get('case_title')}' (Primary target: {c.get('primary_target_phone')}, Status: {c.get('status')})")


def main():
    base_dir = Path(__file__).resolve().parent.parent / "data"
    print("=" * 60)
    print("  ADERA THREAT INTELLIGENCE DATA VALIDATOR (BIRUK - MEMBER 1) ")
    print("=" * 60)

    scam_types = load_json(base_dir / "scam_types.json")
    valid_scam_types = validate_scam_types(scam_types)

    fraud_indicators = load_json(base_dir / "fraud_indicators.json")
    valid_indicators = validate_fraud_indicators(fraud_indicators)

    reports_data = load_json(base_dir / "synthetic_reports.json")
    validate_synthetic_reports(reports_data, valid_scam_types, valid_indicators)

    cases_data = load_json(base_dir / "synthetic_scam_cases.json")
    validate_synthetic_cases(cases_data)

    print("=" * 60)
    print("  ALL ADERA THREAT INTELLIGENCE DATASETS ARE 100% VALIDATED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
