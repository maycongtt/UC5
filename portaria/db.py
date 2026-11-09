import sqlite3
from pathlib import Path

ESQUEMA = Path(__file__).with_name("schema.sql")


def conectar(caminho="portaria.db"):
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row             # acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")   # vale por conexão
    return conn


def preparar_banco(conn):
    conn.executescript(ESQUEMA.read_text(encoding="utf-8"))
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO setor (nome, lotacao_maxima) VALUES (?, ?)",
            [("Secretaria", 5), ("Coordenação", 3), ("Laboratório", 10)],
        )
        conn.executemany(
            "INSERT OR IGNORE INTO cracha (codigo) VALUES (?)",
            [(f"V-{n:02d}",) for n in range(1, 11)],
        )