import sys
import os
# Add the project root directory to sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

print(sys.path)

import uuid
import datetime
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QListWidget, QListWidgetItem, QToolButton, QMenu, QDialog, QInputDialog,
    QSizePolicy, QTextEdit, QTabWidget, QScrollArea, QFrame, QComboBox, QLineEdit,
    QMessageBox, QApplication, QFileDialog
)
from PySide6.QtCore import Qt, QPoint, QTimer, QByteArray, QBuffer, Signal, QThread
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QIcon, QAction, QFont, QClipboard, QImage
import speech_recognition as sr
import pyttsx3
import requests
import torch
from diffusers import StableDiffusionPipeline
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from diffusers import StableDiffusionImg2ImgPipeline
from pathlib import Path
import gc

# Import database functions (ensure database_chat.py is available)
from database.database_chat import (
    get_chats_by_user, log_user_action, create_chat, update_chat_name,
    delete_chat, get_messages, insert_message, export_chat, get_usage_statistics
)
from database.db_imagedata import insert_image_history, get_image_history, delete_image_history
from document_processing.document_handler import upload_document, save_uploaded_document, list_documents
from document_processing.integration import query_model

IMAGE_DIR = "generated_images"

# ------------------- Ollama API Integration -------------------
def generate_ollama_response(model, prompt):
    try:
        # Send the request to the Ollama API
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True  # Enable streaming
            },
            timeout=120,  # Increase timeout to 120 seconds
            stream=True  # Enable streaming in the request
        )

        # Check if the response is successful
        if response.status_code == 200:
            # Process the streamed response
            full_response = ""
            for chunk in response.iter_lines(decode_unicode=True):
                if chunk:
                    try:
                        # Parse each chunk as JSON
                        data = json.loads(chunk)
                        full_response += data.get("response", "")
                    except json.JSONDecodeError:
                        pass  # Ignore invalid JSON chunks
            return full_response
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.Timeout:
        return "Error: The request timed out. Please try again later."
    except requests.exceptions.ConnectionError:
        return "Error: Unable to connect to the server. Please ensure the server is running."
    except Exception as e:
        return f"Connection error: {str(e)}"

# ------------------- Home Page -------------------
class HomePage(QWidget):
    def __init__(self, switch_page_fn):
        super().__init__()
        self.switch_page_fn = switch_page_fn
        layout = QVBoxLayout(self)
        title = QLabel("Welcome to NeuroGenius GPT")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        about = QLabel(
            "NeuroGenius GPT is an AI-powered platform offering secure chat, advanced document analysis, "
            "and more. Our solution respects privacy while delivering cutting-edge AI capabilities.\n\n"
            "Click on 'Chats' in the sidebar to start a conversation with our AI."
        )
        about.setWordWrap(True)
        about.setAlignment(Qt.AlignCenter)
        about.setStyleSheet("font-size: 16px; margin: 20px;")
        quick_start = QPushButton("Start Chatting")
        quick_start.setStyleSheet("font-size: 16px; padding: 10px;")
        quick_start.clicked.connect(lambda: self.switch_page_fn(1))
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(about)
        layout.addWidget(quick_start, 0, Qt.AlignCenter)
        layout.addStretch()

# ------------------- Document Processor Thread -------------------
class DocumentProcessorThread(QThread):
    result_ready = Signal(str)  # Signal to send the result back to the UI
    error_occurred = Signal(str)

    def __init__(self, file_path, task):
        super().__init__()
        self.file_path = file_path
        self.task = task  # Task can be 'extract_text', 'ocr', or 'read_text'

    def run(self):
        try:
            if self.task == "extract_text":
                from PyPDF2 import PdfReader
                reader = PdfReader(self.file_path)
                text = "".join(page.extract_text() for page in reader.pages)
                self.result_ready.emit(text)
            elif self.task == "ocr":
                from PIL import Image
                import pytesseract
                text = pytesseract.image_to_string(Image.open(self.file_path))
                self.result_ready.emit(text)
            elif self.task == "read_text":
                with open(self.file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                self.result_ready.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))
# ------------------- Document Screen -------------------
class DocumentScreen(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        if not self.username:
            raise ValueError("Username is required to initialize DocumentScreen.")
        
        # Ensure the upload directory is user-specific
        self.upload_dir = os.path.join("user_documents", self.username, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)  # Ensure the user's directory exists
        self.selected_file = None  # To store the currently selected file
        self.query_history = []  # To store query chat history
        self.query_histories = {}  # To store query history for each document

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)

        # Sidebar
        self.sidebar = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search documents...")
        self.search_bar.textChanged.connect(self.filter_documents)
        self.sidebar.addWidget(self.search_bar)

        # Upload Button with Icon
        self.upload_button = QPushButton("Upload Document")
        self.upload_button.setIcon(QIcon("assets/upload_icon.png"))  # Replace with your icon path
        self.upload_button.clicked.connect(self.upload_document)
        self.sidebar.addWidget(self.upload_button)

        # Document List
        self.document_list = QListWidget()
        self.document_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.document_list.customContextMenuRequested.connect(self.show_context_menu)
        self.document_list.itemClicked.connect(self.select_document)
        self.load_documents()
        self.sidebar.addWidget(self.document_list)

        main_layout.addLayout(self.sidebar, 1)

        # Main Content Area
        self.content_area = QVBoxLayout()

        # Add a loading indicator
        self.loading_label = QLabel("NeuroVision is thinking...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 14px; font-style: italic; color: gray;")
        self.loading_label.setVisible(False)  # Initially hidden
        self.content_area.addWidget(self.loading_label)

        # Document Preview
        self.preview_label = QLabel("Document Preview")
        self.preview_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.content_area.addWidget(self.preview_label)

        # Document Preview with Scroll and Zoom
        self.preview_scroll_area = QScrollArea()
        self.preview_scroll_area.setWidgetResizable(True)
        self.document_preview = QLabel()
        self.document_preview.setAlignment(Qt.AlignCenter)
        self.document_preview.setStyleSheet("border: 1px solid #ccc;")
        self.preview_scroll_area.setWidget(self.document_preview)
        self.content_area.addWidget(self.preview_scroll_area)

        # Zoom Buttons
        zoom_layout = QHBoxLayout()
        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_in_button)
        zoom_layout.addWidget(zoom_out_button)
        self.content_area.addLayout(zoom_layout)

        # Model Selection Dropdown
        self.model_selector = QComboBox()
        self.model_selector.addItem("NeuroVision", "granite3.2-vision:latest")
        self.model_selector.addItem("NeuroVision1.0", "llama3.2-vision:11b")
        self.model_selector.addItem("NeuroVision2.0", "gemma3:4b")
        self.content_area.addWidget(QLabel("Select Model:"))
        self.content_area.addWidget(self.model_selector)

        # Query Drafting Area
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Type your query here...")
        self.content_area.addWidget(self.query_input)

        self.query_button = QPushButton("Ask Query")
        self.query_button.clicked.connect(self.ask_query)
        self.content_area.addWidget(self.query_button)

        # Query Chat History
        self.chat_history_scroll = QScrollArea()
        self.chat_history_scroll.setWidgetResizable(True)
        self.chat_history_widget = QWidget()
        self.chat_history_layout = QVBoxLayout(self.chat_history_widget)
        self.chat_history_layout.addStretch()
        self.chat_history_scroll.setWidget(self.chat_history_widget)
        self.content_area.addWidget(self.chat_history_scroll)

        main_layout.addLayout(self.content_area, 3)
        self.setLayout(main_layout)

    
    def convert_pdf_to_images(self,pdf_path):
        images = convert_from_path(pdf_path)
        image_paths = []
        for i, image in enumerate(images):
            image_path = f"{pdf_path}_page_{i + 1}.jpg"
            image.save(image_path, "JPEG")
            image_paths.append(image_path)
        return image_paths
    
    def extract_text_from_image(self, image_path):
        """
        Extract text from an image using Tesseract OCR.
        """
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text.strip()
        except Exception as e:
            return f"Error extracting text from image: {str(e)}"


    def show_context_menu(self, pos):
        """
        Show a context menu for the document list.
        """
        item = self.document_list.itemAt(pos)
        if not item:
            return  # No item at the clicked position

        # Create the context menu
        menu = QMenu()
        open_action = QAction("Open", self)
        delete_action = QAction("Delete", self)

        # Connect actions to their respective methods
        open_action.triggered.connect(lambda: self.open_document(item))
        delete_action.triggered.connect(lambda: self.delete_document(item))

        # Add actions to the menu
        menu.addAction(open_action)
        menu.addAction(delete_action)

        # Show the menu at the cursor position
        menu.exec(self.document_list.mapToGlobal(pos))

    def open_document(self, item):
        """
        Open the selected document.
        """
        file_path = item.data(Qt.UserRole)
        if file_path:
            QMessageBox.information(self, "Open Document", f"Opening document: {file_path}")
        else:
            QMessageBox.warning(self, "Error", "No document selected.")

    def delete_document(self, item):
        """
        Delete the selected document.
        """
        file_path = item.data(Qt.UserRole)
        if file_path:
            confirm = QMessageBox.question(
                self, "Delete Document", f"Are you sure you want to delete {file_path}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                try:
                    os.remove(file_path)
                    self.load_documents()  # Refresh the document list
                    QMessageBox.information(self, "Success", "Document deleted successfully.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete document: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "No document selected.")

    def zoom_in(self):
        """
        Zoom in on the document preview.
        """
        current_size = self.document_preview.pixmap().size()
        self.document_preview.setPixmap(self.document_preview.pixmap().scaled(current_size * 1.2, Qt.KeepAspectRatio))

    def zoom_out(self):
        """
        Zoom out on the document preview.
        """
        current_size = self.document_preview.pixmap().size()
        self.document_preview.setPixmap(self.document_preview.pixmap().scaled(current_size * 0.8, Qt.KeepAspectRatio))

    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF file page by page to reduce memory usage.
        """
        try:
            reader = PdfReader(pdf_path)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text).strip()  # Combine all pages into a single string
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"

    def upload_document(self):
        """
        Handle document upload and save it to the user's directory.
        """
        file_path = upload_document()
        if file_path:
            save_path = save_uploaded_document(file_path, self.upload_dir)
            if save_path:
                QMessageBox.information(self, "Success", "Document uploaded successfully!")
                self.load_documents()
            else:
                QMessageBox.warning(self, "Error", "Failed to upload document.")

    def load_documents(self):
        """
        Load and display the list of uploaded documents for the current user.
        Organize them into categories: Images, PDFs, Word Documents, and Text Files.
        """
        self.document_list.clear()
        documents = list_documents(self.upload_dir)
        if not documents:
            self.document_list.addItem("No documents uploaded yet.")
            return

        # Organize documents by type
        categories = {
            "Images": [],
            "PDFs": [],
            "Word Documents": [],
            "Text Files": []
        }

        for doc in documents:
            file_name = os.path.basename(doc)
            if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                categories["Images"].append(file_name)
            elif file_name.lower().endswith(".pdf"):
                categories["PDFs"].append(file_name)
            elif file_name.lower().endswith((".doc", ".docx")):
                categories["Word Documents"].append(file_name)
            elif file_name.lower().endswith(".txt"):
                categories["Text Files"].append(file_name)

        # Add categories and files to the list
        for category, files in categories.items():
            if files:
                category_item = QListWidgetItem(category)
                category_item.setFlags(Qt.ItemIsEnabled)  # Make category non-selectable
                self.document_list.addItem(category_item)
                for file in files:
                    file_item = QListWidgetItem(f"  {file}")  # Indent files under the category
                    file_item.setData(Qt.UserRole, os.path.join(self.upload_dir, file))
                    self.document_list.addItem(file_item)

    def filter_documents(self, text):
        """
        Filter the document list based on the search query.
        """
        for i in range(self.document_list.count()):
            item = self.document_list.item(i)
            if item.flags() & Qt.ItemIsEnabled:  # Skip category headers
                continue
            item.setHidden(text.lower() not in item.text().lower())

    def select_document(self, item):
        """
        Handle document selection from the list and process it in a background thread.
        """
        file_path = item.data(Qt.UserRole)
        if not file_path:
            return  # Skip category headers
        self.selected_file = file_path

        # Clear query input and chat history
        self.query_input.clear()
        for i in reversed(range(self.chat_history_layout.count() - 1)):
            widget = self.chat_history_layout.itemAt(i).widget()
            if widget:
                self.chat_history_layout.removeWidget(widget)
                widget.deleteLater()

        # Load query history for the selected document
        self.query_histories[self.selected_file] = self.load_query_history(self.selected_file)
        query_history = self.query_histories.get(self.selected_file, [])
        for entry in query_history:
            self.append_query_message("You", entry["query"])
            self.append_query_message("NeuroVision", entry["response"])

        self.loading_label.setVisible(True)

        # Determine task based on file type
        if file_path.lower().endswith(".pdf"):
            task = "extract_text"
        elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
            task = "ocr"
        elif file_path.lower().endswith(".txt"):
            task = "read_text"
        else:
            QMessageBox.warning(self, "Error", "Unsupported file format.")
            self.loading_label.setVisible(False)
            return

        # Start the background thread for processing
        self.processor_thread = DocumentProcessorThread(file_path, task)
        self.processor_thread.result_ready.connect(self.display_document_content)
        self.processor_thread.error_occurred.connect(self.handle_document_error)
        self.processor_thread.start()

    def display_document_content(self, content):
        """
        Display the processed document content in the preview area.
        """
        self.loading_label.setVisible(False)
        self.document_preview.setText(content)

    def display_document_content(self, content):
        """
        Display the processed document content in the preview area.
        """
        self.loading_label.setVisible(False)
        self.document_preview.setText(content)

    def handle_document_error(self, error_message):
        """
        Handle errors that occur during document processing.
        """
        self.loading_label.setVisible(False)
        QMessageBox.warning(self, "Error", f"Failed to process document: {error_message}")

    def append_query_message(self, sender, message):
        """
        Append a query or response message to the chat interface.
        """
        message_frame = QFrame()
        message_frame.setFrameShape(QFrame.StyledPanel)
        if sender == "You":
            message_frame.setStyleSheet("background-color: #E1F5FE; border-radius: 10px; margin: 5px;")
        else:
            message_frame.setStyleSheet("background-color: #F5F5F5; border-radius: 10px; margin: 5px;")
        layout = QVBoxLayout(message_frame)
        sender_label = QLabel(sender)
        sender_label.setStyleSheet("font-weight: bold;")
        content_label = QLabel(message)
        content_label.setWordWrap(True)
        layout.addWidget(sender_label)
        layout.addWidget(content_label)

         # Add context menu for editing, copying, and deleting
        message_frame.setContextMenuPolicy(Qt.CustomContextMenu)
        message_frame.customContextMenuRequested.connect(
            lambda pos: self.show_document_context_menu(pos, message_frame, content_label)
        )

        self.chat_history_layout.insertWidget(self.chat_history_layout.count() - 1, message_frame)


    def save_query_history(self, file_path, query_history):
        """
        Save the query history for a document to a JSON file.
        """
        try:
            history_file = f"{file_path}.history.json"
            with open(history_file, "w") as f:
                json.dump(query_history, f, indent=4)
        except Exception as e:
            print(f"Error saving query history: {str(e)}")


    def load_query_history(self, file_path):
        """
        Load the query history for a document from a JSON file.
        """
        try:
            history_file = f"{file_path}.history.json"
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading query history: {str(e)}")
            return []

    def ask_query(self):
        """
        Process the query on the selected document.
        """
        if not self.selected_file:
            QMessageBox.warning(self, "No Document Selected", "Please select a document first.")
            return

        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Empty Query", "Please enter a query.")
            return

        # Get the selected model key
        model_key = self.model_selector.currentData()

        try:
            # Show the loading indicator
            self.loading_label.setVisible(True)
            QApplication.processEvents()  # Force UI update

            # Prepare input for the model
            document_content = None
            if self.selected_file.lower().endswith(".txt"):
                # Read the text file
                with open(self.selected_file, "r", encoding="utf-8") as f:
                    document_content = f.read()
            elif self.selected_file.lower().endswith(".pdf"):
                # Extract text from PDF
                document_content = self.extract_text_from_pdf(self.selected_file)
            elif self.selected_file.lower().endswith((".png", ".jpg", ".jpeg")):
                # Extract text from image
                document_content = self.extract_text_from_image(self.selected_file)
            else:
                QMessageBox.warning(self, "Error", "Unsupported file format.")
                return

            if not document_content:
                QMessageBox.warning(self, "Error", "The document is empty or could not be processed.")
                return

            # Combine previous prompts with the current query
            previous_prompts = "\n".join(
                [f"You: {entry['query']}\nAssistant: {entry['response']}" for entry in self.query_histories.get(self.selected_file, [])]
            )
            input_text = f"Previous Prompts:\n{previous_prompts}\n\nDocument Content:\n{document_content}\n\nQuery:\n{query}"

            # Call the query_model function
            response = generate_ollama_response(model_key, input_text)

            # Update chat history
            self.append_query_message("You", query)
            self.append_query_message("NeuroVision", response)

            # Save the query and response for the current document
            if self.selected_file not in self.query_histories:
                self.query_histories[self.selected_file] = []
            self.query_histories[self.selected_file].append({"query": query, "response": response})

            # Save the query history to a file
            self.save_query_history(self.selected_file, self.query_histories[self.selected_file])

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to process query: {str(e)}")
        finally:
            # Hide the loading indicator
            self.loading_label.setVisible(False)

    
    def show_document_context_menu(self, pos, message_frame, content_label):
        menu = QMenu()

        # Add edit, copy, and delete actions to the menu
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_document_message(message_frame, content_label))
        menu.addAction(edit_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.copy_document_message(content_label.text()))
        menu.addAction(copy_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_document_message(message_frame))
        menu.addAction(delete_action)

        menu.exec(message_frame.mapToGlobal(pos))


    def edit_document_message(self, message_frame, content_label):
        """
        Edit the content of a document message.
        """
        original_text = content_label.text()
        new_text, ok = QInputDialog.getText(self, "Edit Message", "Edit your message:", text=original_text)
        if ok and new_text:
            content_label.setText(new_text)


    def copy_document_message(self, text):
        """
        Copy the content of a document message to the clipboard.
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(text)


    def delete_document_message(self, message_frame):
        """
        Delete a document message from the document interface.
        """
        self.chat_history_layout.removeWidget(message_frame)
        message_frame.deleteLater()

    def handle_document_error(self, error_message):
        """
        Handle errors that occur during document processing.
        """
        self.loading_label.setVisible(False)
        QMessageBox.warning(self, "Error", f"Failed to process document: {error_message}")

# ------------------- Image Generation Screen -------------------
class ImageGenerationScreen(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id  # Store the logged-in user's ID
        self.device = "cpu"  # Default to CPU
        self.pipe = None  # Model not loaded initially
        self.history = {}  # History dictionary maps prompt -> {"container": widget, "image_path": file path}
        self.initUI()
        self.load_model()
        self.load_history_from_db()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Text-to-Image Generation")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Input Area: Prompt and Generate Button
        input_layout = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Enter your prompt...")
        self.prompt_input.returnPressed.connect(self.handle_generate_button)
        input_layout.addWidget(self.prompt_input)
        self.generate_button = QPushButton("Generate Image")
        self.generate_button.clicked.connect(self.handle_generate_button)
        input_layout.addWidget(self.generate_button)
        main_layout.addLayout(input_layout)

        # Loading Indicator
        self.loading_label = QLabel("NeuroVision is generating your image...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 14px; font-style: italic; color: gray;")
        self.loading_label.setVisible(False)
        main_layout.addWidget(self.loading_label)

        # Chat History (Scroll Area) for generated messages
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.addStretch()  # So messages appear at the top
        self.history_scroll.setWidget(self.history_widget)
        main_layout.addWidget(self.history_scroll)

        self.setLayout(main_layout)

    def load_model(self, use_cuda=False):
        """Load the Stable Diffusion model dynamically based on the selected device."""
        if self.pipe is None:
            try:
                # Dynamically select the device
                if use_cuda and torch.cuda.is_available():
                    self.device = "cuda"
                elif torch.backends.mps.is_available():  # For macOS Metal Performance Shaders
                    self.device = "mps"
                elif torch.has_mps:  # For Intel GPUs (shared memory)
                    self.device = "mps"
                else:
                    self.device = "cpu"

                print(f"Loading model on {self.device}...")
                self.pipe = StableDiffusionPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-2-1",
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    use_safetensors=True
                ).to(self.device)
                print("Model loaded successfully.")
            except Exception as e:
                QMessageBox.critical(None, "Model Load Error", f"Failed to load model: {str(e)}")

    def unload_model(self):
        """Free GPU memory by unloading the model."""
        if self.pipe:
            print("Unloading model...")
            del self.pipe
            self.pipe = None
            torch.cuda.empty_cache()
            gc.collect()  # Force garbage collection
            self.device = "cpu"
            print("Model unloaded. Switched back to CPU.")

    def handle_generate_button(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a prompt.")
            return

        self.loading_label.setVisible(True)
        QApplication.processEvents()

        try:
            # Load model on CUDA only for image generation
            self.load_model(use_cuda=True)

            # Generate the image
            image = self.generate_image(prompt)
            image_path = self.save_image_to_disk(image, prompt)
            self.add_to_history(prompt, image_path)
            insert_image_history(self.user_id, prompt, image_path)  # Save with user_id
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate image: {str(e)}")
        finally:
            self.loading_label.setVisible(False)
            self.prompt_input.clear()

            # Unload the model to free GPU memory
            self.unload_model()

    def generate_image(self, prompt):
        """Load model to GPU, generate image, then unload."""
        if not torch.cuda.is_available():
            raise ValueError("CUDA is not available. Ensure you have a GPU with the correct drivers installed.")

        self.load_model()  # Load the model only when needed

        try:
            result = self.pipe(prompt=prompt, num_inference_steps=30)
            image = result.images[0]
            return image
        finally:
            self.unload_model()  # Free memory after use


    def save_image_to_disk(self, image, prompt):
        """Save the generated image to disk and return its file path."""
        os.makedirs(IMAGE_DIR, exist_ok=True)
        sanitized = "".join(c for c in prompt if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_")
        file_path = os.path.join(IMAGE_DIR, f"{sanitized}_{uuid.uuid4().hex}.png")
        image.save(file_path)
        return file_path

    def add_to_history(self, prompt, image_path):
        """Create a chat-style container for the prompt and generated image, and add it to the UI and history dict."""
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)
        container.setStyleSheet("background-color: #F5F5F5; border-radius: 10px; margin: 5px;")
        container_layout = QVBoxLayout(container)

        prompt_label = QLabel(f"You: {prompt}")
        prompt_label.setStyleSheet("font-weight: bold;")
        container_layout.addWidget(prompt_label)

        pixmap = QPixmap(image_path)
        image_label = QLabel()
        image_label.setPixmap(pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        container_layout.addWidget(image_label)

        container.setContextMenuPolicy(Qt.CustomContextMenu)
        container.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, container, prompt_label, image_label)
        )

        index = self.history_layout.count() - 1
        self.history_layout.insertWidget(index, container)

        self.history[prompt] = {"container": container, "image_path": image_path}

        QTimer.singleShot(100, lambda: self.history_scroll.verticalScrollBar().setValue(
            self.history_scroll.verticalScrollBar().maximum()
        ))

    def extract_text_from_image(self, image_path):
        """
        Extract text from an image using Tesseract OCR, with resizing for optimization.
        """
        try:
            image = Image.open(image_path)
            # Resize image if it's too large
            max_size = (1600, 1600)  # Adjust as needed
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.ANTIALIAS)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            return f"Error extracting text from image: {str(e)}"

    def load_history_from_db(self):
        """Load history from the database for the logged-in user."""
        records = get_image_history(self.user_id)  # Pass the user_id here
        for entry in records:
            prompt = entry["prompt"]
            image_path = entry["image_path"]
            if os.path.exists(image_path):
                self.add_to_history(prompt, image_path)

    def show_context_menu(self, position, container, prompt_label, image_label):
        """Show context menu for a chat container with options to edit, copy, download, or delete."""
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Prompt")
        copy_action = menu.addAction("Copy Prompt")
        download_action = menu.addAction("Download Image")
        delete_action = menu.addAction("Delete Prompt & Image")
        action = menu.exec_(container.mapToGlobal(position))
        if action == edit_action:
            self.edit_prompt(container, prompt_label, image_label)
        elif action == copy_action:
            self.copy_prompt(prompt_label.text().replace("You: ", ""))
        elif action == download_action:
            self.download_image(prompt_label.text().replace("You: ", ""))
        elif action == delete_action:
            self.delete_history_item(container, prompt_label.text().replace("You: ", ""))

    def edit_prompt(self, container, prompt_label, image_label):
        """Allow the user to edit the prompt and regenerate the image for that container."""
        old_prompt = prompt_label.text().replace("You: ", "")
        new_prompt, ok = QInputDialog.getText(self, "Edit Prompt", "Edit your prompt:", text=old_prompt)
        if ok and new_prompt.strip():
            try:
                new_image = self.generate_image(new_prompt)
                new_image_path = self.save_image_to_disk(new_image, new_prompt)
                prompt_label.setText(f"You: {new_prompt}")
                new_pixmap = QPixmap(new_image_path)
                image_label.setPixmap(new_pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.history.pop(old_prompt, None)
                self.history[new_prompt] = {"container": container, "image_path": new_image_path}
                # Update database record: remove the old record and insert the new one
                delete_image_history(self.user_id, old_prompt)  # Pass user_id here
                insert_image_history(self.user_id, new_prompt, new_image_path)  # Pass user_id here
            except Exception as e:
                QMessageBox.critical(self, "Edit Error", f"Failed to regenerate image: {str(e)}")

    def copy_prompt(self, prompt):
        """Copy the prompt text to the clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(prompt)

    def delete_history_item(self, container, prompt):
        """Delete the chat container and remove its record from history and DB."""
        self.history_layout.removeWidget(container)
        container.deleteLater()
        self.history.pop(prompt, None)
        delete_image_history(self.user_id, prompt)  # Pass user_id here

    def download_image(self, prompt):
        """Download the generated image for the given prompt using a file dialog."""
        if prompt not in self.history:
            QMessageBox.warning(self, "Download Error", "Prompt not found in history.")
            return
        image_path = self.history[prompt]["image_path"]
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", f"{prompt.replace(' ', '_')}.png")
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", default_path, "PNG Files (*.png)")
        if file_path:
            if not QPixmap(image_path).save(file_path, "PNG"):
                QMessageBox.warning(self, "Download Error", "Failed to save image.")
            else:
                QMessageBox.information(self, "Download", f"Image saved to {file_path}")

# ------------------- Chat Screen -------------------
class ChatResponseThread(QThread):
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model, prompt):
        super().__init__()
        self.model = model
        self.prompt = prompt

    def run(self):
        try:
            response = generate_ollama_response(self.model, self.prompt)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ChatScreen(QWidget):
    def __init__(self, chat_id, user_id, model="mistral:7b"):
        super().__init__()
        self.chat_id = chat_id
        self.user_id = user_id
        self.model = model
        self.messages = []  # Local copy of messages (in addition to DB)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_recording = False
        self.tts_engine = pyttsx3.init()
        self.tts_engine.connect('finished-utterance', self.on_speech_finished)
        self.speech_paused = False
        self.speech_text = ""
        self.speech_position = 0
        self.initUI()
        self.load_chat_history()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_widget)
        main_layout.addWidget(self.scroll_area)

        # Add a loading indicator
        self.loading_label = QLabel("NeuroGenius is thinking...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 14px; font-style: italic; color: gray;")
        self.loading_label.setVisible(False)  # Initially hidden
        main_layout.addWidget(self.loading_label)
        
        # Input area: text input, send button, model selection, and mic button
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input, 3)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button, 0)
        
        self.model_combo = QComboBox()
        self.models = {
            "NeuroGenius": "llama2:7b",
            "NeuroGenius1": "mistral:7b",
            "NeuroGenius2": "deepseek-r1:7b"
        }
        for display, model in self.models.items():
            self.model_combo.addItem(display, model)
        # Set default index (e.g., NeuroGenius1)
        self.model_combo.setCurrentIndex(1)
        input_layout.addWidget(QLabel("Model:"), 0)
        input_layout.addWidget(self.model_combo, 1)
        
        self.mic_button = QPushButton("🎤 Start")
        self.mic_button.clicked.connect(self.toggle_recording)
        input_layout.addWidget(self.mic_button, 0)
        
        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.is_recording = True
        self.mic_button.setText("🛑 Stop")
        self.recognizer.listen_in_background(self.microphone, self.recognize_speech)

    def stop_recording(self):
        self.is_recording = False
        self.mic_button.setText("🎤 Start")

    def recognize_speech(self, recognizer, audio):
        try:
            text = recognizer.recognize_google(audio)
            self.message_input.setText(text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

    def load_chat_history(self):
        try:
            message_history = get_messages(self.chat_id)
            if message_history:
                for msg in message_history:
                    self.messages.append({"role": msg["role"], "content": msg["content"]})
                    sender = "You" if msg["role"] == "user" else "NeuroGenius GPT"
                    self.append_message(sender, msg["content"], suppress_db=True)
                QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().maximum()))
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")

    def send_message(self):
        user_input = self.message_input.text().strip()
        if not user_input:
            return

        # Append the user's message to the chat interface
        self.append_message("You", user_input)

        # Show the loading indicator
        self.loading_label.setVisible(True)

        # Prepare the input for the model
        chat_history = "\n".join(
            [f"You: {msg['content']}" if msg['role'] == "user" else f"AI: {msg['content']}" for msg in self.messages]
        )
        input_text = f"{chat_history}\nYou: {user_input}"

        # Start the background thread for response generation
        self.response_thread = ChatResponseThread(self.model, input_text)
        self.response_thread.response_ready.connect(self.display_response)
        self.response_thread.error_occurred.connect(self.handle_response_error)
        self.response_thread.start()

        # Add the user's message to the local message list
        self.messages.append({"role": "user", "content": user_input})

    def display_response(self, response):
        # Hide the loading indicator
        self.loading_label.setVisible(False)

        # Append the AI's response to the chat interface
        self.append_message("NeuroGenius GPT", response)

        # Add the AI's response to the local message list
        self.messages.append({"role": "assistant", "content": response})

        # Save the message to the database
        insert_message(self.chat_id, "assistant", response)

    def handle_response_error(self, error_message):
        self.loading_label.setVisible(False)
        QMessageBox.warning(self, "Error", f"Failed to generate response: {error_message}")

    def append_message(self, sender, message, suppress_db=False):
        message_frame = QFrame()
        message_frame.setFrameShape(QFrame.StyledPanel)
        if sender == "You":
            message_frame.setStyleSheet("background-color: #E1F5FE; border-radius: 10px; margin: 5px;")
        else:
            message_frame.setStyleSheet("background-color: #F5F5F5; border-radius: 10px; margin: 5px;")
        layout = QVBoxLayout(message_frame)
        sender_label = QLabel(sender)
        sender_label.setStyleSheet("font-weight: bold;")
        content_label = QLabel(message)
        content_label.setWordWrap(True)
        
        # Create a horizontal layout for the message content
        content_layout = QHBoxLayout()
        content_layout.addWidget(content_label)
        
        layout.addWidget(sender_label)
        layout.addLayout(content_layout)

        # Set context menu policy for the message frame
        message_frame.setContextMenuPolicy(Qt.CustomContextMenu)
        message_frame.customContextMenuRequested.connect(lambda pos: self.show_message_context_menu(pos, message_frame, content_label))

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_frame)

    def show_message_context_menu(self, pos, message_frame, content_label):
        menu = QMenu()

        # Add edit, copy, delete, speech, pause, and download actions to the menu with icons
        edit_action = QAction(QIcon("assets/edit_icon.png"), "Edit", self)
        edit_action.triggered.connect(lambda: self.edit_chat_message(message_frame, content_label))
        menu.addAction(edit_action)

        copy_action = QAction(QIcon("assets/copy_icon.png"), "Copy", self)
        copy_action.triggered.connect(lambda: self.copy_chat_message(content_label.text()))
        menu.addAction(copy_action)

        delete_action = QAction(QIcon("assets/delete_icon.png"), "Delete", self)
        delete_action.triggered.connect(lambda: self.delete_chat_message(message_frame))
        menu.addAction(delete_action)

        speech_action = QAction(QIcon("assets/speech_icon.png"), "Speak", self)
        speech_action.triggered.connect(lambda: self.speak_message(content_label.text()))
        menu.addAction(speech_action)

        pause_action = QAction(QIcon("assets/pause_icon.png"), "Pause", self)
        pause_action.triggered.connect(self.pause_speech)
        menu.addAction(pause_action)

        download_action = QAction(QIcon("assets/download_icon.png"), "Download", self)
        download_action.triggered.connect(lambda: self.download_message(content_label.text()))
        menu.addAction(download_action)

        menu.exec(message_frame.mapToGlobal(pos))


    def edit_chat_message(self, message_frame, content_label):
        """
        Edit the content of a chat message.
        """
        original_text = content_label.text()
        new_text, ok = QInputDialog.getText(self, "Edit Message", "Edit your message:", text=original_text)
        if ok and new_text:
            content_label.setText(new_text)
            # Update the message in the local list and database if necessary
            for message in self.messages:
                if message["content"] == original_text:
                    message["content"] = new_text
                    break
            # Regenerate the response based on the edited prompt
            response = generate_ollama_response(self.model, new_text)
            self.append_message("NeuroGenius GPT", response)
            insert_message(self.chat_id, "assistant", response)


    def copy_chat_message(self, text):
        """
        Copy the content of a chat message to the clipboard.
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(text)


    def delete_chat_message(self, message_frame):
        """
        Delete a chat message from the chat interface.
        """
        self.messages_layout.removeWidget(message_frame)
        message_frame.deleteLater()
        # Remove the message from the local list and database if necessary
        # ...


    def speak_message(self, text):
        if self.speech_paused:
            self.tts_engine.endLoop()
            self.speech_paused = False
        else:
            self.speech_text = text
            self.speech_position = 0
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()


    def pause_speech(self):
        self.tts_engine.stop()
        self.speech_paused = True


    def download_message(self, text):
        filename = f"message_{uuid.uuid4()}.mp3"
        self.tts_engine.save_to_file(text, filename)
        self.tts_engine.runAndWait()
        QMessageBox.information(self, "Download", f"Message downloaded as {filename}")

    def get_chat_history(self):
        return self.messages
    
    def on_speech_finished(self, name, completed):
        """
        Handle the 'finished-utterance' signal from the TTS engine.
        """
        if not completed and self.speech_paused:
            self.speech_position = self.tts_engine.getProperty('position')
        else:
            self.speech_paused = False


# ------------------- Main Window -------------------
class MainWindow(QWidget):
    def __init__(self, switch_stack_fn):
        super().__init__()
        self.switch_stack_fn = switch_stack_fn
        self.username = ""
        self.user_id = ""
        self.setWindowTitle("NeuroGenius GPT - Dashboard")
        self.chats = {}  # Dictionary: chat_id -> {"name": str, "model": str, "widget": ChatScreen}
        self.current_chat_id = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        
        # Top Bar
        top_bar = QHBoxLayout()
        self.welcome_label = QLabel("Welcome, User!")
        self.welcome_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_bar.addWidget(self.welcome_label)
        top_bar.addStretch()
        
        # Menu Button
        self.menu_button = QToolButton()
        icon_path = "assets/three_dots.png"
        if os.path.exists(icon_path):
            self.menu_button.setIcon(QIcon(icon_path))
        else:
            self.menu_button.setText("⋮")
            self.menu_button.setStyleSheet("font-size: 18px;")
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self)
        profile_action = QAction("Profile", self)
        subscribe_action = QAction("Subscribe", self)
        history_action = QAction("History", self)
        logout_action = QAction("Logout", self)
        profile_action.triggered.connect(self.open_profile)
        subscribe_action.triggered.connect(self.open_subscription)
        history_action.triggered.connect(self.open_history)
        logout_action.triggered.connect(self.handle_logout)
        menu.addAction(profile_action)
        menu.addAction(subscribe_action)
        menu.addAction(history_action)
        menu.addSeparator()
        menu.addAction(logout_action)
        self.menu_button.setMenu(menu)
        top_bar.addWidget(self.menu_button)
        main_layout.addLayout(top_bar)

        # Content Layout
        content_layout = QHBoxLayout()
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setMaximumWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/neurogenius_logo.jpg")
        if not logo_pixmap.isNull():
            size = 80
            logo_pixmap = logo_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            rounded = QPixmap(size, size)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, logo_pixmap)
            painter.end()
            logo_label.setPixmap(rounded)
        else:
            logo_label.setText("NEUROGENIUS")
            logo_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        sidebar_layout.addSpacing(20)
        
        # Navigation Buttons
        nav_title = QLabel("Navigation")
        nav_title.setStyleSheet("font-weight: bold;")
        sidebar_layout.addWidget(nav_title)
        self.home_btn = QPushButton("Home")
        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.chat_btn = QPushButton("Chats")
        self.chat_btn.clicked.connect(lambda: self.switch_page(1))
        self.doc_btn = QPushButton("Documents")
        self.doc_btn.clicked.connect(lambda: self.switch_page(2))
        self.img_gen_btn = QPushButton("Image Generation")
        self.img_gen_btn.clicked.connect(lambda: self.switch_page(3))
        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.chat_btn)
        sidebar_layout.addWidget(self.doc_btn)
        sidebar_layout.addWidget(self.img_gen_btn)
        sidebar_layout.addSpacing(10)
        
        # Chat Section
        self.chat_section = QWidget()
        chat_section_layout = QVBoxLayout(self.chat_section)
        chat_title = QLabel("My Chats")
        chat_title.setStyleSheet("font-weight: bold;")
        chat_section_layout.addWidget(chat_title)
        self.chat_list = QListWidget()
        self.chat_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_context_menu)
        self.chat_list.itemClicked.connect(self.select_chat)
        chat_section_layout.addWidget(self.chat_list)
        self.new_chat_button = QPushButton("+ New Chat")
        self.new_chat_button.clicked.connect(self.create_new_chat)
        chat_section_layout.addWidget(self.new_chat_button)
        sidebar_layout.addWidget(self.chat_section)
        self.chat_section.setVisible(False)
        sidebar_layout.addStretch()
        
        # Back to Home Button
        self.back_home_button = QPushButton("← Back to Home")
        self.back_home_button.clicked.connect(lambda: self.switch_page(0))
        sidebar_layout.addWidget(self.back_home_button)
        self.back_home_button.setVisible(False)
        content_layout.addWidget(self.sidebar)
        
        # Stacked Widget (Pages)
        self.stack = QStackedWidget()
        self.home_page = HomePage(self.switch_page)
        self.chat_page = QWidget()
        self.image_generation_page = ImageGenerationScreen(self.user_id)  # Pass user_id here
        
        # Chat Page Stack
        self.chat_stack = QStackedWidget()
        chat_page_layout = QVBoxLayout()
        chat_page_layout.addWidget(self.chat_stack)
        self.chat_page.setLayout(chat_page_layout)
        
        # Add Pages to Stack
        self.stack.addWidget(self.home_page)     # index 0
        self.stack.addWidget(self.chat_page)     # index 1
        self.stack.addWidget(self.image_generation_page)  # index 2
        
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.stack.setCurrentIndex(0)
        
        self.chats = {}
        self.current_chat_id = None
        self.update_sidebar_visibility()

    def set_username(self, username, user_id):
        """
        Set the username and user_id for the session.
        """
        self.username = username
        self.user_id = user_id
        self.welcome_label.setText(f"Welcome, {username}!")
        log_user_action(user_id, "Logged in", f"Username: {username}")
        self.load_user_chats()

        # Initialize DocumentScreen only if username is valid
        if self.username:
            self.document_page = DocumentScreen(self.username)
            self.stack.insertWidget(2, self.document_page)  # Add DocumentScreen to the stack
        else:
            raise ValueError("Username must be set before initializing DocumentScreen.")

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        if index == 1 and not self.chats:
            self.create_new_chat()
        self.update_sidebar_visibility()

    def update_sidebar_visibility(self):
        current_index = self.stack.currentIndex()
        if current_index == 1:
            self.chat_section.setVisible(True)
            self.back_home_button.setVisible(True)
            self.home_btn.setVisible(False)
            self.chat_btn.setVisible(False)
            self.doc_btn.setVisible(False)
        else:
            self.chat_section.setVisible(False)
            self.back_home_button.setVisible(False)
            self.home_btn.setVisible(True)
            self.chat_btn.setVisible(True)
            self.doc_btn.setVisible(True)

    def load_user_chats(self):
        # Clear current chats and UI list
        self.chats = {}
        self.chat_list.clear()
        while self.chat_stack.count() > 0:
            widget = self.chat_stack.widget(0)
            self.chat_stack.removeWidget(widget)
            widget.deleteLater()
        user_chats = get_chats_by_user(self.user_id)
        if user_chats:
            for chat in user_chats:
                chat_id = chat["id"]
                chat_name = chat["name"]
                model = chat["model"]
                chat_widget = ChatScreen(chat_id, self.user_id, model)
                self.chats[chat_id] = {"name": chat_name, "model": model, "widget": chat_widget}
                self.chat_stack.addWidget(chat_widget)
                item = QListWidgetItem(chat_name)
                item.setData(Qt.ItemDataRole.UserRole, chat_id)
                self.chat_list.addItem(item)
            self.chat_list.setCurrentRow(0)
            first_chat_id = self.chat_list.item(0).data(Qt.ItemDataRole.UserRole)
            self.current_chat_id = first_chat_id
            self.chat_stack.setCurrentWidget(self.chats[first_chat_id]["widget"])
        else:
            self.create_new_chat()

    def create_new_chat(self):
        chat_id = str(uuid.uuid4())
        chat_name = f"Chat {len(self.chats) + 1}"
        model = "mistral:7b"
        create_chat(self.user_id, chat_id, chat_name, model)
        chat_widget = ChatScreen(chat_id, self.user_id, model)
        self.chats[chat_id] = {"name": chat_name, "model": model, "widget": chat_widget}
        self.chat_stack.addWidget(chat_widget)
        item = QListWidgetItem(chat_name)
        item.setData(Qt.ItemDataRole.UserRole, chat_id)
        self.chat_list.addItem(item)
        self.chat_list.setCurrentItem(item)
        self.chat_stack.setCurrentWidget(chat_widget)
        self.current_chat_id = chat_id
        self.switch_page(1)

    def select_chat(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id in self.chats:
            self.current_chat_id = chat_id
            self.chat_stack.setCurrentWidget(self.chats[chat_id]["widget"])

    def download_chat(self, chat_id):
        """
        Download the chat history for the specified chat ID.
        """
        if chat_id not in self.chats:
            QMessageBox.warning(self, "Error", "Chat not found.")
            return

        chat_name = self.chats[chat_id]["name"]
        try:
            # Export the chat using the database function
            export_path = export_chat(chat_id, format="txt")  # You can also use "json"
            QMessageBox.information(self, "Download Successful", f"Chat '{chat_name}' downloaded to {export_path}.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to download chat: {str(e)}")

    def show_chat_context_menu(self, pos: QPoint):
        item = self.chat_list.itemAt(pos)
        if not item:
            return
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        rename_action = QAction("Rename Chat", self)
        delete_action = QAction("Delete Chat", self)
        download_action = QAction("Download Chat", self)
        rename_action.triggered.connect(lambda: self.rename_chat(chat_id))
        delete_action.triggered.connect(lambda: self.delete_chat(chat_id))
        download_action.triggered.connect(lambda: self.download_chat(chat_id))
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addAction(download_action)
        menu.exec(self.chat_list.mapToGlobal(pos))

    def rename_chat(self, chat_id):
        current_name = self.chats[chat_id]["name"]
        new_name, ok = QInputDialog.getText(self, "Rename Chat", "Enter new chat name:", text=current_name)
        if ok and new_name:
            update_chat_name(chat_id, new_name)
            self.chats[chat_id]["name"] = new_name
            for i in range(self.chat_list.count()):
                item = self.chat_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == chat_id:
                    item.setText(new_name)
                    break

    def delete_chat(self, chat_id):  # Corrected import path
        if chat_id in self.chats:
            delete_chat(chat_id)
            widget = self.chats[chat_id]["widget"]
            self.chat_stack.removeWidget(widget)
            widget.deleteLater()
            for i in range(self.chat_list.count()):
                item = self.chat_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == chat_id:
                    self.chat_list.takeItem(i)
                    break
            del self.chats[chat_id]
            if self.chat_list.count() > 0:
                item = self.chat_list.item(0)
                self.chat_list.setCurrentItem(item)
                self.current_chat_id = item.data(Qt.ItemDataRole.UserRole)
                self.chat_stack.setCurrentWidget(self.chats[self.current_chat_id]["widget"])
            else:
                self.create_new_chat()

    def open_profile(self):
        class ProfileDialog(QDialog):
            def __init__(self, username, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Edit Profile")
                self.resize(400, 300)
                self.username = username
                self.load_profile_details()
                layout = QVBoxLayout()
                layout.addWidget(QLabel("Edit your profile details:"))
                self.username_edit = QLineEdit(self.username)
                layout.addWidget(QLabel("Username:"))
                layout.addWidget(self.username_edit)
                self.email_edit = QLineEdit(self.email)
                layout.addWidget(QLabel("Email:"))
                layout.addWidget(self.email_edit)
                self.phone_edit = QLineEdit()
                self.phone_edit.setPlaceholderText("Phone")
                self.phone_edit.setReadOnly(False)  # Ensure the field is not read-only
                self.phone_edit.setEnabled(True)  # Ensure the field is enabled
                layout.addWidget(self.phone_edit)
                self.password_input = QLineEdit()
                self.password_input.setPlaceholderText("Password")
                self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Mask input for password
                self.password_input.setReadOnly(False)  # Ensure the field is not read-only
                self.password_input.setEnabled(True)  # Ensure the field is enabled
                layout.addWidget(self.password_input)
                self.update_button = QPushButton("Update Profile")
                self.update_button.clicked.connect(self.update_profile)
                layout.addWidget(self.update_button)
                self.setLayout(layout)

            def load_profile_details(self):
                """
                Load profile details from a database or file.
                """
                try:
                    # Example: Load from a JSON file
                    with open("user_profile.json", "r") as f:
                        profile = json.load(f)
                        self.email = profile.get("email", f"{self.username.lower()}@example.com")
                        self.phone = profile.get("phone", "1234567890")
                except FileNotFoundError:
                    # Default values if no profile exists
                    self.email = f"{self.username.lower()}@example.com"
                    self.phone = "1234567890"

            def update_profile(self):
                """
                Save updated profile details to a database or file.
                """
                self.username = self.username_edit.text().strip()
                self.email = self.email_edit.text().strip()
                self.phone = self.phone_edit.text().strip()
                try:
                    # Example: Save to a JSON file
                    with open("user_profile.json", "w") as f:
                        json.dump({"username": self.username, "email": self.email, "phone": self.phone}, f)
                    QMessageBox.information(self, "Success", "Profile updated successfully!")
                    self.accept()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to save profile: {str(e)}")

        dialog = ProfileDialog(self.username, self)
        dialog.exec()

    def open_subscription(self):
        class SubscriptionDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Subscribe for Premium")
                self.resize(400, 200)
                layout = QVBoxLayout()
                title = QLabel("NeuroGenius GPT Premium")
                title.setStyleSheet("font-size: 18px; font-weight: bold;")
                title.setAlignment(Qt.AlignCenter)
                features = QLabel("• Access to all models\n• Higher message limits\n• Priority processing\n• Advanced features")
                coming_soon = QLabel("Subscription functionality coming soon!")
                coming_soon.setAlignment(Qt.AlignCenter)
                coming_soon.setStyleSheet("font-style: italic;")
                layout.addWidget(title)
                layout.addWidget(features)
                layout.addSpacing(20)
                layout.addWidget(coming_soon)
                self.setLayout(layout)
        dialog = SubscriptionDialog(self)
        dialog.exec()

    def open_history(self):
        class HistoryDialog(QDialog):
            def __init__(self, user_id, parent=None):
                super().__init__(parent)
                self.user_id = user_id
                self.setWindowTitle("Usage History")
                self.resize(800, 500)
                layout = QVBoxLayout()
                self.tabs = QTabWidget()
                self.log_tab = QWidget()
                self.stats_tab = QWidget()
                self.tabs.addTab(self.log_tab, "Activity Log")
                self.tabs.addTab(self.stats_tab, "Usage Statistics")
                log_layout = QVBoxLayout(self.log_tab)
                self.log_text = QTextEdit()
                self.log_text.setReadOnly(True)
                log_layout.addWidget(self.log_text)
                stats_layout = QVBoxLayout(self.stats_tab)
                self.stats_label = QLabel()
                self.stats_label.setStyleSheet("font-size: 14px;")
                stats_layout.addWidget(self.stats_label)
                stats_layout.addStretch()
                layout.addWidget(self.tabs)
                self.setLayout(layout)
                self.load_logs()
                self.load_statistics()

            def load_logs(self):
                """
                Load activity logs from a file or database.
                """
                try:
                    with open("logs/app_usage.log", "r") as f:
                        content = f.read()
                    filtered = "\n".join(line for line in content.splitlines() if f"User {self.user_id}" in line)
                    self.log_text.setText(filtered if filtered else "No activity found for your account.")
                except FileNotFoundError:
                    self.log_text.setText("No activity log found.")
                except Exception as e:
                    self.log_text.setText(f"Error loading logs: {str(e)}")

            def load_statistics(self):
                """
                Load usage statistics from a database or file.
                """
                try:
                    stats = get_usage_statistics(self.user_id, days=30)
                    if stats:
                        summary = (
                            f"<b>Usage Summary (Last {stats['period_days']} days)</b><br>"
                            f"Total messages: {stats['total_messages']}<br>"
                            f"Your messages: {stats['user_messages']}<br>"
                            f"AI responses: {stats['assistant_messages']}<br>"
                        )
                        self.stats_label.setText(summary)
                    else:
                        self.stats_label.setText("No usage statistics available.")
                except Exception as e:
                    self.stats_label.setText(f"Error loading statistics: {str(e)}")

        dialog = HistoryDialog(self.user_id, self)
        dialog.exec()

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        if index == 1 and not self.chats:
            self.create_new_chat()
        self.update_sidebar_visibility()

    def handle_logout(self):
        from database.database_chat import log_user_action  # Corrected import path
        try:
            log_user_action(self.user_id, "Logged out")
            self.switch_stack_fn("login")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to log out: {str(e)}")

    # Ensure threads are stopped before deletion
    def closeEvent(self, event):
        """
        Ensure all threads are stopped before the window is closed.
        """
        if hasattr(self, 'response_thread') and self.response_thread.isRunning():
            self.response_thread.quit()
            self.response_thread.wait()

        if hasattr(self, 'processor_thread') and self.processor_thread.isRunning():
            self.processor_thread.quit()
            self.processor_thread.wait()

        event.accept()

# ------------------- End of MainWindow -------------------
