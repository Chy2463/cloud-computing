import json
import os
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_cases() -> list[dict[str, Any]]:
    cases_dir = _repo_root() / "tests" / "cases"
    cases: list[dict[str, Any]] = []
    for path in sorted(cases_dir.glob("tc*.json")):
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    return cases


def _load_evaluator():
    from importlib.util import module_from_spec, spec_from_file_location

    module_path = _repo_root() / "functions" / "processing" / "lambda_function.py"
    spec = spec_from_file_location("processing_lambda", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load processing lambda module")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _subset(d: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {k: d.get(k) for k in keys}


def main() -> int:
    os.environ.setdefault("PYTHONUTF8", "1")
    module = _load_evaluator()
    evaluate_submission = getattr(module, "evaluate_submission")

    required_keys = ["status", "category", "priority", "note"]
    cases = _load_cases()
    failures: list[str] = []

    for case in cases:
        case_id = str(case.get("id") or "UNKNOWN")
        input_data = case.get("input") or {}
        expected = case.get("expected") or {}

        result = evaluate_submission(input_data)
        actual_pick = _subset(result, required_keys)
        expected_pick = _subset(expected, required_keys)

        if actual_pick != expected_pick:
            failures.append(
                json.dumps(
                    {
                        "id": case_id,
                        "expected": expected_pick,
                        "actual": actual_pick,
                    },
                    ensure_ascii=False,
                )
            )

    if failures:
        print("FAIL")
        for row in failures:
            print(row)
        return 1

    print(f"PASS ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

