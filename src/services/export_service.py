
import json
import sqlite3

import pandas as pd
from sqlalchemy import inspect

from src.database import engine
from config import RAW_DATA_DIR, DATABASE_PATH


def export_all_tables():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    manifest = {
        "project": "YottaFlex AI Delinquency & Collections Management",
        "database": "SQLite",
        "export_format": ["CSV", "JSON", "SQL"],
        "tables": [],
    }

    print("\n===================================")
    print(" DATABASE EXPORT")
    print("===================================")

    for table_name in table_names:
        dataframe = pd.read_sql_table(table_name, engine)

        csv_path = RAW_DATA_DIR / f"{table_name}.csv"
        json_path = RAW_DATA_DIR / f"{table_name}.json"

        dataframe.to_csv(csv_path, index=False)

        records = dataframe.astype(object).where(
            pd.notna(dataframe), None
        ).to_dict(orient="records")

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, default=str)

        manifest["tables"].append({
            "table": table_name,
            "record_count": len(dataframe),
            "csv_file": csv_path.name,
            "json_file": json_path.name,
        })

        print(f"Exported: {table_name} ({len(dataframe)} records)")

    manifest_path = RAW_DATA_DIR / "source_manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    print("-----------------------------------")
    print(f"Exported tables: {len(table_names)}")
    print(f"Manifest: {manifest_path}")
    print("CSV AND JSON EXPORT COMPLETED")


def export_sql_dump():
    sql_path = RAW_DATA_DIR / "yottaflex_seed.sql"

    with sqlite3.connect(DATABASE_PATH) as connection:
        dump = "\n".join(connection.iterdump())

    with open(sql_path, "w", encoding="utf-8") as file:
        file.write("-- YottaFlex synthetic database SQL seed\n")
        file.write("PRAGMA foreign_keys=OFF;\n\n")
        file.write(dump)
        file.write("\n")

    print(f"SQL seed exported: {sql_path}")


if __name__ == "__main__":
    export_all_tables()
    export_sql_dump()

