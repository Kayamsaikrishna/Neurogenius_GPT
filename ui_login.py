class LoginScreen(QWidget):
    def __init__(self, switch_to_main_callback, switch_stack_fn):
        super().__init__()
        self.switch_to_main_callback = switch_to_main_callback
        self.switch_stack_fn = switch_stack_fn

        # Window settings
        self.setWindowTitle("NeuroGenius GPT - Login")
        self.resize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QLabel#title_label {
                font-size: 24px;
                font-weight: bold;
                color: #343a40;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #ced4da;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                color: white;
                background-color: #007bff;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton#forgot_button {
                background-color: transparent;
                color: #007bff;
                text-decoration: underline;
            }
            QPushButton#forgot_button:hover {
                color: #0056b3;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)

        # Logo at the top (rounded)
        logo_label = QLabel()
        pixmap = QPixmap("assets/neurogenius_logo.jpg")  # Replace with your logo path
        size = 120
        if not pixmap.isNull():
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
        else:
            logo_label.setText("NEUROGENIUS")
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff;")
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        # Title label
        title_label = QLabel("Welcome Back!")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Input fields
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Username / Email / Phone")
        main_layout.addWidget(self.identifier_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login)  # Trigger login on Enter key
        main_layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_button)

        # Forgot password button
        self.forgot_button = QPushButton("Forgot Password?")
        self.forgot_button.setObjectName("forgot_button")
        self.forgot_button.setCursor(Qt.PointingHandCursor)
        self.forgot_button.clicked.connect(lambda: self.switch_stack_fn("forgot"))
        main_layout.addWidget(self.forgot_button)

        # Register button
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)
        register_label = QLabel("Don't have an account?")
        register_label.setStyleSheet("color: #6c757d;")
        self.register_button = QPushButton("Register")
        self.register_button.setStyleSheet("""
            QPushButton {
                color: #007bff;
                background-color: transparent;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #0056b3;
            }
        """)
        self.register_button.setCursor(Qt.PointingHandCursor)
        self.register_button.clicked.connect(lambda: self.switch_stack_fn("register"))
        register_layout.addWidget(register_label)
        register_layout.addWidget(self.register_button)
        main_layout.addLayout(register_layout)

        # Set layout
        self.setLayout(main_layout)

    def handle_login(self):
        identifier = self.identifier_input.text().strip()
        password = self.password_input.text().strip()

        if not identifier or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        # Simulate authentication logic
        if self.authenticate(identifier, password):
            self.switch_to_main_callback(identifier)
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials.")

    def authenticate(self, identifier, password):
        # Replace this with your actual authentication logic (e.g., database check)
        return identifier == "admin" and password == "password"