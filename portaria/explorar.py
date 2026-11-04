"""Laboratório de SQL: rode, leia a saída e responda às perguntas."""

import sqlite3
from pathlib import Path

conn = sqlite3.connect(":memory:")  # banco descartável, só na memória
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(Path("portaria/schema.sql").read_text(encoding="utf-8"))

conn.execute("INSERT INTO setor (nome, lotacao_maxima) VALUES (?, ?)", ("Secretaria", 5))
conn.execute("INSERT INTO cracha (codigo) VALUES (?)", ("V-01",))
conn.execute("INSERT INTO visitante (nome, documento) VALUES (?, ?)", ("Ana Lima", "52998224725"))
conn.execute("INSERT INTO visitante (nome, documento) VALUES (?, ?)", ("Bruno Sousa", "11144477735"))

# 1. CREATE: abrir uma visita
conn.execute(
    "INSERT INTO visita (visitante_id, setor_id, cracha_id, entrada) VALUES (?, ?, ?, ?)",
    (1, 1, 1, "2026-10-21 09:00:00"),
)

# 2. READ: quem está no prédio
for linha in conn.execute("SELECT visitante_id, entrada FROM visita WHERE saida IS NULL"):
    print("presente:", dict(linha))

# 3. UPDATE: encerrar a visita
conn.execute("UPDATE visita SET saida = ? WHERE id = ?", ("2026-10-21 09:40:00", 1))
print("presentes depois do UPDATE:",
      conn.execute("SELECT COUNT(*) FROM visita WHERE saida IS NULL").fetchone()[0])

# 4. DELETE: tentar apagar um visitante que tem histórico
try:
    conn.execute("DELETE FROM visitante WHERE id = ?", (1,))
except sqlite3.IntegrityError as erro:
    print("DELETE recusado:", erro)

# 5. Por que placeholders? Compare as duas buscas com a mesma entrada maliciosa.
entrada = "' OR '1'='1"
inseguro = conn.execute(
    f"SELECT nome FROM visitante WHERE documento = '{entrada}'"
).fetchall()
seguro = conn.execute(
    "SELECT nome FROM visitante WHERE documento = ?", (entrada,)
).fetchall()
print("concatenando:   ", [l["nome"] for l in inseguro])
print("com placeholder:", [l["nome"] for l in seguro])