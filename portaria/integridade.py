"""O que a chave estrangeira protege? Trabalha numa CÓPIA do banco."""

import sqlite3
from pathlib import Path

# Backup consistente, inclusive se o banco original estiver aberto.
# Execute em ambiente de teste, com pelo menos duas visitas em andamento.
Path("copia_integridade.db").unlink(missing_ok=True)
origem = sqlite3.connect("portaria.db")
destino = sqlite3.connect("copia_integridade.db")
try:
    origem.backup(destino)
finally:
    destino.close()
    origem.close()

for ligada in (True, False):
    conn = sqlite3.connect("copia_integridade.db")
    conn.execute(f"PRAGMA foreign_keys = {'ON' if ligada else 'OFF'}")
    visitante_id = conn.execute(
        "SELECT visitante_id FROM visita WHERE saida IS NULL LIMIT 1"
    ).fetchone()[0]
    try:
        with conn:
            conn.execute("DELETE FROM visitante WHERE id = ?", (visitante_id,))
        print(f"foreign_keys {'ON ' if ligada else 'OFF'}: DELETE aceito")
    except sqlite3.IntegrityError as erro:
        print(f"foreign_keys {'ON ' if ligada else 'OFF'}: DELETE recusado ({erro})")

    abertas = conn.execute("SELECT COUNT(*) FROM visita WHERE saida IS NULL").fetchone()[0]
    na_lista = conn.execute(
        "SELECT COUNT(*) FROM visita v JOIN visitante p ON p.id = v.visitante_id "
        "WHERE v.saida IS NULL"
    ).fetchone()[0]
    em_uso = conn.execute("SELECT COUNT(*) FROM cracha WHERE situacao = 'em_uso'").fetchone()[0]
    print(f"   visitas abertas: {abertas} | aparecem na lista de presentes: {na_lista} "
          f"| crachás em uso: {em_uso}")
    conn.close()