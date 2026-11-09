from sqlalchemy import select
from sqlalchemy.orm import Session

from portaria.orm import Setor, Visitante, criar_engine

engine = criar_engine(echo=True)

with Session(engine) as sessao:
    for v in sessao.scalars(select(Visitante).order_by(Visitante.nome)):
        print(v.nome, "tem", len(v.visitas), "visita(s)")

    sessao.add(Setor(nome="Almoxarifado", lotacao_maxima=2, ativo=1))
    sessao.commit()
    print("Setor criado.")