
import csv
import math
import time
import requests
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_DATASET = BASE_DIR / "dataset" / "viirs_snpp_2025_indonesia.csv"

JUMLAH_PROSES = 4


# Mencari koordinat berdasarkan nama wilayah
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
        print("Gagal mencari koordinat:", error)
        return None


# Membaca dataset
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


# Menghitung jarak menggunakan Haversine
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


# Membagi dataset menjadi beberapa bagian
def bagi_dataset(data, jumlah_bagian):
    bagian = []
    ukuran = len(data)
    dasar = ukuran // jumlah_bagian
    sisa = ukuran % jumlah_bagian
    awal = 0

    for i in range(jumlah_bagian):
        tambahan = 1 if i < sisa else 0
        akhir = awal + dasar + tambahan
        bagian.append(data[awal:akhir])
        awal = akhir

    return bagian


# Fungsi yang dijalankan oleh setiap proses
def cari_pada_bagian(tugas):
    nomor_proses, bagian_data, target_lat, target_lon, radius = tugas
    hasil = []

    for hotspot in bagian_data:
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

    return nomor_proses, hasil


# Pencarian paralel
def pencarian_paralel(data, target_lat, target_lon, radius):
    bagian_data = bagi_dataset(data, JUMLAH_PROSES)

    tugas = [
        (i + 1, bagian, target_lat, target_lon, radius)
        for i, bagian in enumerate(bagian_data)
    ]

    hasil_akhir = []

    with ProcessPoolExecutor(max_workers=JUMLAH_PROSES) as executor:
        hasil_proses = executor.map(cari_pada_bagian, tugas)

        for nomor_proses, hasil in hasil_proses:
            print(
                f"Proses {nomor_proses} selesai: "
                f"{len(hasil)} hotspot ditemukan"
            )
            hasil_akhir.extend(hasil)

    return hasil_akhir


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

    hasil = pencarian_paralel(
        data_hotspot,
        lokasi["latitude"],
        lokasi["longitude"],
        radius
    )

    waktu_selesai = time.perf_counter()
    waktu_eksekusi = waktu_selesai - waktu_mulai

    print("\n=== HASIL PENCARIAN PARALEL ===")
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

    print("\nJumlah proses:", JUMLAH_PROSES)
    print("Waktu eksekusi:", waktu_eksekusi, "detik")
    print("Metode: Paralel")


if __name__ == "__main__":
    main()
