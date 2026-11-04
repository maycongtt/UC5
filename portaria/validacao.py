"""Funções puras de validação: não dependem da interface nem do banco."""

import re

def normalizar_nome(nome: str | None) -> str:
    """Remove espaços nas pontas e espaços repetidos no meio."""
    return " ".join((nome or "").split())

def normalizar_documento(valor: str | None) -> str:
    """Mantém apenas dígitos: '123.456.789-09' -> '12345678909'."""
    return re.sub(r"\D", "", valor or "")

def cpf_valido(valor: str | None) -> bool:
    """Valida os dígitos verificadores do CPF.

    Use apenas CPFs fictícios gerados para teste. Um CPF válido
    matematicamente pode pertencer a uma pessoa real.
    """
    d = normalizar_documento(valor)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(d[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11 % 10
        if digito != int(d[posicao]):
            return False
    return True

def mascarar_documento(valor: str | None) -> str:
    """Exibe só o miolo do CPF (***.456.789-**), reduzindo exposição na tela."""
    d = normalizar_documento(valor)
    if len(d) != 11:
        return "***"
    return f"***.{d[3:6]}.{d[6:9]}-**"