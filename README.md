<div align="center">

# 📸 SnapClass

### AI-Powered Smart Attendance System

Mark attendance in seconds using face recognition, voice verification, and QR-based class enrollment.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Backend-3ECF8E?logo=supabase&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## 📖 Overview

**SnapClass** is a web application that automates classroom attendance using AI. Instead of manual roll calls, teachers can capture attendance through facial recognition, while students enroll into classes instantly through a shareable QR code or join link.

The goal is to reduce time wasted on attendance, minimize proxy attendance, and give teachers a simple, reliable record of who was present.

## ✨ Features

- 👩‍🏫 **Separate Teacher and Student portals** with role-based access
- 🙂 **Face recognition attendance** using dlib and `face_recognition` models
- 🎙️ **Voice verification** using speaker embeddings (Resemblyzer + Librosa)
- 🔗 **QR code / join-link enrollment**: students join a class with a single scan
- 🔐 **Secure authentication** with bcrypt password hashing
- ☁️ **Cloud database** powered by Supabase
- ⚡ **Fast, lightweight UI** built with Streamlit

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / App | Streamlit |
| Face Recognition | dlib, face_recognition_models, scikit-learn |
| Voice Recognition | Resemblyzer, Librosa |
| Backend / Database | Supabase |
| Security | bcrypt |
| QR Codes | Segno |
| Data Handling | NumPy, Pandas, Pillow |

## 📂 Project Structure

```
.
├── app.py                 # Application entry point and routing
├── requirements.txt       # Python dependencies
└── src/
    ├── screens/           # Home, Teacher, and Student screens
    └── components/        # Reusable UI components (e.g. auto-enroll dialog)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- A [Supabase](https://supabase.com) project
- A webcam and microphone (for face and voice features)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ayushsingh87182/AI-Attendance-System.git
cd AI-Attendance-System

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configuration

Add your Supabase credentials. <!-- verify: check the code for the exact secret/env variable names -->

```toml
# .streamlit/secrets.toml
SUPABASE_URL = "your-supabase-project-url"
SUPABASE_KEY = "your-supabase-anon-key"
```

> ⚠️ Never commit your secrets file. Add `.streamlit/secrets.toml` to `.gitignore`.

### Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## 🧭 How It Works

1. **Teacher** signs up, creates a class, and shares the generated QR code or join link.
2. **Students** register, upload their face (and voice sample), and join the class via the link.
3. During class, the teacher starts an attendance session and the system matches faces against enrolled students.
4. Attendance is saved to the database and can be reviewed by the teacher.

<!-- verify: adjust these steps to match the actual app flow -->

## 📸 Screenshots

<!-- Add screenshots here -->
<!-- ![Home](assets/home.png) -->
<!-- ![Teacher Dashboard](assets/teacher.png) -->

## 🗺️ Roadmap

- [ ] Attendance analytics and export (CSV / PDF)
- [ ] Liveness detection to prevent photo spoofing
- [ ] Email / SMS notifications for absentees
- [ ] Mobile-friendly UI improvements

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License. <!-- verify: add a LICENSE file -->

## 👤 Author

**Ayush Singh**
GitHub: [@ayushsingh87182](https://github.com/ayushsingh87182)

---

<div align="center">⭐ If you found this project useful, consider giving it a star!</div>
