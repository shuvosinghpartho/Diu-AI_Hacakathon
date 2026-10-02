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

**VisionPay Terminal** is an advanced AI-powered web application designed to act as a complete financial forensics tool. It leverages **Google's Gemini 3.5 Flash** to analyze images of currency, receipts, and identity documents in real-time. Whether it's detecting fake currency, extracting text, or verifying documents, VisionPay handles it seamlessly with an edge-inspired, glassmorphic UI.

A dedicated **Bangla Voice Assistant** is integrated to guide users, making the platform accessible and intuitive for everyday financial screening in Bangladesh.

---

## 🚀 Features

- 💵 **Smart Cash Counting:** Analyzes an image of multiple currency notes and calculates the total amount instantly.
- 🕵️ **Fake Note Detection:** Scans Bangladeshi Taka (BDT) notes for anomalies, security threads, and watermarks to detect counterfeit currency.
- 📄 **Document Verification:** Verifies the authenticity of Identity Cards (NID) and Passports.
- 🧾 **Receipt Forensics:** Extracts data from bills and receipts, detecting tampering or anomalies in the text.
- 🔢 **Number OCR:** Accurately extracts phone numbers, account numbers, and specific numerical data from handwritten or printed images.
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
- **Google Generative AI (Gemini 3.5 Flash):** Core AI engine for image analysis, OCR, and reasoning.
- **Motor (MongoDB):** Asynchronous database driver for saving scan history and analytics.
- **Pillow (PIL):** Image processing and handling before sending to the AI model.

---

## ⚙️ Installation

### Prerequisites
- Python 3.9+
- MongoDB (Running locally or MongoDB Atlas)
- Google Gemini API Key

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
 ┃ ┣ 📂 services        # Business Logic & Gemini AI Integration Wrapper
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
