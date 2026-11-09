"""Mapeamento ORM das tabelas da Portaria Digital, para comparação com o SQL explícito.

Não substitui repositorio.py: é um módulo isolado de estudo.
"""

from sqlalchemy import ForeignKey, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload


class Base(DeclarativeBase):
    pass


class Setor(Base):
    __tablename__ = "setor"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    lotacao_maxima: Mapped[int]
    ativo: Mapped[int]


class Visitante(Base):
    __tablename__ = "visitante"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    documento: Mapped[str]
    visitas: Mapped[list["Visita"]] = relationship(back_populates="visitante")


class Cracha(Base):
    __tablename__ = "cracha"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str]
    situacao: Mapped[str]


class Visita(Base):
    __tablename__ = "visita"
    id: Mapped[int] = mapped_column(primary_key=True)
    visitante_id: Mapped[int] = mapped_column(ForeignKey("visitante.id"))
    setor_id: Mapped[int] = mapped_column(ForeignKey("setor.id"))
    cracha_id: Mapped[int] = mapped_column(ForeignKey("cracha.id"))
    motivo: Mapped[str | None]
    entrada: Mapped[str]
    saida: Mapped[str | None]

    visitante: Mapped[Visitante] = relationship(back_populates="visitas")
    setor: Mapped[Setor] = relationship()
    cracha: Mapped[Cracha] = relationship()


def criar_engine(caminho: str = "portaria.db", echo: bool = False):
    return create_engine(f"sqlite:///{caminho}", echo=echo)


def listar_presentes_orm(engine) -> list[tuple[int, str, str, str]]:
    with Session(engine) as sessao:
        consulta = (
            select(Visita)
            .where(Visita.saida.is_(None))
            .options(
                selectinload(Visita.visitante),
                selectinload(Visita.setor),
                selectinload(Visita.cracha),
            )
            .order_by(Visita.entrada)
        )
        return [
            (v.id, v.visitante.nome, v.setor.nome, v.cracha.codigo)
            for v in sessao.scalars(consulta)
        ]