
import json

from config import GROUND_TRUTH_DIR, PROCESSED_DATA_DIR


def evaluate_detection():
    ground_truth_file = GROUND_TRUTH_DIR / "edge_cases.json"
    detected_file = PROCESSED_DATA_DIR / "detected_edge_cases.json"

    with open(ground_truth_file, "r", encoding="utf-8") as file:
        ground_truth = json.load(file)

    with open(detected_file, "r", encoding="utf-8") as file:
        detected = json.load(file)

    expected = {
        (item["label"], item["record_id"])
        for item in ground_truth
    }

    actual = {
        (item["label"], item["record_id"])
        for item in detected
    }

    true_positives = expected & actual
    false_positives = actual - expected
    false_negatives = expected - actual

    tp = len(true_positives)
    fp = len(false_positives)
    fn = len(false_negatives)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    report = {
        "expected_cases": len(expected),
        "detected_cases": len(actual),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "correctly_detected": [
            {
                "label": label,
                "record_id": record_id,
            }
            for label, record_id in sorted(true_positives)
        ],
        "false_positives_details": [
            {
                "label": label,
                "record_id": record_id,
            }
            for label, record_id in sorted(false_positives)
        ],
        "missed_cases": [
            {
                "label": label,
                "record_id": record_id,
            }
            for label, record_id in sorted(false_negatives)
        ],
    }

    output_file = PROCESSED_DATA_DIR / "evaluation_report.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===================================")
    print(" EDGE CASE EVALUATION REPORT")
    print("===================================")
    print(f"Expected cases: {len(expected)}")
    print(f"Detected cases: {len(actual)}")
    print(f"True positives: {tp}")
    print(f"False positives: {fp}")
    print(f"False negatives: {fn}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1_score:.2%}")
    print("-----------------------------------")
    print(f"Report saved to: {output_file}")
    print("===================================")


if __name__ == "__main__":
    evaluate_detection()
