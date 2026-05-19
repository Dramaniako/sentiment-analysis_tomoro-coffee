Sistem Monitoring Sentimen Sosial & Brand Real-Time (Tomoro Coffee)
Sistem ini adalah pipeline end-to-end untuk mengekstraksi, memproses, dan menganalisis sentimen pelanggan secara otomatis dari Google Maps. Proyek ini dibangun untuk membantu perusahaan memantau kepuasan pelanggan secara real-time dengan memanfaatkan teknik Web Scraping dan Natural Language Processing (NLP) berbasis Deep Learning.

🚀 Arsitektur Sistem
Pipeline ini terdiri dari tiga tahap utama:

Data Ingestion: Menggunakan Playwright dengan Persistent Context untuk menembus proteksi anti-bot Google Maps dan melakukan ekstraksi ulasan secara otomatis.

Data Processing & NLP:

Cleaning: Penghapusan noise, URL, emoji, dan karakter non-alfanumerik.

Normalization: Konversi bahasa gaul/slang ke Bahasa Indonesia formal menggunakan kamus khusus.

Classification: Penggunaan model IndoBERT (RoBERTa) yang sudah dilatih khusus untuk analisis sentimen bahasa Indonesia.

Visualization: Dashboard interaktif berbasis Streamlit untuk memvisualisasikan distribusi sentimen dan memantau umpan balik negatif secara cepat.

🛠 Instalasi
Pastikan kamu sudah menginstal Python (versi 3.9+ disarankan).

Clone repositori ini:

Bash
git clone https://github.com/username/repository-kamu.git
cd repository-kamu
Instal dependensi yang diperlukan:

Bash
pip install -r requirements.txt
⚙️ Cara Penggunaan
Ekstraksi Data: Masukkan URL target Google Maps ke dalam file extractor.py lalu jalankan:

Bash
python extractor.py
(Data akan tersimpan secara otomatis dalam format .jsonl).

Analisis Sentimen:
Jalankan mesin NLP untuk membersihkan data dan melakukan klasifikasi sentimen:

Bash
python nlp_engine.py
Dashboard Visualisasi:
Jalankan dashboard interaktif untuk melihat hasil analisis:

Bash
python -m streamlit run dashboard.py
📊 Hasil (Dataset Summary)
Sistem ini mampu mengklasifikasikan ulasan ke dalam tiga kategori:

Positif: Mengidentifikasi kepuasan pelanggan terkait produk/layanan.

Negatif: Mengidentifikasi pain points pelanggan untuk perbaikan operasional.

Netral: Ulasan yang bersifat informatif atau deskriptif.

📝 Catatan Penting
Security: Harap pastikan folder chrome_profile tidak pernah diunggah ke repository publik karena mengandung session cookies.

Dependencies: Proyek ini menggunakan transformers dan torch (PyTorch). Pastikan koneksi internet stabil saat menjalankan nlp_engine.py pertama kali untuk mengunduh model.