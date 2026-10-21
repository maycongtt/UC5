from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Visitantes")
        self.resize(520, 460)
        self.registros = []

        self.titulo = QLabel("Recepção — Registro de Visitantes")
        self.campo_nome = QLineEdit()
        self.campo_nome.setPlaceholderText("Nome completo")

        self.combo_destino = QComboBox()
        self.combo_destino.addItems([
            "Selecione um setor", "Secretaria",
            "Coordenação", "Laboratório",
        ])

        self.botao_cadastrar = QPushButton("Registrar visita")
        self.botao_limpar = QPushButton("Limpar campos")
        self.mensagem = QLabel("Preencha os campos.")
        self.lista = QListWidget()
        self.contador = QLabel("Visitas nesta sessão: 0")

        formulario = QFormLayout()
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Destino:", self.combo_destino)

        layout = QVBoxLayout()
        layout.addWidget(self.titulo)
        layout.addLayout(formulario)
        layout.addWidget(self.botao_cadastrar)
        layout.addWidget(self.botao_limpar)
        layout.addWidget(self.mensagem)
        layout.addWidget(QLabel("Visitantes registrados:"))
        layout.addWidget(self.lista)
        layout.addWidget(self.contador)
        self.setLayout(layout)

        # Os eventos da interface chamam métodos da classe.
        
        self.botao_cadastrar.clicked.connect(self.regitrar_visita)
        self.botao_limpar.clicked.connect(self.limpar_campos)

    def regitrar_visita(self):
        nome = self.campo_nome.text().strip()
        destino = self.combo_destino.currentText()

        if not nome:
            self.mensagem.setText("informe o nome do visitante.")
            self.mensagem.setStyleSheet("color: red;")
            self.campo_nome.setFocus()
            return

        if self.combo_destino.currentIndex() == 0:
            self.mensagem.setText("selecione o setor de destino.")
            return

        registro =  {"nome": nome, "destino": destino}
        self.registros.append(registro)
        self.lista.addItem(f"{nome} - {destino}")
        self.contador.setText(
            f"Visitas nesta sessão: {len(self.registros)}"
        )
        self.mensagem.setText("Visita registrada com sucesso!")
        self.limpar_campos()

    def limpar_campos(self):
        self.campo_nome.clear()
        self.combo_destino.setCurrentIndex(0)
        self.campo_nome.setFocus()