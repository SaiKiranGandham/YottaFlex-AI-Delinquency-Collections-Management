
import csv
import json
import sqlite3

from config import RAW_DATA_DIR


def verify_exports():
    manifest_path = RAW_DATA_DIR / "source_manifest.json"
    sql_path = RAW_DATA_DIR / "yottaflex_seed.sql"

    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = json.load(file)

    errors = []

    print("\n===================================")
    print(" EXPORT VERIFICATION")
    print("===================================")

    # Verify CSV and JSON files
    for table in manifest["tables"]:
        table_name = table["table"]
        expected_count = table["record_count"]

        csv_path = RAW_DATA_DIR / table["csv_file"]
        json_path = RAW_DATA_DIR / table["json_file"]

        with open(csv_path, "r", encoding="utf-8", newline="") as file:
            csv_count = sum(1 for _ in csv.DictReader(file))

        with open(json_path, "r", encoding="utf-8") as file:
            json_records = json.load(file)

        json_count = len(json_records)

        if csv_count != expected_count:
            errors.append(f"CSV count mismatch: {table_name}")

        if json_count != expected_count:
            errors.append(f"JSON count mismatch: {table_name}")

        print(
            f"{table_name}: CSV={csv_count}, "
            f"JSON={json_count}, Expected={expected_count}"
        )

    # Restore SQL dump into an in-memory database
    if not sql_path.exists():
        errors.append("SQL seed file is missing.")
    else:
        memory_db = sqlite3.connect(":memory:")

        try:
            with open(sql_path, "r", encoding="utf-8") as file:
                memory_db.executescript(file.read())

            for table in manifest["tables"]:
                table_name = table["table"]
                expected_count = table["record_count"]

                restored_count = memory_db.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]

                if restored_count != expected_count:
                    errors.append(
                        f"SQL count mismatch: {table_name}"
                    )

            print("\nSQL seed restoration: SUCCESS")

        except sqlite3.Error as error:
            errors.append(f"SQL restoration failed: {error}")

        finally:
            memory_db.close()

    print("\n-----------------------------------")

    if errors:
        print(f"VERIFICATION FAILED: {len(errors)} issue(s)")
        for error in errors:
            print("-", error)
    else:
        print("ALL EXPORTS VERIFIED SUCCESSFULLY!")

    print("===================================")

    return len(errors) == 0


if __name__ == "__main__":
    if not verify_exports():
        raise SystemExit(1)
