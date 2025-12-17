# 🚀 AI Content Studio | Full-Stack Content Generation Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-Framework-green)
![AI](https://img.shields.io/badge/AI-Whisper%20%7C%20Ollama%20%7C%20SD3-orange)

An integrated, locally-hosted platform designed for content creators to generate articles, summarize texts, transcribe audio, and create images using cutting-edge AI models. The project fully supports Arabic and English with a modern, user-friendly interface.

---

## 📸 Project Screenshots

### 1. Smart Summarization (with Live Streaming)
![Summarization Screen](screenshots/summary.gif)

### 2. Audio Transcription (Whisper AI)
![Transcription Screen](screenshots/transcribe.gif)
### 🤖 Chatbot Demo
![Chatbot in Action](screenshots/chatbot-demo.gif)

## ✨ Key Features

* **📝 Article Generation & Expansion:** Generate professional articles and expand paragraphs using Llama models via Ollama.
* **⚡ Real-Time Summarization (Streaming):** Summarize long articles with word-by-word text streaming and automatic Markdown formatting.
* **🎙️ Precise Audio Transcription:** Convert audio files to text with high accuracy using **OpenAI Whisper** (running locally).
* **🎨 Creative Image Generation:** Create expressive images for articles using **Stability AI (SD3)** based on the text content.
* **🤖 Intelligent AI Assistant:** Direct chat with AI to brainstorm ideas and refine drafts.
* **💎 Professional UI:** Eye-friendly design with optimized containers, clean typography, and RTL support for Arabic.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **AI Models:**
    * *Text:* Ollama (Llama 3 / GPT-OSS)
    * *Audio:* OpenAI Whisper (Base Model)
    * *Images:* Stability AI API (SD3)
* **Frontend:** HTML5, CSS3, JavaScript (Fetch API, Marked.js)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** (Version 3.8 or later).
2.  **FFmpeg:** Required for the Whisper library to process audio files.
    * *Windows:* [Download FFmpeg](https://www.gyan.dev/ffmpeg/builds/) (Make sure to add it to your System PATH).
3.  **Ollama:** Must be installed and running in the background.
    * Pull the required model: `ollama run gpt-oss:120b-cloud` (or whichever model you configured in `utils.py`).

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/ayakakaa135-boop/ai-content-studio.git](https://github.com/ayakakaa135-boop/ai-content-studio.git)
cd ai-content-studio

## 🛠️ Setup & Installation

Follow these commands in your **Terminal** to get started:

### 1️⃣ Create a Virtual Environment
```bash
python -m venv venv
2️⃣ Activate the Environment
Windows:

Bash

venv\Scripts\activate
macOS/Linux:

Bash

source venv/bin/activate
3️⃣ Install Dependencies
Bash

pip install -r requirements.txt
4️⃣ Run the App
Bash

python app.py
Open your browser at: http://127.0.0.1:5000


