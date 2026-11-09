-- Portaria Digital: esquema SQLite.
-- As regras críticas existem também no banco (defesa em profundidade):
-- a aplicação valida antes, o banco recusa se algo escapar.

CREATE TABLE IF NOT EXISTS setor (
    id              INTEGER PRIMARY KEY,
    nome            TEXT    NOT NULL UNIQUE,
    lotacao_maxima  INTEGER NOT NULL CHECK (lotacao_maxima > 0),
    ativo           INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS visitante (
    id          INTEGER PRIMARY KEY,
    nome        TEXT NOT NULL CHECK (length(trim(nome)) > 0),
    documento   TEXT NOT NULL UNIQUE,          -- somente dígitos
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS cracha (
    id        INTEGER PRIMARY KEY,
    codigo    TEXT NOT NULL UNIQUE,
    situacao  TEXT NOT NULL DEFAULT 'disponivel'
              CHECK (situacao IN ('disponivel', 'em_uso', 'extraviado'))
);

CREATE TABLE IF NOT EXISTS visita (
    id            INTEGER PRIMARY KEY,
    visitante_id  INTEGER NOT NULL REFERENCES visitante (id) ON DELETE RESTRICT,
    setor_id      INTEGER NOT NULL REFERENCES setor (id)     ON DELETE RESTRICT,
    cracha_id     INTEGER NOT NULL REFERENCES cracha (id)    ON DELETE RESTRICT,
    motivo        TEXT,
    entrada       TEXT NOT NULL,                -- 'AAAA-MM-DD HH:MM:SS'
    saida         TEXT,                         -- NULL = visitante no prédio
    CHECK (saida IS NULL OR saida >= entrada)
);

-- RN02: um visitante só pode ter uma visita aberta.
CREATE UNIQUE INDEX IF NOT EXISTS ux_visita_aberta_visitante
    ON visita (visitante_id) WHERE saida IS NULL;

-- RN03: um crachá só pode estar em uma visita aberta.
CREATE UNIQUE INDEX IF NOT EXISTS ux_visita_aberta_cracha
    ON visita (cracha_id) WHERE saida IS NULL;

CREATE INDEX IF NOT EXISTS ix_visita_entrada ON visita (entrada);
