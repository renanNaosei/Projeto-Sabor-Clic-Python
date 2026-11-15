/* =====================================================================
   SABOR & CLIC — MODELO FÍSICO (SQLite)
   Projeto Integrador — Parte 2 (4º Bimestre)
   Escopo: 11 tabelas = 9 entidades da Parte 1 + INGREDIENTE e
   FICHA_TECNICA (controle de estoque), com restrições e índices.
   Requer SQLite 3.25+ (funções de janela nos relatórios).

   Diferenças em relação à versão SQL Server:
     - não existe CREATE DATABASE: o banco é o próprio arquivo .db;
     - INT IDENTITY(1,1)  ->  INTEGER PRIMARY KEY AUTOINCREMENT;
     - NVARCHAR(n)        ->  TEXT (o tamanho não é imposto pelo SQLite);
     - BIT                ->  INTEGER com CHECK (x IN (0,1));
     - DATETIME2          ->  TEXT no formato ISO 'AAAA-MM-DD HH:MM:SS';
     - texto é sensível a maiúsculas: e-mail e nomes únicos usam COLLATE NOCASE
       (no SQL Server a collation padrão já ignora maiúsculas);
     - as chaves estrangeiras só valem com PRAGMA foreign_keys = ON
       (a aplicação liga esse PRAGMA a cada conexão).
   ===================================================================== */

PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS Agendamento;
DROP TABLE IF EXISTS Item_Pedido;
DROP TABLE IF EXISTS Pedido;
DROP TABLE IF EXISTS Ficha_Tecnica;
DROP TABLE IF EXISTS Ingrediente;
DROP TABLE IF EXISTS Bancada;
DROP TABLE IF EXISTS Prato;
DROP TABLE IF EXISTS Cozinheiro;
DROP TABLE IF EXISTS Cliente;
DROP TABLE IF EXISTS Administrador;
DROP TABLE IF EXISTS Usuario;

PRAGMA foreign_keys = ON;

CREATE TABLE Usuario (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash      TEXT    NOT NULL,
    data_cadastro   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    tipo_usuario    TEXT    NOT NULL
        CHECK (tipo_usuario IN ('administrador', 'cliente', 'cozinheiro')),
    ativo           INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);


CREATE TABLE Administrador (
    id_usuario      INTEGER PRIMARY KEY
        REFERENCES Usuario(id_usuario),
    nivel_permissao TEXT    NOT NULL
);

CREATE TABLE Cliente (
    id_usuario        INTEGER PRIMARY KEY
        REFERENCES Usuario(id_usuario),
    endereco_entrega  TEXT NULL,
    telefone          TEXT NULL
);

CREATE TABLE Cozinheiro (
    id_usuario      INTEGER PRIMARY KEY
        REFERENCES Usuario(id_usuario),
    turno_trabalho  TEXT    NOT NULL
        CHECK (turno_trabalho IN ('Manhã', 'Tarde', 'Noite')),
    especialidade   TEXT    NULL
);

CREATE TABLE Prato (
    id_prato          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome              TEXT          NOT NULL,
    descricao         TEXT          NULL,
    preco             DECIMAL(10,2) NOT NULL CHECK (preco >= 0),
    categoria         TEXT          NULL,
    disponivel        INTEGER       NOT NULL DEFAULT 1 CHECK (disponivel IN (0, 1)),
    imagem_url        TEXT          NULL,
    id_usuario_admin  INTEGER       NOT NULL
        REFERENCES Administrador(id_usuario)
);

CREATE TABLE Bancada (
    id_bancada      INTEGER PRIMARY KEY AUTOINCREMENT,
    identificacao   TEXT          NOT NULL UNIQUE COLLATE NOCASE,
    descricao       TEXT          NULL,
    capacidade      INTEGER       NULL CHECK (capacidade > 0),
    equipamentos    TEXT          NULL,
    valor_hora      DECIMAL(10,2) NOT NULL CHECK (valor_hora >= 0),
    status          TEXT          NOT NULL DEFAULT 'Disponível'
        CHECK (status IN ('Disponível', 'Ocupada', 'Manutenção'))
);

CREATE TABLE Ingrediente (
    id_ingrediente      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT          NOT NULL UNIQUE COLLATE NOCASE,
    unidade_medida      TEXT          NOT NULL,
    quantidade_estoque  DECIMAL(10,3) NOT NULL DEFAULT 0
        CHECK (quantidade_estoque >= 0),
    estoque_minimo      DECIMAL(10,3) NOT NULL DEFAULT 0
        CHECK (estoque_minimo >= 0)
);

CREATE TABLE Ficha_Tecnica (
    id_prato             INTEGER       NOT NULL
        REFERENCES Prato(id_prato),
    id_ingrediente       INTEGER       NOT NULL
        REFERENCES Ingrediente(id_ingrediente),
    quantidade_utilizada DECIMAL(10,3) NOT NULL
        CHECK (quantidade_utilizada > 0),
    PRIMARY KEY (id_prato, id_ingrediente)
);

CREATE TABLE Pedido (
    id_pedido               INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario_cliente      INTEGER       NOT NULL
        REFERENCES Cliente(id_usuario),
    id_usuario_cozinheiro   INTEGER       NULL
        REFERENCES Cozinheiro(id_usuario),
    data_hora_pedido        TEXT          NOT NULL DEFAULT (datetime('now', 'localtime')),
    status                  TEXT          NOT NULL DEFAULT 'Aguardando'
        CHECK (status IN ('Aguardando', 'Iniciando Preparo', 'Em Preparo', 'Pronto para Entrega')),
    valor_total             DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (valor_total >= 0),
    observacoes             TEXT          NULL
);

CREATE TABLE Item_Pedido (
    id_item_pedido          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido               INTEGER       NOT NULL
        REFERENCES Pedido(id_pedido),
    id_prato                INTEGER       NOT NULL
        REFERENCES Prato(id_prato),
    quantidade              INTEGER       NOT NULL CHECK (quantidade > 0),
    preco_unitario          DECIMAL(10,2) NOT NULL CHECK (preco_unitario >= 0),
    tempo_estimado_preparo  INTEGER       NULL CHECK (tempo_estimado_preparo > 0)
);

CREATE TABLE Agendamento (
    id_agendamento      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario_cliente  INTEGER NOT NULL
        REFERENCES Cliente(id_usuario),
    id_bancada          INTEGER NOT NULL
        REFERENCES Bancada(id_bancada),
    data_hora_inicio    TEXT    NOT NULL,
    data_hora_fim       TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'Confirmado'
        CHECK (status IN ('Confirmado', 'Cancelado', 'Concluído')),
    CHECK (data_hora_fim > data_hora_inicio)
);

CREATE INDEX ix_prato_admin           ON Prato (id_usuario_admin);
CREATE INDEX ix_pedido_cliente        ON Pedido (id_usuario_cliente);
CREATE INDEX ix_pedido_cozinheiro     ON Pedido (id_usuario_cozinheiro);
CREATE INDEX ix_pedido_status_data    ON Pedido (status, data_hora_pedido);
CREATE INDEX ix_item_pedido_pedido    ON Item_Pedido (id_pedido);
CREATE INDEX ix_item_pedido_prato     ON Item_Pedido (id_prato);
CREATE INDEX ix_ficha_ingrediente     ON Ficha_Tecnica (id_ingrediente);
CREATE INDEX ix_agendamento_bancada   ON Agendamento (id_bancada, data_hora_inicio, data_hora_fim);
CREATE INDEX ix_agendamento_cliente   ON Agendamento (id_usuario_cliente);
