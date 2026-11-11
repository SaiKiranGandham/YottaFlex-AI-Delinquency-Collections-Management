
import hashlib
import subprocess
import sys

from config import RAW_DATA_DIR, BASE_DIR


def run_command(command):
    subprocess.run(
        command,
        cwd=BASE_DIR,
        check=True,
    )


def calculate_checksums():
    checksums = {}

    for file_path in sorted(RAW_DATA_DIR.iterdir()):
        if file_path.is_file():
            file_hash = hashlib.sha256(
                file_path.read_bytes()
            ).hexdigest()

            checksums[file_path.name] = file_hash

    return checksums


def check_reproducibility():
    print("\nRUN 1: Generate starter dataset")
    run_command([sys.executable, "main.py", "--scale", "starter"])
    run_command([sys.executable, "-m", "src.services.export_service"])
    first_run = calculate_checksums()

    print("\nRUN 2: Generate starter dataset again")
    run_command([sys.executable, "main.py", "--scale", "starter"])
    run_command([sys.executable, "-m", "src.services.export_service"])
    second_run = calculate_checksums()

    print("\n===================================")
    print(" REPRODUCIBILITY TEST")
    print("===================================")

    if first_run == second_run:
        print("PASS: Both runs produced identical files.")
        print("All SHA-256 checksums match.")
        return True

    print("FAIL: Generated files are different.")

    for filename in sorted(set(first_run) | set(second_run)):
        if first_run.get(filename) != second_run.get(filename):
            print(f"Mismatch: {filename}")

    return False


if __name__ == "__main__":
    if not check_reproducibility():
        raise SystemExit(1)
