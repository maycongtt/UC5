"""Regras de negócio da portaria.

A interface chama estas funções; elas validam, controlam a transação e
lançam RegraNegocioError com mensagens prontas para o usuário.
"""

from datetime import datetime

from portaria import repositorio as repo
from portaria.erros import RegraNegocioError
from portaria.validacao import cpf_valido, normalizar_documento, normalizar_nome


def agora() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def cadastrar_visitante(conn, nome: str, documento: str) -> int:
    nome = normalizar_nome(nome)
    doc = normalizar_documento(documento)
    if not nome:
        raise RegraNegocioError("Informe o nome do visitante.")
    if not cpf_valido(doc):
        raise RegraNegocioError("CPF inválido. Confira os 11 dígitos.")
    if repo.buscar_visitante_por_documento(conn, doc):
        raise RegraNegocioError("Já existe um visitante com este CPF.")
    with conn:  # commit no sucesso, rollback em exceção
        return repo.inserir_visitante(conn, nome, doc)


def registrar_entrada(conn, documento: str, setor_id: int, motivo: str = "",
                      momento: str | None = None, nome: str | None = None) -> int:
    """Registra visitante novo (se necessário), visita e crachá numa única transação."""
    doc = normalizar_documento(documento)
    if not cpf_valido(doc):
        raise RegraNegocioError("CPF inválido. Confira os 11 dígitos.")

    setor = repo.obter_setor(conn, setor_id)
    if setor is None or not setor["ativo"]:
        raise RegraNegocioError("Selecione um setor de destino válido.")

    # Projeto local com um operador e uma conexão; vários operadores exigiriam
    # estratégia própria de concorrência e bloqueio de escrita (BEGIN IMMEDIATE).
    with conn:
        visitante = repo.buscar_visitante_por_documento(conn, doc)
        if visitante is None:
            nome_normalizado = normalizar_nome(nome)
            if not nome_normalizado:
                raise RegraNegocioError("Informe o nome do visitante.")
            visitante_id = repo.inserir_visitante(conn, nome_normalizado, doc)
            nome_visitante = nome_normalizado
        else:
            visitante_id = visitante["id"]
            nome_visitante = visitante["nome"]

        if repo.visita_aberta_do_visitante(conn, visitante_id):
            raise RegraNegocioError(
                f"{nome_visitante} já está no prédio. Registre a saída antes."
            )
        if repo.contar_presentes_no_setor(conn, setor_id) >= setor["lotacao_maxima"]:
            raise RegraNegocioError(
                f"{setor['nome']} atingiu a lotação de {setor['lotacao_maxima']} visitantes."
            )
        cracha = repo.buscar_cracha_disponivel(conn)
        if cracha is None:
            raise RegraNegocioError("Não há crachá disponível. Aguarde uma devolução.")

        visita_id = repo.inserir_visita(
            conn, visitante_id, setor_id, cracha["id"],
            normalizar_nome(motivo) or None, momento or agora(),
        )
        repo.atualizar_situacao_cracha(conn, cracha["id"], "em_uso")
    return visita_id

def registrar_saida(conn, visita_id: int, momento: str | None = None) -> None:
    """Check-out: encerra a visita E devolve o crachá na mesma transação."""
    momento = momento or agora()
    with conn:
        visita = repo.obter_visita(conn, visita_id)
        if visita is None:
            raise RegraNegocioError("Visita não encontrada.")
        if visita["saida"] is not None:
            raise RegraNegocioError("Esta visita já foi encerrada.")
        if momento < visita["entrada"]:
            raise RegraNegocioError("A saída não pode ser anterior à entrada.")

        repo.encerrar_visita(conn, visita_id, momento)
        repo.atualizar_situacao_cracha(conn, visita["cracha_id"], "disponivel")