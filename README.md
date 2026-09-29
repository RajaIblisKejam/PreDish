# PreDish - Dari Insting ke Data
PreDish adalah aplikasi web *SaaS* (Software as a Service) Minimum Viable Product (MVP) yang dirancang khusus untuk pemilik usaha *F&B* (kafe, restoran, katering). Aplikasi ini membantu pemilik usaha memprediksi jumlah porsi atau bahan baku yang harus disiapkan keesokan harinya berdasarkan data historis penjualan dan variabel eksternal (cuaca, tanggal gajian, hari libur), sehingga dapat menekan kerugian akibat kelebihan produksi (*overproduction*) atau kekurangan stok (*stockout*).

## Fitur Utama
1. **Onboarding Multi-tenant**: Pendaftaran akun dan profil bisnis tersendiri (tiap pengguna hanya melihat data bisnisnya).
2. **Dashboard Prediksi**: Rekomendasi produksi harian yang terhitung otomatis dan divisualisasikan dengan grafik tren (*Chart.js*).
3. **Input & Upload Riwayat**: Dukungan *input* manual harian atau unggah data massal menggunakan CSV/Excel.
4. **Mesin Prediksi (Forecast Engine)**: Memanfaatkan metode statistik sederhana (*Weighted Moving Average*) yang digabungkan dengan koefisien variabel kalender & cuaca.
5. **Riwayat & Insight**: Pelacakan akurasi prediksi, potensi penurunan kelebihan produksi, lengkap dengan opsi *export* CSV.
6. **Sistem Notifikasi Pintar**: Mengingatkan *user* apabila data tidak lengkap, akurasi prediksi turun drastis, atau apabila tren sisa produksi terlalu banyak.

## Persyaratan Sistem
- Python 3.10 atau lebih baru
- Django 5.x
- Pandas & OpenPyXL (untuk pengolahan CSV & Excel)

## Cara Instalasi
1. *Clone* repositori ini atau *copy* folder sumber.
2. Buat dan aktifkan *Virtual Environment*:
   ```bash
   python -m venv venv
   # Di Windows:
   venv\Scripts\activate
   # Di Mac/Linux:
   source venv/bin/activate
   ```
3. Instal pustaka (*library*) yang dibutuhkan:
   ```bash
   pip install django pandas openpyxl
   ```
4. Jalankan migrasi *database*:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Cara Menjalankan
1. Pastikan *virtual environment* masih aktif.
2. Jalankan server pengembangan bawaan Django:
   ```bash
   python manage.py runserver
   ```
3. Buka *browser* Anda dan kunjungi `http://127.0.0.1:8000/`.

## Struktur Database & Model (MVP)
Aplikasi ini menggunakan SQLite secara *default* dan dibagi menjadi beberapa *App*:
- **`accounts`**: Modul *built-in* dari Django untuk autentikasi User (Login/Register).
- **`business`**:
  - `Business`: Menyimpan profil F&B (Kafe, Restoran, dsb).
  - `MenuItem`: Menyimpan daftar menu yang dijual oleh `Business`.
- **`sales`**:
  - `DailySale`: Menyimpan log harian per menu (jumlah terjual dan jumlah diproduksi).
- **`forecast`**:
  - `Forecast`: Menyimpan hasil prediksi mesin per hari per menu beserta tingkat *confidence*-nya.
  - `ExternalFactor`: Menyimpan pengaturan cuaca, periode gajian, dll per tanggal produksi.
- **`notifications`**:
  - `Notification`: Menyimpan teguran/saran yang dihasilkan dari evaluasi log harian.

## Arsitektur MVP
PreDish mengadopsi struktur arsitektur Django **MVT** (Model-View-Template):
- **Logika Bisnis vs *View***: Logika penghitungan persentase dan algoritma prediksi dipisahkan ke dalam file `services.py` (*Service Layer*) agar `views.py` tetap ringkas dan tidak memikul beban komputasi.
- **Transaksional**: Fitur unggah file dan operasi massal ke *database* selalu dibungkus di dalam `transaction.atomic()` untuk membatalkan seluruh perubahan seandainya ada data gagal (*Rollback*).
- **Keamanan Dasar**: Seluruh *endpoint* dilindungi `@login_required` dan query berbasis hierarki ID pengguna (`request.user.businesses`), menjadikan aplikasi ini stabil menampung banyak *tenant* di satu database *default*.
- **UI/UX**: Menggunakan konfigurasi dasar `Tailwind CSS` via CDN untuk merakit purwarupa MVP secara instan namun terasa premium.
