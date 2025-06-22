from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from authentication import register, send_welcome_email
from PySide6.QtGui import QPixmap, QPainter, QPainterPath

class RegisterScreen(QWidget):
    def __init__(self, switch_stack_fn):
        """
        switch_stack_fn: function to switch back to login
        """
        super().__init__()
        self.switch_stack_fn = switch_stack_fn

        self.setWindowTitle("NeuroGenius GPT - Register")
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


        self.title_label = QLabel("Create an Account")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        layout.addWidget(self.phone_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.handle_register)
        layout.addWidget(self.register_button)

        self.back_button = QPushButton("Back to Login")
        self.back_button.clicked.connect(lambda: self.switch_stack_fn("login"))
        layout.addWidget(self.back_button)

        self.setLayout(layout)

    def handle_register(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()

        if not (username and email and phone and password):
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if register(username, email, phone, password):
            QMessageBox.information(self, "Success", "Account created successfully!")
            # Send a welcome email
            send_welcome_email(email, username)
            self.switch_stack_fn("login")
        else:
            QMessageBox.warning(self, "Error", "Username/Email/Phone already exists.")
