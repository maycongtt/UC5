"""Persistência com SQL explícito e parametrizado.

Regra da casa: nenhum valor vindo da interface é concatenado em SQL.
Estas funções NÃO fazem commit; quem controla a transação é o serviço.
"""

import sqlite3

Linha = sqlite3.Row

# ---------- visitante ----------

def inserir_visitante(conn, nome: str, documento: str) -> int:
    cur = conn.execute(
        "INSERT INTO visitante (nome, documento) VALUES (?, ?)", (nome, documento)
    )
    return cur.lastrowid

def buscar_visitante_por_documento(conn, documento: str) -> Linha | None:
    return conn.execute(
        "SELECT id, nome, documento FROM visitante WHERE documento = ?", (documento,)
    ).fetchone()

# ---------- setor ----------

def listar_setores_ativos(conn) -> list[Linha]:
    return conn.execute(
        "SELECT id, nome, lotacao_maxima FROM setor WHERE ativo = 1 ORDER BY nome"
    ).fetchall()

def obter_setor(conn, setor_id: int) -> Linha | None:
    return conn.execute(
        "SELECT id, nome, lotacao_maxima, ativo FROM setor WHERE id = ?", (setor_id,)
    ).fetchone()

def contar_presentes_no_setor(conn, setor_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM visita WHERE setor_id = ? AND saida IS NULL", (setor_id,)
    ).fetchone()[0]

# ---------- crachá ----------

def buscar_cracha_disponivel(conn) -> Linha | None:
    return conn.execute(
        "SELECT id, codigo FROM cracha WHERE situacao = 'disponivel' "
        "ORDER BY codigo LIMIT 1"
    ).fetchone()

def atualizar_situacao_cracha(conn, cracha_id: int, situacao: str) -> None:
    conn.execute("UPDATE cracha SET situacao = ? WHERE id = ?", (situacao, cracha_id))

def contar_crachas_por_situacao(conn) -> dict[str, int]:
    linhas = conn.execute(
        "SELECT situacao, COUNT(*) AS total FROM cracha GROUP BY situacao"
    ).fetchall()
    return {l["situacao"]: l["total"] for l in linhas}

# ---------- visita ----------

def visita_aberta_do_visitante(conn, visitante_id: int) -> Linha | None:
    return conn.execute(
        "SELECT id FROM visita WHERE visitante_id = ? AND saida IS NULL",
        (visitante_id,),
    ).fetchone()

def inserir_visita(conn, visitante_id, setor_id, cracha_id, motivo, entrada) -> int:
    cur = conn.execute(
        "INSERT INTO visita (visitante_id, setor_id, cracha_id, motivo, entrada) "
        "VALUES (?, ?, ?, ?, ?)",
        (visitante_id, setor_id, cracha_id, motivo, entrada),
    )
    return cur.lastrowid

def obter_visita(conn, visita_id: int) -> Linha | None:
    return conn.execute(
        """
        SELECT v.id, v.visitante_id, v.cracha_id, c.codigo AS cracha,
               v.entrada, v.saida
          FROM visita v
          JOIN cracha c ON c.id = v.cracha_id
         WHERE v.id = ?
        """,
        (visita_id,),
    ).fetchone()

def encerrar_visita(conn, visita_id: int, saida: str) -> None:
    conn.execute("UPDATE visita SET saida = ? WHERE id = ?", (saida, visita_id))

def listar_presentes(conn) -> list[Linha]:
    """Quem está no prédio agora. É a lista usada numa evacuação."""
    return conn.execute(
        """
        SELECT v.id, p.nome, p.documento, s.nome AS setor, c.codigo AS cracha,
               v.entrada
          FROM visita v
          JOIN visitante p ON p.id = v.visitante_id
          JOIN setor s     ON s.id = v.setor_id
          JOIN cracha c    ON c.id = v.cracha_id
         WHERE v.saida IS NULL
         ORDER BY v.entrada
        """
    ).fetchall()

def listar_historico(conn, inicio: str, fim: str, termo: str = "") -> list[Linha]:
    """Visitas com entrada no intervalo [inicio, fim], filtrando por nome ou setor."""
    padrao = f"%{termo.strip()}%"  # o curinga vai no PARÂMETRO, não no SQL
    return conn.execute(
        """
        SELECT v.id, p.nome, p.documento, s.nome AS setor, c.codigo AS cracha,
               v.entrada, v.saida,
               CAST(ROUND((julianday(v.saida) - julianday(v.entrada)) * 1440) AS INTEGER)
                   AS minutos
          FROM visita v
          JOIN visitante p ON p.id = v.visitante_id
          JOIN setor s     ON s.id = v.setor_id
          JOIN cracha c    ON c.id = v.cracha_id
         WHERE date(v.entrada) BETWEEN ? AND ?
           AND (p.nome LIKE ? OR s.nome LIKE ?)
         ORDER BY v.entrada DESC
        """,
        (inicio, fim, padrao, padrao),
    ).fetchall()

def resumo_por_setor(conn, inicio: str, fim: str) -> list[Linha]:
    return conn.execute(
        """
        SELECT s.nome AS setor, COUNT(v.id) AS visitas,
               ROUND(AVG((julianday(v.saida) - julianday(v.entrada)) * 1440), 1)
                   AS media_minutos
          FROM setor s
          LEFT JOIN visita v
                 ON v.setor_id = s.id AND date(v.entrada) BETWEEN ? AND ?
         GROUP BY s.id
         ORDER BY visitas DESC, s.nome
        """,
        (inicio, fim),
    ).fetchall()