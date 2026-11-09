from datetime import datetime
from portaria import repositorio as repo
import sqlite3

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from portaria.validacao import (
    cpf_valido,
    mascarar_documento,
    normalizar_documento,
    normalizar_nome,
)

SETORES = ["Secretaria", "Coordenação", "Laboratório"]
CRACHAS = [f"V-{n:02d}" for n in range(1, 11)]
COLUNAS = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"]


def somente_digitos(texto):
    return "".join(c for c in texto if c.isdigit())


class JanelaPrincipal(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Portaria Digital")
        self.resize(820, 520)

        # ---------- formulário de entrada ----------
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_cpf.setMaxLength(14)
        self.campo_nome = QLineEdit()
        self.combo_setor = QComboBox()
        # A lista de setores virá do banco em carregar_setores().
        self.botao_entrada = QPushButton("&Registrar entrada")
        self.botao_limpar = QPushButton("&Limpar campos")
        self.mensagem = QLabel("Informe o CPF do visitante.")

        formulario = QFormLayout()
        formulario.addRow("&CPF:", self.campo_cpf)
        formulario.addRow("&Nome:", self.campo_nome)
        formulario.addRow("S&etor:", self.combo_setor)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_entrada)
        botoes.addWidget(self.botao_limpar)

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
        self.botao_saida = QPushButton("Registrar &saída da visita selecionada")
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
        self.campo_cpf.editingFinished.connect(self.buscar_visitante)
        self.botao_entrada.clicked.connect(self.registrar_entrada)
        self.botao_limpar.clicked.connect(self.limpar_campos)
        self.botao_saida.clicked.connect(self.registrar_saida)
        self.campo_filtro.textChanged.connect(self.atualizar_tabela)

        # Inicialização do estado visual a partir do banco.
        self.carregar_setores()
        self.atualizar_tabela()

    def carregar_setores(self):
        selecionado = self.combo_setor.currentData()
        self.combo_setor.clear()
        self.combo_setor.addItem("Selecione um setor", None)
        for setor in repo.listar_setores_ativos(self.conn):
            self.combo_setor.addItem(setor["nome"], setor["id"])
        self.combo_setor.setCurrentIndex(max(self.combo_setor.findData(selecionado), 0))


    def buscar_visitante(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        visitante = repo.buscar_visitante_por_documento(self.conn, cpf)
        if visitante:
            self.campo_nome.setText(visitante["nome"])
            self.campo_nome.setReadOnly(True)
            self.mensagem.setText("Visitante já cadastrado. Escolha o setor.")
        else:
            if self.campo_nome.isReadOnly():
                self.campo_nome.clear()
            self.campo_nome.setReadOnly(False)
    
    def registrar_entrada(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        nome = " ".join(self.campo_nome.text().split())
        setor_id = self.combo_setor.currentData()

        if not cpf_valido(cpf):
            self.mensagem.setText("CPF inválido. Confira os 11 dígitos.")
            return
        if not nome:
            self.mensagem.setText("Informe o nome do visitante.")
            return
        if setor_id is None:
            self.mensagem.setText("Selecione o setor de destino.")
            return

        try:
            # Verificações antecipadas: evita abandonar uma transação já
            # iniciada por INSERT usando return dentro de with self.conn.
            visitante = repo.buscar_visitante_por_documento(self.conn, cpf)
            if visitante and repo.visita_aberta_do_visitante(self.conn, visitante["id"]):
                self.mensagem.setText(f"{nome} já está no prédio. Registre a saída antes.")
                return
            cracha = repo.buscar_cracha_disponivel(self.conn)
            if cracha is None:
                self.mensagem.setText("Não há crachá disponível. Aguarde uma devolução.")
                return

            with self.conn:
                visitante_id = (
                    visitante["id"] if visitante is not None
                    else repo.inserir_visitante(self.conn, nome, cpf)
                )
                repo.inserir_visita(
                    self.conn, visitante_id, setor_id, cracha["id"], None, agora()
                )
                repo.atualizar_situacao_cracha(self.conn, cracha["id"], "em_uso")
        except sqlite3.Error as erro:
            QMessageBox.critical(self, "Portaria Digital", f"Erro no banco: {erro}")
            return

        self.limpar_campos()
        self.mensagem.setText(f"Entrada registrada. Entregue o crachá {cracha['codigo']}.")
        self.atualizar_tabela()

    def registrar_saida(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            self.mensagem.setText("Selecione uma visita na tabela.")
            return
        visita_id = int(self.tabela.item(linha, 0).text())
        try:
            with self.conn:
                visita = repo.obter_visita(self.conn, visita_id)
                if visita is None or visita["saida"] is not None:
                    self.mensagem.setText("Esta visita já foi encerrada.")
                    return
                repo.encerrar_visita(self.conn, visita_id, agora())
                repo.atualizar_situacao_cracha(
                    self.conn, visita["cracha_id"], "disponivel"
                )
        except sqlite3.Error as erro:
            QMessageBox.critical(self, "Portaria Digital", f"Erro no banco: {erro}")
            return
        self.mensagem.setText("Saída registrada. Crachá devolvido.")
        self.atualizar_tabela()

    def atualizar_tabela(self):
        presentes = repo.listar_presentes(self.conn)
        termo = self.campo_filtro.text().strip().lower()
        linhas = [
            visita for visita in presentes
            if termo in f"{visita['nome']} {visita['setor']}".lower()
        ]
        self.tabela.setRowCount(len(linhas))
        for i, visita in enumerate(linhas):
            valores = [
                visita["id"], visita["nome"],
                mascarar_documento(visita["documento"]),
                visita["setor"], visita["cracha"], visita["entrada"]
            ]
            for j, valor in enumerate(valores):
                self.tabela.setItem(i, j, QTableWidgetItem(str(valor)))
        self.tabela.setCurrentCell(-1, -1)
        crachas = repo.contar_crachas_por_situacao(self.conn)
        self.contador.setText(
            f"No prédio: {len(presentes)} | "
            f"Crachás livres: {crachas.get('disponivel', 0)}"
        )
    def presentes(self):
        return [v for v in self.visitas if v["saida"] is None]

    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.campo_cpf.setFocus()