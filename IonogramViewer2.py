import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from config import Config


def main():
    app = QApplication(sys.argv)

    config = Config("data/IonogramViewer2.ini")

    program_configuration = config.get_parameters()

    window = MainWindow(program_configuration)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
