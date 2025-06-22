# NeuroGenius GPT Documentation

## 🚀 Overview
NeuroGenius GPT is an AI-powered platform offering secure chat, text-to-image generation, document analysis, and more. It ensures user privacy while delivering cutting-edge AI capabilities in an intuitive and user-friendly interface.

## ✨ Features

### 1️⃣ Secure Chat
Engage in intelligent conversations with NeuroGenius AI.
- 🎙 **Speech-to-Text**: Use your microphone to input messages.
- 🔊 **Text-to-Speech**: Listen to AI responses.
- 📝 **Message Editing**: Edit sent messages and regenerate AI responses.
- 📥 **Message Downloading**: Save messages as audio files.
- 📁 **Chat History Management**: Rename, delete, or download chat histories.

### 2️⃣ Text-to-Image Generation
Generate high-quality images from text prompts using NeuroVision AI.
- 📂 **User-Specific History**: Access past image generations.
- 🎨 **Image Editing**: Modify prompts to regenerate images.
- 📥 **Image Downloading**: Save generated images.
- 📌 **Context Menu**: Options to edit, copy, delete, or download images.

### 3️⃣ Document Analysis
Upload and process various document formats, including PDFs, images, and text files.
- 🔍 **OCR (Optical Character Recognition)**: Extract text from images.
- 📑 **PDF Text Extraction**: Extract text from PDFs.
- ❓ **Query Processing**: Ask AI-driven questions about documents.
- 👀 **Document Preview**: View uploaded documents with zoom functionality.
- 📜 **Query History**: Save and load query histories for each document.

### 4️⃣ User Management
Secure user-specific features ensure privacy and data isolation.
- 👤 **Profile Management**: Update username, email, phone number, and password.
- 📊 **Usage History**: View activity logs and statistics.
- 🔒 **Logout Functionality**: Securely log out of the application.

### 5️⃣ AI Model Integration
Seamlessly switch between multiple AI models for chat, document analysis, and image generation.

## 🛠 Technical Details

### 1️⃣ Tech Stack
- **Frontend**: PySide6 (Qt for Python) for the user interface.
- **Backend**: Python for AI integration and business logic.
- **Database**: SQLite for user data, chat histories, and image records.
- **AI Models**: Proprietary NeuroGenius AI models.

### 2️⃣ Key Libraries
- `PySide6`: GUI development.
- `Pillow`: Image processing.
- `PyPDF2`: PDF text extraction.
- `pytesseract`: OCR functionality.
- `SpeechRecognition`: Speech-to-text conversion.
- `pyttsx3`: Text-to-speech conversion.

## 📂 Project Structure
```bash
NeuroGenius_App/
├── authentication.py           # Handles user authentication (login, registration, password reset)
├── database.py                 # Core database connection and management logic
├── main.py                     # Entry point for the application
├── model.py                    # AI model orchestration and management
├── requirements.txt            # Python dependencies for the project
├── setup.py                    # Setup script for packaging the application
├── structure.py                # Script to print the directory structure
├── ui_auth.py                  # UI for authentication (login, registration)
├── ui_forgot.py                # UI for password recovery
├── ui_login.py                 # UI for the login screen
├── ui_main.py                  # Main application UI and logic
├── ui_register.py              # UI for user registration
├── utils.py                    # Utility functions used across the application
├── assets/                     # Static assets (icons, images)
├── database/                   # Database-related scripts and files
├── document_processing/        # Document processing and query handling
├── generated_images/           # Folder for storing generated images
├── logs/                       # Application logs
├── models/                     # Placeholder for AI models (if applicable)
├── neurogenius.egg-info/       # Metadata for the Python package
├── temp/                       # Temporary files
├── user_documents/             # User-specific uploaded documents
└── utils/                      # Utility scripts
```

## 🎯 How to Run the Application

### 🛠 Prerequisites
- Install **Python 3.8** or higher.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### ▶️ Running the Application
```bash
python main.py
```

## 📌 Usage Instructions

### 🔐 1. Login
- Enter your username and password to log in.
- New users can register by providing their details.

### 💬 2. Chat
- Navigate to the **Chats** section.
- Start a new chat or continue an existing one.
- Use the microphone button for speech-to-text input.

### 🖼 3. Image Generation
- Navigate to **Image Generation**.
- Enter a text prompt and click **Generate Image**.
- View, edit, or download generated images.

### 📄 4. Document Analysis
- Navigate to **Documents**.
- Upload a document and select it.
- Ask queries and receive AI-generated responses.

### ⚙️ 5. Profile Management
- Access the **Profile** section.
- Update your username, email, phone number, or password.
 
## 🚀 Future Enhancements
- 🏆 **Subscription Plans**: Add premium subscriptions.
- ☁ **Cloud Integration**: Store user data and generated content in the cloud.
- 🔥 **Advanced AI Models**: Integrate more powerful AI models.
- 📱 **Mobile Support**: Develop a mobile-friendly version.

## 🛠 Troubleshooting

### ❗ Common Issues

#### ⚠ Model Load Error:
- Ensure required AI models are downloaded.
- Check GPU availability for CUDA-based operations.

#### 🔍 Database Errors:
- Verify that the SQLite database files exist and are accessible.

#### 🖼 OCR Issues:
- Ensure Tesseract OCR is installed and configured correctly.

## 👥 Contributors
- **Project Lead**: [Kayam Sai Krishna](mailto:kayamsaikrishna@gmail.com)

## 📜 License
This project is licensed under the **MIT License**. See the LICENSE file for details.
