import sys

from PySide6.QtWidgets import QApplication

from portaria.ui.janela_principal import JanelaPrincipal


def main():
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())