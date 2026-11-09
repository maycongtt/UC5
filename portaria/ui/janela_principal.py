from datetime import datetime
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
        self.combo_setor.clear()
        self.combo_setor.addItem("Selecione um setor", None)
        linhas = self.conn.execute(
            "SELECT id, nome FROM setor WHERE ativo = 1 ORDER BY nome"
        ).fetchall()
        for linha in linhas:
            self.combo_setor.addItem(linha["nome"], linha["id"])

    def buscar_visitante(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        linha = self.conn.execute(
            "SELECT nome FROM visitante WHERE documento = ?", (cpf,)
        ).fetchone()
        if linha:
            self.campo_nome.setText(linha["nome"])
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
            self.campo_cpf.setFocus()
            return
        if not nome:
            self.mensagem.setText("Informe o nome do visitante.")
            self.campo_nome.setFocus()
            return
        if setor_id is None:
            self.mensagem.setText("Selecione o setor de destino.")
            return

        visitante = self.conn.execute(
            "SELECT id FROM visitante WHERE documento = ?", (cpf,)
        ).fetchone()
        if visitante is None:
            visitante_id = self.conn.execute(
                "INSERT INTO visitante (nome, documento) VALUES (?, ?)", (nome, cpf)
            ).lastrowid
        else:
            visitante_id = visitante["id"]

        aberta = self.conn.execute(
            "SELECT 1 FROM visita WHERE visitante_id = ? AND saida IS NULL",
            (visitante_id,),
        ).fetchone()
        if aberta:
            self.mensagem.setText(f"{nome} já está no prédio. Registre a saída antes.")
            return

        cracha = self.conn.execute(
            "SELECT id, codigo FROM cracha WHERE situacao = 'disponivel' "
            "ORDER BY codigo LIMIT 1"
        ).fetchone()
        if cracha is None:
            self.mensagem.setText("Não há crachá disponível. Aguarde uma devolução.")
            return

        self.conn.execute(
            "INSERT INTO visita (visitante_id, setor_id, cracha_id, entrada) "
            "VALUES (?, ?, ?, ?)",
            (visitante_id, setor_id, cracha["id"], agora()),
        )
        self.conn.execute(
            "UPDATE cracha SET situacao = 'em_uso' WHERE id = ?", (cracha["id"],)
        )
        self.conn.commit()

        self.limpar_campos()
        self.mensagem.setText(f"Entrada registrada. Entregue o crachá {cracha['codigo']}.")
        self.atualizar_tabela()

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
        termo = f"%{self.campo_filtro.text().strip()}%"  # o curinga vai no parâmetro
        linhas = self.conn.execute(
            """
            SELECT v.id, p.nome, p.documento, s.nome AS setor,
                   c.codigo AS cracha, v.entrada
              FROM visita v
              JOIN visitante p ON p.id = v.visitante_id
              JOIN setor s     ON s.id = v.setor_id
              JOIN cracha c    ON c.id = v.cracha_id
             WHERE v.saida IS NULL
               AND (p.nome LIKE ? OR s.nome LIKE ?)
             ORDER BY v.entrada
            """,
            (termo, termo),
        ).fetchall()

        self.tabela.setRowCount(len(linhas))
        for i, l in enumerate(linhas):
            valores = [l["id"], l["nome"], mascarar_documento(l["documento"]),
                       l["setor"], l["cracha"], l["entrada"]]
            for j, valor in enumerate(valores):
                self.tabela.setItem(i, j, QTableWidgetItem(str(valor)))
        self.tabela.setCurrentCell(-1, -1)

        total = self.conn.execute(
            "SELECT COUNT(*) FROM visita WHERE saida IS NULL"
        ).fetchone()[0]
        livres = self.conn.execute(
            "SELECT COUNT(*) FROM cracha WHERE situacao = 'disponivel'"
        ).fetchone()[0]
        self.contador.setText(f"No prédio: {total} | Crachás livres: {livres}")

    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.campo_cpf.setFocus()