# 🛒 BeliKuy E-Commerce Platform

BeliKuy adalah platform *e-commerce* modern berbasis *Microservices Architecture* yang dirancang untuk memberikan pengalaman jual-beli yang mulus bagi Pembeli (Customer), Penjual (Seller), dan Pemantauan penuh bagi Super Admin.

Proyek ini dibangun sebagai **Final Project**, mengintegrasikan antarmuka dinamis berbasis Python dengan ketangguhan pemrosesan data *backend* berbasis Node.js.

## 🚀 Fitur Utama
Aplikasi ini terbagi menjadi 3 peran (*role*) utama:
1. **👨‍💼 Customer**: Eksplorasi katalog, pencarian cerdas, *checkout* multi-produk, manajemen alamat, simulasi *payment gateway*, dan pelacakan resi.
2. **🏪 Seller**: Pembukaan toko otomatis, manajemen inventaris/katalog barang, pemrosesan pesanan, input resi ekspedisi, laporan pendapatan (*omzet*), dan penarikan dana (*withdrawal*).
3. **👑 Super Admin**: *Dashboard* analitik omzet (*Gross Merchandise Value*), *monitoring* seluruh transaksi lintas toko, persetujuan penarikan dana *seller*, serta manajemen status *vendor*, metode pembayaran, dan jasa ekspedisi.

## 🛠️ Teknologi yang Digunakan
* **Frontend (UI/UX)**: Python 3 & Streamlit (dengan Injeksi HTML/JS kustom untuk UI kelas atas).
* **Backend (API)**: Node.js & Express.js (Arsitektur *Microservices* murni).
* **Database**: MySQL (Terdistribusi ke dalam 3 *database* terpisah).
* **Komunikasi**: RESTful API Gateway.

## 📂 Struktur Repositori
* `belikuy_frontend/` - Antarmuka pengguna (Python Streamlit).
* `belikuy_api_gateway/` - Pintu gerbang utama API (Port 3000).
* `belikuy_marketplace_service/` - Layanan inti pengguna, produk, dan transaksi utama.
* `belikuy_seller_service/` - Layanan khusus manajemen toko dan katalog.
* `belikuy_payment_service/` - Layanan pembayaran dan dompet pencairan dana.
* `belikuy_delivery_service/` - Layanan logistik dan ekspedisi.

---

## ⚙️ Cara Menjalankan Aplikasi (Local Setup)

Ikuti langkah-langkah di bawah ini untuk menjalankan aplikasi BeliKuy di komputermu:

### 1. Persiapan Kebutuhan Sistem
Pastikan perangkat lunak berikut sudah terinstal:
* **Laragon** atau **XAMPP** (untuk menjalankan MySQL Server).
* **Node.js** (versi 16 atau lebih baru).
* **Python** (versi 3.9 atau lebih baru).

### 2. Konfigurasi Database
1. Buka aplikasi **Laragon** lalu klik **Start All** (atau buka **XAMPP** dan klik **Start** pada modul **MySQL**).
2. Akses *database client*:
   - Jika menggunakan **Laragon**: Klik tombol **Database** (HeidiSQL) atau akses `http://localhost/phpmyadmin` jika terinstal.
   - Jika menggunakan **XAMPP**: Buka *browser* dan akses `http://localhost/phpmyadmin`.
3. Buat 3 *database* kosong dengan nama berikut:
   - `belikuy_marketplace_db`
   - `belikuy_seller_db`
   - `belikuy_payment_db`
4. Lakukan *Import* _file_ SQL yang telah disediakan ke masing-masing *database* tersebut.

### 3. Menjalankan Aplikasi
Kami telah menyediakan *script* otomatis agar kamu tidak perlu menyalakan *service* satu per satu!
1. Buka *folder* utama proyek `belikuy`.
2. Klik dua kali (*double-click*) pada _file_ **`start_all.bat`**.
3. Tunggu beberapa detik hingga semua jendela *Command Prompt* bermunculan (menandakan *API Gateway*, *Microservices*, dan *Frontend* sedang dinyalakan).
4. *Browser* akan otomatis membuka `http://localhost:8501` yang merupakan halaman utama aplikasi BeliKuy.

Selamat berbelanja dan berjualan di BeliKuy! 🎉
