
DROP TRIGGER IF EXISTS trg_item_pedido_baixa_estoque_ins;
DROP TRIGGER IF EXISTS trg_item_pedido_baixa_estoque_upd;
DROP TRIGGER IF EXISTS trg_item_pedido_baixa_estoque_del;
DROP TRIGGER IF EXISTS trg_item_pedido_total_ins;
DROP TRIGGER IF EXISTS trg_item_pedido_total_upd;
DROP TRIGGER IF EXISTS trg_item_pedido_total_del;
DROP TRIGGER IF EXISTS trg_agendamento_conflito_ins;
DROP TRIGGER IF EXISTS trg_agendamento_conflito_upd;

/* =====================================================================
   1. BAIXA AUTOMÁTICA DE ESTOQUE
      Consumo = quantidade do item x quantidade_utilizada da ficha técnica.
        - INSERT: debita o consumo da linha nova;
        - DELETE: devolve (estorna) o consumo da linha removida;
        - UPDATE: devolve o consumo antigo e debita o novo.
   ===================================================================== */
CREATE TRIGGER trg_item_pedido_baixa_estoque_ins
AFTER INSERT ON Item_Pedido
BEGIN
    SELECT RAISE(ABORT, 'Estoque insuficiente de ingrediente para este pedido.')
    WHERE EXISTS (
        SELECT 1
        FROM Ficha_Tecnica AS ft
        JOIN Ingrediente   AS i ON i.id_ingrediente = ft.id_ingrediente
        WHERE ft.id_prato = NEW.id_prato
          AND ROUND(i.quantidade_estoque - NEW.quantidade * ft.quantidade_utilizada, 3) < 0
    );

    UPDATE Ingrediente
    SET quantidade_estoque = ROUND(quantidade_estoque - NEW.quantidade * (
            SELECT ft.quantidade_utilizada
            FROM Ficha_Tecnica AS ft
            WHERE ft.id_prato = NEW.id_prato
              AND ft.id_ingrediente = Ingrediente.id_ingrediente), 3)
    WHERE id_ingrediente IN (SELECT id_ingrediente FROM Ficha_Tecnica WHERE id_prato = NEW.id_prato);
END;

CREATE TRIGGER trg_item_pedido_baixa_estoque_del
AFTER DELETE ON Item_Pedido
BEGIN
    UPDATE Ingrediente
    SET quantidade_estoque = ROUND(quantidade_estoque + OLD.quantidade * (
            SELECT ft.quantidade_utilizada
            FROM Ficha_Tecnica AS ft
            WHERE ft.id_prato = OLD.id_prato
              AND ft.id_ingrediente = Ingrediente.id_ingrediente), 3)
    WHERE id_ingrediente IN (SELECT id_ingrediente FROM Ficha_Tecnica WHERE id_prato = OLD.id_prato);
END;

CREATE TRIGGER trg_item_pedido_baixa_estoque_upd
AFTER UPDATE OF quantidade, id_prato ON Item_Pedido
BEGIN
    UPDATE Ingrediente
    SET quantidade_estoque = ROUND(quantidade_estoque + OLD.quantidade * (
            SELECT ft.quantidade_utilizada
            FROM Ficha_Tecnica AS ft
            WHERE ft.id_prato = OLD.id_prato
              AND ft.id_ingrediente = Ingrediente.id_ingrediente), 3)
    WHERE id_ingrediente IN (SELECT id_ingrediente FROM Ficha_Tecnica WHERE id_prato = OLD.id_prato);

    SELECT RAISE(ABORT, 'Estoque insuficiente de ingrediente para este pedido.')
    WHERE EXISTS (
        SELECT 1
        FROM Ficha_Tecnica AS ft
        JOIN Ingrediente   AS i ON i.id_ingrediente = ft.id_ingrediente
        WHERE ft.id_prato = NEW.id_prato
          AND ROUND(i.quantidade_estoque - NEW.quantidade * ft.quantidade_utilizada, 3) < 0
    );

    UPDATE Ingrediente
    SET quantidade_estoque = ROUND(quantidade_estoque - NEW.quantidade * (
            SELECT ft.quantidade_utilizada
            FROM Ficha_Tecnica AS ft
            WHERE ft.id_prato = NEW.id_prato
              AND ft.id_ingrediente = Ingrediente.id_ingrediente), 3)
    WHERE id_ingrediente IN (SELECT id_ingrediente FROM Ficha_Tecnica WHERE id_prato = NEW.id_prato);
END;

/* =====================================================================
   2. VALOR TOTAL DO PEDIDO
      Mantém Pedido.valor_total = soma de (quantidade x preco_unitario)
      dos itens. O total é calculado pelo banco, e não pelo front-end.
   ===================================================================== */
CREATE TRIGGER trg_item_pedido_total_ins
AFTER INSERT ON Item_Pedido
BEGIN
    UPDATE Pedido
    SET valor_total = ROUND(COALESCE((
            SELECT SUM(quantidade * preco_unitario) FROM Item_Pedido WHERE id_pedido = NEW.id_pedido), 0), 2)
    WHERE id_pedido = NEW.id_pedido;
END;

CREATE TRIGGER trg_item_pedido_total_upd
AFTER UPDATE ON Item_Pedido
BEGIN
    UPDATE Pedido
    SET valor_total = ROUND(COALESCE((
            SELECT SUM(quantidade * preco_unitario) FROM Item_Pedido WHERE id_pedido = Pedido.id_pedido), 0), 2)
    WHERE id_pedido IN (NEW.id_pedido, OLD.id_pedido);
END;

CREATE TRIGGER trg_item_pedido_total_del
AFTER DELETE ON Item_Pedido
BEGIN
    UPDATE Pedido
    SET valor_total = ROUND(COALESCE((
            SELECT SUM(quantidade * preco_unitario) FROM Item_Pedido WHERE id_pedido = OLD.id_pedido), 0), 2)
    WHERE id_pedido = OLD.id_pedido;
END;

/* =====================================================================
   3. CONFLITO DE HORÁRIO NA LOCAÇÃO DE BANCADAS
      Dois agendamentos confirmados da mesma bancada não podem se
      sobrepor. Reservas encostadas (uma termina às 12:00 e outra começa
      às 12:00) são permitidas. Aqui o trigger é BEFORE (barra antes de gravar);
      no SQL Server é AFTER e precisou de ROLLBACK + THROW.
   ===================================================================== */
CREATE TRIGGER trg_agendamento_conflito_ins
BEFORE INSERT ON Agendamento
WHEN NEW.status = 'Confirmado'
BEGIN
    SELECT RAISE(ABORT, 'Conflito de horário: a bancada já está reservada neste período.')
    WHERE EXISTS (
        SELECT 1
        FROM Agendamento AS existente
        WHERE existente.id_bancada       = NEW.id_bancada
          AND existente.status           = 'Confirmado'
          AND existente.data_hora_inicio < NEW.data_hora_fim
          AND existente.data_hora_fim    > NEW.data_hora_inicio
    );
END;

CREATE TRIGGER trg_agendamento_conflito_upd
BEFORE UPDATE OF id_bancada, data_hora_inicio, data_hora_fim, status ON Agendamento
WHEN NEW.status = 'Confirmado'
BEGIN
    SELECT RAISE(ABORT, 'Conflito de horário: a bancada já está reservada neste período.')
    WHERE EXISTS (
        SELECT 1
        FROM Agendamento AS existente
        WHERE existente.id_bancada       = NEW.id_bancada
          AND existente.id_agendamento  <> NEW.id_agendamento
          AND existente.status           = 'Confirmado'
          AND existente.data_hora_inicio < NEW.data_hora_fim
          AND existente.data_hora_fim    > NEW.data_hora_inicio
    );
END;
