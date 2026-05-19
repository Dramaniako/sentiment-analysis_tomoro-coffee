# ☕ Tomoro Coffee Sentiment Analysis
Sistem end-to-end untuk mengekstraksi, memproses, dan memantau sentimen pelanggan dari Google Maps secara real-time.

## 📸 Demo
Demo berikut dilakukan dengan data dari review Google Maps untuk brand Tomoro Coffee di daerah Bali, link yang digunakan untuk ekstrasi tersedia pada file **_extractor.py_**.
<img width="1268" height="522" alt="image" src="https://github.com/user-attachments/assets/01e5418e-a66c-4677-bc9c-14446c254f0d" />

## 📦 Installation
Clone repositori ini dan instal dependensi yang diperlukan:

```Bash
git clone https://github.com/username/tomoro-sentiment.git
cd tomoro-sentiment
pip install -r requirements.txt
```
## 🛠 Usage
Ekstraksi Data:
Masukkan URL lokasi target di extractor.py dan jalankan:

```Bash
python extractor.py
```
Analisis Sentimen:
Jalankan mesin NLP untuk pembersihan teks dan klasifikasi:

```Bash
python nlp_engine.py
```
Dashboard:
Jalankan dashboard interaktif:

```Bash
python -m streamlit run dashboard.py
```
## ✨ Features
- Anti-Bot Scraping: Mengatasi proteksi Google Maps dengan Persistent Context.

- Slang Normalization: Pembersihan teks otomatis untuk bahasa gaul/slang Indonesia.

- AI Sentiment Engine: Menggunakan model IndoBERT untuk klasifikasi emosi.

- Dashboard Visual: Visualisasi data interaktif untuk pengambilan keputusan bisnis.

## 🧰 Tech Stack
- Python 3.11

- Playwright: Web automation & scraping.

- Transformers (IndoBERT): Model AI untuk NLP.

- Pandas: Manipulasi data.

- Streamlit: Dashboard UI.

- Plotly: Visualisasi grafik.

## 🤝 Contributing
Kontribusi selalu terbuka! Jika ada saran untuk penambahan fitur atau perbaikan model, silakan buka issue atau kirimkan pull request.
