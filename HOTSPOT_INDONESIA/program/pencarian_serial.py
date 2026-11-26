
import csv
import math
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_DATASET = BASE_DIR / "dataset" / "viirs_snpp_2025_indonesia.csv"

# Mengubah nama wilayah menjadi koordinat
def cari_koordinat(nama_wilayah):
    url = "https://nominatim.openstreetmap.org/search"

    parameter = {
        "q": nama_wilayah + ", Indonesia",
        "format": "jsonv2",
        "limit": 1
    }

    headers = {
        "User-Agent": "HotspotIndonesiaStudentProject/1.0"
    }

    try:
        response = requests.get(
            url,
            params=parameter,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()
        hasil = response.json()

        if not hasil:
            return None

        return {
            "nama": hasil[0]["display_name"],
            "latitude": float(hasil[0]["lat"]),
            "longitude": float(hasil[0]["lon"])
        }

    except requests.RequestException as error:
        print("Gagal menghubungi layanan lokasi:", error)
        return None


# Membaca dataset hotspot
def baca_dataset():
    data_hotspot = []

    with open(FILE_DATASET, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            data_hotspot.append({
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "tanggal": row["acq_date"],
                "waktu": row["acq_time"],
                "confidence": row["confidence"],
                "frp": float(row["frp"])
            })

    return data_hotspot


# Menghitung jarak menggunakan rumus Haversine
def hitung_jarak(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))

    return 6371 * c


# Pencarian hotspot secara serial
def pencarian_serial(data, target_lat, target_lon, radius):
    hasil = []

    for hotspot in data:
        jarak = hitung_jarak(
            target_lat,
            target_lon,
            hotspot["latitude"],
            hotspot["longitude"]
        )

        if jarak <= radius:
            hotspot_hasil = hotspot.copy()
            hotspot_hasil["jarak_km"] = jarak
            hasil.append(hotspot_hasil)

    return hasil


def main():
    print("=== PENCARIAN HOTSPOT INDONESIA ===")

    nama_wilayah = input("Masukkan nama kabupaten/kota: ").strip()

    if not nama_wilayah:
        print("Nama wilayah tidak boleh kosong.")
        return

    print("\nMencari koordinat wilayah...")

    lokasi = cari_koordinat(nama_wilayah)

    if lokasi is None:
        print("Wilayah tidak ditemukan atau layanan tidak tersedia.")
        return

    print("\n=== LOKASI DITEMUKAN ===")
    print("Nama wilayah:", lokasi["nama"])
    print("Latitude:", lokasi["latitude"])
    print("Longitude:", lokasi["longitude"])

    try:
        radius = float(input("\nMasukkan radius (km): "))

        if radius <= 0:
            print("Radius harus lebih besar dari 0.")
            return

    except ValueError:
        print("Radius harus berupa angka.")
        return

    data_hotspot = baca_dataset()

    print("\nJumlah data hotspot:", len(data_hotspot))

    waktu_mulai = time.perf_counter()

    hasil = pencarian_serial(
        data_hotspot,
        lokasi["latitude"],
        lokasi["longitude"],
        radius
    )

    waktu_selesai = time.perf_counter()
    waktu_eksekusi = waktu_selesai - waktu_mulai

    print("\n=== HASIL PENCARIAN ===")
    print("Wilayah:", lokasi["nama"])
    print("Radius:", radius, "km")
    print("Jumlah data diperiksa:", len(data_hotspot))
    print("Jumlah hotspot ditemukan:", len(hasil))

    for nomor, hotspot in enumerate(hasil[:20], start=1):
        print(
            f"{nomor}. Tanggal: {hotspot['tanggal']} | "
            f"Jarak: {hotspot['jarak_km']:.3f} km | "
            f"FRP: {hotspot['frp']}"
        )

    if len(hasil) > 20:
        print("... dan", len(hasil) - 20, "hotspot lainnya.")

    print("\nWaktu eksekusi:", waktu_eksekusi, "detik")
    print("Metode: Serial")
    print("Sumber koordinat: OpenStreetMap / Nominatim")


if __name__ == "__main__":
    main()
