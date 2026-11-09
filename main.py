import sys

from PySide6.QtWidgets import QApplication

from portaria.db import conectar, preparar_banco
from portaria.ui.janela_principal import JanelaPrincipal


def main():
    conn = conectar()
    preparar_banco(conn)
    app = QApplication(sys.argv)
    janela = JanelaPrincipal(conn)
    janela.show()
    codigo = app.exec()
    conn.close()
    return codigo


if __name__ == "__main__":
    sys.exit(main())