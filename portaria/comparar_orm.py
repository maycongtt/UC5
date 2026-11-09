from portaria.db import conectar
from portaria.orm import criar_engine, listar_presentes_orm

conn = conectar()
via_sql = [
    tuple(l) for l in conn.execute(
        """
        SELECT v.id, p.nome, s.nome, c.codigo
          FROM visita v
          JOIN visitante p ON p.id = v.visitante_id
          JOIN setor s     ON s.id = v.setor_id
          JOIN cracha c    ON c.id = v.cracha_id
         WHERE v.saida IS NULL
         ORDER BY v.entrada
        """
    )
]
print("SQL explícito:", via_sql)

print("--- ORM: conte os SELECT que aparecem abaixo ---")
via_orm = listar_presentes_orm(criar_engine(echo=True))
print("ORM:", via_orm)
print("Resultados iguais?", via_sql == via_orm)