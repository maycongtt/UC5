from portaria.validacao import cpf_valido, mascarar_documento, normalizar_documento

from datetime import datetime

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

SETORES = ["Secretaria", "Coordenação", "Laboratório"]
CRACHAS = [f"V-{n:02d}" for n in range(1, 11)]
COLUNAS = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"]

def somente_digitos(texto):
    return "".join(c for c in texto if c.isdigit())

class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portaria Digital")
        self.resize(820, 520)

        # Estado em memória: ainda some quando a aplicação fecha.
        self.visitantes = {}                 # cpf -> nome
        self.visitas = []                    # lista de dicionários
        self.crachas_livres = list(CRACHAS)  # crachás na gaveta da recepção
        self.proximo_id = 1

        # ---------- formulário de entrada ----------
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_cpf.setMaxLength(14)
        self.campo_nome = QLineEdit()
        self.combo_setor = QComboBox()
        self.combo_setor.addItem("Selecione um setor")
        self.combo_setor.addItems(SETORES)
        self.botao_entrada = QPushButton("Registrar entrada")
        self.botao_limpar = QPushButton("Limpar campos")
        self.mensagem = QLabel("Informe o CPF do visitante.")

        formulario = QFormLayout()
        formulario.addRow("&CPF:", self.campo_cpf)    # Alt+C
        formulario.addRow("&Nome:", self.campo_nome)  # Alt+N
        formulario.addRow("S&etor:", self.combo_setor)  # Alt+E

        botoes = QHBoxLayout()
        self.botao_entrada = QPushButton("&Registrar entrada")  #Alt+R
        self.botao_limpar = QPushButton("&Limpar campos")    #Alt+L

        # ---------- quem está no prédio ----------
        self.campo_filtro = QLineEdit()
        self.campo_filtro.setPlaceholderText("Filtrar por nome ou setor")
        self.tabela = QTableWidget(0, len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.botao_saida = QPushButton("Registrar &saída da visita selecionada")  # Alt+S
        self.contador = QLabel()

        layout = QVBoxLayout()
        layout.addLayout(formulario)
        layout.addLayout(botoes)
        layout.addWidget(self.mensagem)
        layout.addWidget(QLabel("No prédio agora:"))
        layout.addWidget(self.campo_filtro)
        layout.addWidget(self.tabela)
        layout.addWidget(self.botao_saida)
        layout.addWidget(self.contador)
        self.setLayout(layout)

        # ---------- eventos ----------
        # self.campo_cpf.editingFinished.connect(self.buscar_visitante)
        # self.botao_entrada.clicked.connect(self.registrar_entrada)
        # self.botao_limpar.clicked.connect(self.limpar_campos)
        # self.botao_saida.clicked.connect(self.registrar_saida)
        # self.campo_filtro.textChanged.connect(self.atualizar_tabela)

        self.atualizar_tabela()

    def registrar_entrada(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        nome = " ".join(self.campo_nome.text().split())

        if not cpf_valido(cpf):
            self.mensagem.setText("CPF inválido. Confira os 11 dígitos.")
            self.campo_cpf.setFocus()
            return
        # (...) validações de nome e setor continuam iguais
        if any(v["cpf"] == cpf for v in self.presentes()):
            self.mensagem.setText(f"{nome} já está no prédio. Registre a saída antes.")
            return
        if not self.crachas_livres:
            self.mensagem.setText("Não há crachá disponível. Aguarde uma devolução.")
            return

        self.visitantes.setdefault(cpf, nome)  # não sobrescreve cadastro existente
        # (...) o restante do método continua igual
   
    def registrar_entrada(self):
        cpf = "".join(c for c in self.campo_cpf.text() if c.isdigit())
        nome = " ".join(self.campo_nome.text().split())

        if len(cpf) != 11:
            self.mensagem.setText("O CPF precisa ter 11 dígitos.")
            self.campo_cpf.setFocus()
            return
        if not nome:
            self.mensagem.setText("Informe o nome do visitante.")
            self.campo_nome.setFocus()
            return
        if self.combo_setor.currentIndex() == 0:
            return

        setor = self.combo_setor.currentText()
        self.mensagem.setText(f"Dados válidos: {nome} para {setor}. Ainda não gravamos nada.")


    def registrar_saida(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            self.mensagem.setText("Selecione uma visita na tabela.")
            return
        visita_id = int(self.tabela.item(linha, 0).text())
        for visita in self.visitas:
            if visita["id"] == visita_id:
                visita["saida"] = datetime.now().strftime("%H:%M:%S")
                self.crachas_livres.append(visita["cracha"])
                self.mensagem.setText(f"Saída registrada. Crachá {visita['cracha']} devolvido.")
                break
        self.atualizar_tabela()

    def presentes(self):
        return [v for v in self.visitas if v["saida"] is None]

    def atualizar_tabela(self):
        termo = self.campo_filtro.text().strip().lower()
        linhas = []
        for v in self.presentes():
            texto = f"{self.visitantes[v['cpf']]} {v['setor']}".lower()
            if termo in texto:
                linhas.append(v)

        self.tabela.setRowCount(len(linhas))
        for i, v in enumerate(linhas):
            valores = [v["id"], self.visitantes[v["cpf"]], mascarar_documento(v["cpf"]),
                       v["setor"], v["cracha"], v["entrada"]]
            for j, valor in enumerate(valores):
                self.tabela.setItem(i, j, QTableWidgetItem(str(valor)))
        self.tabela.setCurrentCell(-1, -1)  # nenhuma visita fica selecionada sem querer

        self.contador.setText(
            f"No prédio: {len(self.presentes())} | Crachás livres: {len(self.crachas_livres)}"
        )


    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.campo_cpf.setFocus()
