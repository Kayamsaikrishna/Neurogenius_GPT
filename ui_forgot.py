from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from authentication import request_password_reset, reset_password
from PySide6.QtGui import QPixmap, QPainter, QPainterPath

class ForgotScreen(QWidget):
    def __init__(self, switch_stack_fn):
        """
        switch_stack_fn: function to switch back to login
        """
        super().__init__()
        self.switch_stack_fn = switch_stack_fn

        self.setWindowTitle("NeuroGenius GPT - Forgot Password")
        self.resize(400, 300)

        layout = QVBoxLayout()

 # Logo at the top (rounded)
        logo_label = QLabel()
        pixmap = QPixmap("assets/neurogenius_logo.jpg")
        size = 100
        pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        rounded = QPixmap(size, size)
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        logo_label.setPixmap(rounded)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)


        self.title_label = QLabel("Password Reset")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Username / Email / Phone")
        layout.addWidget(self.identifier_input)

        self.request_button = QPushButton("Request OTP")
        self.request_button.clicked.connect(self.request_otp)
        layout.addWidget(self.request_button)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter OTP")
        layout.addWidget(self.otp_input)

        self.newpass_input = QLineEdit()
        self.newpass_input.setPlaceholderText("New Password")
        self.newpass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.newpass_input)

        self.confirmpass_input = QLineEdit()
        self.confirmpass_input.setPlaceholderText("Confirm New Password")
        self.confirmpass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirmpass_input)

        self.reset_button = QPushButton("Reset Password")
        self.reset_button.clicked.connect(self.handle_reset)
        layout.addWidget(self.reset_button)

        self.back_button = QPushButton("Back to Login")
        self.back_button.clicked.connect(lambda: self.switch_stack_fn("login"))
        layout.addWidget(self.back_button)

        self.setLayout(layout)

        # Store the OTP in memory for demonstration
        self.otp_cache = None

    def request_otp(self):
        identifier = self.identifier_input.text().strip()
        if not identifier:
            QMessageBox.warning(self, "Error", "Please enter your identifier.")
            return

        success, result = request_password_reset(identifier)
        if success:
            self.otp_cache = result  # store OTP
            QMessageBox.information(self, "Success", f"OTP sent to your email.")
        else:
            QMessageBox.warning(self, "Error", result)

    def handle_reset(self):
        identifier = self.identifier_input.text().strip()
        entered_otp = self.otp_input.text().strip()
        newpass = self.newpass_input.text().strip()
        confirmpass = self.confirmpass_input.text().strip()

        if not self.otp_cache:
            QMessageBox.warning(self, "Error", "Please request OTP first.")
            return
        if entered_otp != self.otp_cache:
            QMessageBox.warning(self, "Error", "Invalid OTP.")
            return
        if newpass != confirmpass:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        reset_password(identifier, newpass)
        QMessageBox.information(self, "Success", "Password reset successful!")
        self.switch_stack_fn("login")
