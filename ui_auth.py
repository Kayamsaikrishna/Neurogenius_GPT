from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from authentication import register, login, request_password_reset, reset_password, send_welcome

class AuthScreen(QWidget):
    def __init__(self, switch_to_main_callback, switch_screen_callback):
        super().__init__()
        self.switch_to_main_callback = switch_to_main_callback
        self.switch_screen_callback = switch_screen_callback

        self.setWindowTitle("NeuroGenius GPT - Login")
        self.resize(400, 250)

        layout = QVBoxLayout()

        # Add Logo at the top (rounded)
        logo_label = QLabel()
        from PySide6.QtGui import QPixmap, QPainter, QPainterPath
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

        self.title_label = QLabel("Login")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Enter Username / Email / Phone")
        layout.addWidget(self.identifier_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(lambda: self.switch_screen_callback("register"))
        layout.addWidget(self.register_button)

        self.forgot_button = QPushButton("Forgot Password?")
        self.forgot_button.clicked.connect(lambda: self.switch_screen_callback("forgot"))
        layout.addWidget(self.forgot_button)

        self.setLayout(layout)

    def handle_login(self):
        identifier = self.identifier_input.text().strip()
        password = self.password_input.text().strip()
        if login(identifier, password):
            self.switch_to_main_callback(identifier)
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials")

class RegisterScreen(QWidget):
    def __init__(self, switch_screen_callback):
        super().__init__()
        self.switch_screen_callback = switch_screen_callback

        self.setWindowTitle("NeuroGenius GPT - Register")
        self.resize(400, 300)

        layout = QVBoxLayout()

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
        self.back_button.clicked.connect(lambda: self.switch_screen_callback("login"))
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
            send_welcome(email)
            self.switch_screen_callback("login")
        else:
            QMessageBox.warning(self, "Error", "Username/Email/Phone already exists.")

class ForgotScreen(QWidget):
    def __init__(self, switch_screen_callback):
        super().__init__()
        self.switch_screen_callback = switch_screen_callback
        self.setWindowTitle("NeuroGenius GPT - Forgot Password")
        self.resize(400, 300)

        layout = QVBoxLayout()

        self.title_label = QLabel("Password Reset")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Enter Username / Email / Phone")
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
        self.back_button.clicked.connect(lambda: self.switch_screen_callback("login"))
        layout.addWidget(self.back_button)

        self.setLayout(layout)
        self.otp_cache = None

    def request_otp(self):
        identifier = self.identifier_input.text().strip()
        if not identifier:
            QMessageBox.warning(self, "Error", "Please enter your identifier.")
            return
        success, result = request_password_reset(identifier)
        if success:
            self.otp_cache = result
            QMessageBox.information(self, "Success", "OTP sent to your email.")
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

        reset_password(identifier, self.otp_cache, newpass)
        QMessageBox.information(self, "Success", "Password reset successful!")
        self.switch_screen_callback("login")
