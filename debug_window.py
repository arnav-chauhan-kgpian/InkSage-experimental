import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
from PySide6.QtCore import Qt

def main():
    print("1. Creating App...")
    app = QApplication(sys.argv)
    
    print("2. Creating Window...")
    window = QMainWindow()
    window.setWindowTitle("InkSage Diagnostic")
    window.setGeometry(100, 100, 400, 200)
    
    label = QLabel("If you can see this,\nPySide6 is working!", window)
    label.setAlignment(Qt.AlignCenter)
    window.setCentralWidget(label)
    
    print("3. Showing Window...")
    window.show()
    
    print("4. Entering Event Loop...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()