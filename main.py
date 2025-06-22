import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from ui_auth import AuthScreen
from ui_register import RegisterScreen
from ui_forgot import ForgotScreen
from ui_main import MainWindow

class AppStack(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroGenius GPT")
        self.resize(1000, 700)
        
        self.login_screen = AuthScreen(self.show_main, self.switch_screen)
        self.register_screen = RegisterScreen(self.switch_screen)
        self.forgot_screen = ForgotScreen(self.switch_screen)
        self.main_window = MainWindow(self.switch_screen)
        
        self.addWidget(self.login_screen)      # index 0
        self.addWidget(self.register_screen)   # index 1
        self.addWidget(self.forgot_screen)       # index 2
        self.addWidget(self.main_window)         # index 3
        
        self.setCurrentWidget(self.login_screen)

    def switch_screen(self, screen_name):
        if screen_name == "login":
            self.setCurrentWidget(self.login_screen)
        elif screen_name == "register":
            self.setCurrentWidget(self.register_screen)
        elif screen_name == "forgot":
            self.setCurrentWidget(self.forgot_screen)

    def show_main(self, identifier):
        # In a real application, get user_id from database.
        # Here we use a simple hash of the identifier.
        import hashlib
        user_id = hashlib.md5(identifier.encode()).hexdigest()
        self.main_window.set_username(identifier, user_id)
        self.setCurrentWidget(self.main_window)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stack = AppStack()
    stack.show()
    sys.exit(app.exec())
