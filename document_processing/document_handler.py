import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PyPDF2 import PdfReader

def upload_document():
    """
    Open a file dialog to upload a document.
    Returns the file path of the uploaded document.
    """
    file_path, _ = QFileDialog.getOpenFileName(
        None, 
        "Upload Document", 
        "", 
        "Text Files (*.txt);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg);;All Files (*)"
    )
    if file_path:
        return file_path
    return None

def save_uploaded_document(file_path, save_dir):
    """
    Save the uploaded document to the specified directory.
    Returns the path where the document is saved.
    """
    try:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        file_name = os.path.basename(file_path)
        save_path = os.path.join(save_dir, file_name)
        with open(file_path, "rb") as src, open(save_path, "wb") as dest:
            dest.write(src.read())
        return save_path
    except Exception as e:
        QMessageBox.warning(None, "Error", f"Failed to save document: {str(e)}")
        return None

def list_documents(directory):
    """
    List all documents in the specified directory.
    Returns a list of file paths.
    """
    if not os.path.exists(directory):
        return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text.strip()  # Remove leading/trailing whitespace
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_txt(txt_path):
    """
    Extract text from a plain text file.
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        return f"Error extracting text from TXT file: {str(e)}"

def is_supported_file(file_path):
    """
    Check if the file is a supported type (PDF, TXT, or image).
    """
    supported_extensions = (".pdf", ".txt", ".png", ".jpg", ".jpeg")
    return file_path.lower().endswith(supported_extensions)