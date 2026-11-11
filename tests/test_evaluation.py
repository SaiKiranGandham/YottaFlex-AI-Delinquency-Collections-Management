
import json

from config import GROUND_TRUTH_DIR, PROCESSED_DATA_DIR


def test_edge_case_evaluation():
    report_path = PROCESSED_DATA_DIR / "evaluation_report.json"

    assert report_path.exists(), "Evaluation report is missing."

    with open(report_path, "r", encoding="utf-8") as file:
        report = json.load(file)

    assert report["expected_cases"] == 5
    assert report["detected_cases"] == 5
    assert report["true_positives"] == 5
    assert report["false_positives"] == 0
    assert report["false_negatives"] == 0
    assert report["precision"] == 1.0
    assert report["recall"] == 1.0
    assert report["f1_score"] == 1.0


def test_ground_truth_file_exists():
    assert (GROUND_TRUTH_DIR / "edge_cases.json").exists()
