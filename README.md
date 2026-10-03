<h1 align="center">
  <img src="https://img.icons8.com/fluency/96/000000/artificial-intelligence.png" alt="VisionPay Logo" width="80" />
  <br>
  VisionPay Terminal 🚀
</h1>

<p align="center">
  <strong>AI Financial Forensics v2.0</strong> <br>
  <i>Built for the DIU AI Hackathon</i>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#how-to-use">How to Use</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#license">License</a>
</p>

---

## 🌟 About The Project

### Mobile number OCR implementation

The Number OCR tab reads an uploaded image or camera frame locally with EasyOCR
on the CPU, then validates the transcribed numbers on the server. No Gemini API
key or paid OCR service is needed. It supports Bangla/English digits, local
11-digit numbers, and `+880`, `880`, or `00880` country codes. Duplicate numbers are
merged; multiple numbers can be selected individually for copying. Unreadable or
invalid numbers produce an empty result rather than a sample number.

Install the local OCR dependencies. On Windows, from the repository root:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt
.\venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

The first scan downloads the Bangla/English OCR models into `~/.EasyOCR/model`,
so it requires internet and takes longer. Later scans run locally using the cached
models. Clear printed numbers work best; handwriting is not reliably supported.
Crop closely around numbers if detection misses them. OCR checks the number's
format, not whether the text is actually a phone number: an account or ID with
the same format can match too. Always compare the result with the image.

Uploads are limited to 10 MB and 20 megapixels.
OCR confidence is model-reported, not measured accuracy. Operators are inferred
from the original number prefix; mobile number portability can change the current
network. This feature does not verify ownership or whether a number is active.

### Local document and receipt OCR

The Document tab uses the same local OCR model to recognize Bangladesh NID and
passport text. It extracts supported fields such as name, parent names, birth date,
NID number, and passport number. The Receipt tab extracts the payment provider,
transaction ID, amount, date/time, sender, and receiver when those labels are visible.

These features transcribe text and validate basic formats only. They do not query a
government, bank, bKash, Nagad, or other provider database, so they cannot certify a
document, confirm a payment, or determine whether a screenshot was edited. Always
compare OCR output with the image and verify important transactions at the source.

Run checks after installing dependencies and `httpx`:
```bash
python -m unittest discover -s tests -p "test_*.py"
node tests/number_scanner_ui.test.cjs
```

**VisionPay Terminal** is a prototype financial image-analysis application. Mobile
number, document, and receipt text extraction run locally through EasyOCR. The cash
counting and fake-note modules still require further implementation before their
results should be relied on.

A dedicated **Bangla Voice Assistant** is integrated to guide users, making the platform accessible and intuitive for everyday financial screening in Bangladesh.

---

## 🚀 Features

- 💵 **Smart Cash Counting:** Analyzes an image of multiple currency notes and calculates the total amount instantly.
- 🕵️ **Fake Note Detection:** Scans Bangladeshi Taka (BDT) notes for anomalies, security threads, and watermarks to detect counterfeit currency.
- 📄 **Document OCR:** Extracts supported fields from NID and passport images without claiming authenticity.
- 🧾 **Receipt OCR:** Extracts structured payment fields without claiming payment or screenshot authenticity.
- 🔢 **Number OCR:** Extracts Bangladesh mobile numbers from printed images locally with EasyOCR, with Bangla and English digit support.
- 🎙️ **Bangla Voice Assistant:** Provides accessible auditory feedback and verdicts in Bangla.
- 📸 **Live Camera Integration:** Scan notes and documents directly using your device's webcam/mobile camera.

---

## 💻 Tech Stack

### Frontend
- **HTML5 & CSS3:** Vanilla CSS with custom Glassmorphism aesthetics and animations.
- **JavaScript (ES6):** Modular Vanilla JS for routing, camera API, and state management.
- **Chart.js:** For visualizing radar charts and data analytics.

### Backend
- **FastAPI (Python):** High-performance backend API routing and image handling.
- **EasyOCR:** Local, CPU-based mobile number OCR with no API fee.
- **Google Generative AI:** Image analysis for the other modules.
- **Motor (MongoDB):** Asynchronous database driver for saving scan history and analytics.
- **Pillow (PIL):** Image processing and handling before sending to the AI model.

---

## ⚙️ Installation

### Prerequisites
- Python 3.11 or 3.12 for local number OCR
- MongoDB (Running locally or MongoDB Atlas)
- Google Gemini API Key for the other modules (not needed for Number OCR)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shuvosinghpartho/Diu-AI_Hacakathon.git
   cd Diu-AI_Hacakathon
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your keys:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   MONGO_URI=mongodb://localhost:27017
   ```

4. **Run the Application:**
   We have provided executable scripts to manage the server easily:
   ```bash
   # To Start the server
   ./start

   # To Stop the server
   ./stop
   ```
   *Alternatively, you can run Uvicorn manually:*
   ```bash
   uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
   ```

5. **Open in Browser:**
   Navigate to 👉 `http://127.0.0.1:8000`

---

## 📂 Project Structure

```text
📦 VisionPay-Terminal
 ┣ 📂 backend
 ┃ ┣ 📂 routes          # FastAPI API Endpoints (count, fake_currency, etc.)
 ┃ ┣ 📂 services        # Local OCR, field parsing, and AI integration
 ┃ ┣ 📜 app.py          # FastAPI application entry point
 ┃ ┗ 📜 database.py     # MongoDB connection setup
 ┣ 📂 frontend
 ┃ ┣ 📂 css             # Modular stylesheets (Glassmorphism, animations)
 ┃ ┣ 📂 js              # API callers, UI modules, Camera stream handler
 ┃ ┗ 📜 index.html      # Main Single Page Application UI
 ┣ 📜 start             # Bash script to start server in background
 ┣ 📜 stop              # Bash script to kill running server
 ┣ 📜 requirements.txt  # Python dependencies
 ┗ 📜 .env              # Environment configurations (ignored in git)
```

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License
Designed & Developed for **DIU AI Hackathon**.

<p align="center">
  <i>Made with ❤️ and 🤖 AI</i>
</p>
