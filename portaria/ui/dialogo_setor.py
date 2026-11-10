from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class DialogoSetor(QDialog):
    """Janela modal para cadastrar ou editar um setor.

    O diálogo só coleta dados. Quem valida e grava é o serviço.
    """

    def __init__(self, parent=None, setor=None):
        super().__init__(parent)
        self.setWindowTitle("Editar setor" if setor else "Novo setor")
        self.setModal(True)

        self.campo_nome = QLineEdit()
        self.campo_lotacao = QSpinBox()
        self.campo_lotacao.setRange(1, 500)
        self.campo_lotacao.setValue(5)
        self.check_ativo = QCheckBox("Setor ativo (aparece na entrada)")
        self.check_ativo.setChecked(True)

        if setor is not None:
            self.campo_nome.setText(setor["nome"])
            self.campo_lotacao.setValue(setor["lotacao_maxima"])
            self.check_ativo.setChecked(bool(setor["ativo"]))
        else:
            self.check_ativo.setEnabled(False)  # setor novo nasce ativo

        formulario = QFormLayout()
        formulario.addRow("&Nome:", self.campo_nome)
        formulario.addRow("&Lotação máxima:", self.campo_lotacao)
        formulario.addRow("", self.check_ativo)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(formulario)
        layout.addWidget(botoes)
        self.setLayout(layout)

    def dados(self):
        return {
            "nome": self.campo_nome.text(),
            "lotacao_maxima": self.campo_lotacao.value(),
            "ativo": self.check_ativo.isChecked(),
        }