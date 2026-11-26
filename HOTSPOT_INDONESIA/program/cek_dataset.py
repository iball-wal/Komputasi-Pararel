
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE_DATASET = (
    BASE_DIR / "dataset" / "viirs_snpp_2025_indonesia.csv"
)

jumlah_data = 0

with open(FILE_DATASET, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    print("Kolom dataset:")
    print(reader.fieldnames)

    for row in reader:
        jumlah_data += 1

print("\n=== HASIL PEMERIKSAAN DATASET ===")
print("Jumlah data hotspot:", jumlah_data)
