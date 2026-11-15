/* =====================================================================
   SABOR & CLIC — QUERIES DE RELATÓRIOS (SQLite)
   Consultas analíticas: vendas, estoque e ocupação.
   ===================================================================== */

/* =====================================================================
   A. VENDAS
   ===================================================================== */

/* ---- A1. Faturamento, volume e ticket médio por dia ---- */
SELECT date(p.data_hora_pedido)        AS dia,
       COUNT(*)                        AS qtd_pedidos,
       ROUND(SUM(p.valor_total), 2)    AS faturamento,
       ROUND(AVG(p.valor_total), 2)    AS ticket_medio
FROM Pedido AS p
GROUP BY date(p.data_hora_pedido)
ORDER BY dia DESC;

/* ---- A2. Pratos mais vendidos (unidades e receita) ---- */
SELECT pr.id_prato,
       pr.nome,
       pr.categoria,
       SUM(ip.quantidade)                       AS unidades_vendidas,
       ROUND(SUM(ip.quantidade * ip.preco_unitario), 2) AS receita
FROM Item_Pedido AS ip
JOIN Prato AS pr ON pr.id_prato = ip.id_prato
GROUP BY pr.id_prato, pr.nome, pr.categoria
ORDER BY unidades_vendidas DESC, receita DESC
LIMIT 10;

/* ---- A3. Receita por categoria e participação no total ---- */
SELECT COALESCE(pr.categoria, 'Sem categoria')               AS categoria,
       ROUND(SUM(ip.quantidade * ip.preco_unitario), 2)      AS receita,
       ROUND(100.0 * SUM(ip.quantidade * ip.preco_unitario)
             / SUM(SUM(ip.quantidade * ip.preco_unitario)) OVER (), 2) AS percentual
FROM Item_Pedido AS ip
JOIN Prato AS pr ON pr.id_prato = ip.id_prato
GROUP BY COALESCE(pr.categoria, 'Sem categoria')
ORDER BY receita DESC;

/* ---- A4. Pedidos por status, com o pedido mais antigo de cada fila ---- */
SELECT p.status,
       COUNT(*)                  AS qtd_pedidos,
       MIN(p.data_hora_pedido)   AS pedido_mais_antigo
FROM Pedido AS p
GROUP BY p.status
ORDER BY CASE p.status
             WHEN 'Aguardando'          THEN 1
             WHEN 'Iniciando Preparo'   THEN 2
             WHEN 'Em Preparo'          THEN 3
             WHEN 'Pronto para Entrega' THEN 4
         END;

/* ---- A5. Fila da cozinha (KDS): pedidos ainda não finalizados ---- */
SELECT p.id_pedido,
       p.status,
       p.data_hora_pedido,
       CAST((julianday('now', 'localtime') - julianday(p.data_hora_pedido)) * 1440 AS INTEGER) AS minutos_na_fila,
       uc.nome                                                         AS cliente,
       COALESCE(uz.nome, '(sem cozinheiro)')                           AS cozinheiro,
       group_concat(ip.quantidade || 'x ' || pr.nome, ', ')            AS itens,
       SUM(ip.quantidade * COALESCE(ip.tempo_estimado_preparo, 0))     AS minutos_estimados_preparo
FROM Pedido AS p
JOIN Usuario AS uc          ON uc.id_usuario = p.id_usuario_cliente
LEFT JOIN Usuario AS uz     ON uz.id_usuario = p.id_usuario_cozinheiro
JOIN Item_Pedido AS ip      ON ip.id_pedido  = p.id_pedido
JOIN Prato AS pr            ON pr.id_prato   = ip.id_prato
WHERE p.status <> 'Pronto para Entrega'
GROUP BY p.id_pedido, p.status, p.data_hora_pedido, uc.nome, uz.nome
ORDER BY p.data_hora_pedido;

/* ---- A6. Desempenho por cozinheiro (inclui quem ainda não pegou pedido) ---- */
SELECT u.nome                                  AS cozinheiro,
       c.turno_trabalho,
       COUNT(DISTINCT p.id_pedido)             AS pedidos_atribuidos,
       COALESCE(SUM(ip.quantidade), 0)         AS itens_a_preparar
FROM Cozinheiro AS c
JOIN Usuario AS u              ON u.id_usuario = c.id_usuario
LEFT JOIN Pedido AS p          ON p.id_usuario_cozinheiro = c.id_usuario
LEFT JOIN Item_Pedido AS ip    ON ip.id_pedido = p.id_pedido
GROUP BY u.nome, c.turno_trabalho
ORDER BY pedidos_atribuidos DESC;

/* ---- A7. Clientes recorrentes (2 ou mais pedidos) ---- */
SELECT u.nome                                    AS cliente,
       COUNT(*)                                  AS qtd_pedidos,
       ROUND(SUM(p.valor_total), 2)              AS total_gasto,
       ROUND(AVG(p.valor_total), 2)              AS ticket_medio,
       MAX(p.data_hora_pedido)                   AS ultimo_pedido
FROM Pedido AS p
JOIN Usuario AS u ON u.id_usuario = p.id_usuario_cliente
GROUP BY u.nome
HAVING COUNT(*) >= 2
ORDER BY total_gasto DESC;

/* =====================================================================
   B. ESTOQUE
   ===================================================================== */

/* ---- B1. Ingredientes abaixo do estoque mínimo (lista de reposição) ---- */
SELECT i.id_ingrediente,
       i.nome,
       i.unidade_medida,
       i.quantidade_estoque,
       i.estoque_minimo,
       ROUND(i.estoque_minimo - i.quantidade_estoque, 3) AS falta_para_o_minimo
FROM Ingrediente AS i
WHERE i.quantidade_estoque < i.estoque_minimo
ORDER BY falta_para_o_minimo DESC;

/* ---- B2. Posição geral do estoque com classificação de risco ---- */
SELECT i.nome,
       i.unidade_medida,
       i.quantidade_estoque,
       i.estoque_minimo,
       CASE
           WHEN i.quantidade_estoque < i.estoque_minimo       THEN 'Crítico'
           WHEN i.quantidade_estoque < i.estoque_minimo * 1.5 THEN 'Atenção'
           ELSE 'Normal'
       END AS situacao
FROM Ingrediente AS i
ORDER BY i.quantidade_estoque / NULLIF(i.estoque_minimo, 0);

/* ---- B3. Consumo teórico de ingredientes pelos pedidos (via ficha técnica) ---- */
SELECT ing.nome,
       ing.unidade_medida,
       ROUND(SUM(ip.quantidade * ft.quantidade_utilizada), 3) AS total_consumido
FROM Item_Pedido AS ip
JOIN Ficha_Tecnica AS ft  ON ft.id_prato = ip.id_prato
JOIN Ingrediente AS ing   ON ing.id_ingrediente = ft.id_ingrediente
GROUP BY ing.nome, ing.unidade_medida
ORDER BY total_consumido DESC;

/* ---- B4. Quantas porções de cada prato o estoque atual permite produzir,
        e qual ingrediente limita (o que acaba primeiro).
        CROSS APPLY + TOP 1 vira ROW_NUMBER() por prato. ---- */
WITH calculo AS (
    SELECT ft.id_prato,
           ing.nome AS ingrediente,
           CAST(ing.quantidade_estoque / ft.quantidade_utilizada AS INTEGER) AS porcoes,
           ROW_NUMBER() OVER (
               PARTITION BY ft.id_prato
               ORDER BY ing.quantidade_estoque / ft.quantidade_utilizada
           ) AS posicao
    FROM Ficha_Tecnica AS ft
    JOIN Ingrediente AS ing ON ing.id_ingrediente = ft.id_ingrediente
)
SELECT pr.nome             AS prato,
       c.ingrediente       AS ingrediente_limitante,
       c.porcoes           AS porcoes_possiveis
FROM Prato AS pr
JOIN calculo AS c ON c.id_prato = pr.id_prato AND c.posicao = 1
ORDER BY porcoes_possiveis;

/* =====================================================================
   C. OCUPAÇÃO DAS BANCADAS
      Ajuste o período e as horas de funcionamento por dia na CTE "parametros".
   ===================================================================== */

/* ---- C1. Taxa de ocupação e receita de locação por bancada no período
        (bancadas sem reserva aparecem com zero) ---- */
WITH parametros AS (
    SELECT '2026-11-01 00:00:00' AS inicio_periodo,
           '2026-12-01 00:00:00' AS fim_periodo,
           12.0                  AS horas_funcionamento_dia
),
resumo AS (
    SELECT b.id_bancada,
           b.identificacao,
           b.status                                   AS status_bancada,
           b.valor_hora,
           COUNT(a.id_agendamento)                    AS qtd_agendamentos,
           COALESCE(SUM((julianday(a.data_hora_fim) - julianday(a.data_hora_inicio)) * 24), 0) AS horas_reservadas
    FROM Bancada AS b
    CROSS JOIN parametros AS pa
    LEFT JOIN Agendamento AS a
           ON a.id_bancada = b.id_bancada
          AND a.status IN ('Confirmado', 'Concluído')
          AND a.data_hora_inicio >= pa.inicio_periodo
          AND a.data_hora_inicio <  pa.fim_periodo
    GROUP BY b.id_bancada, b.identificacao, b.status, b.valor_hora
)
SELECT r.identificacao,
       r.status_bancada,
       r.qtd_agendamentos,
       ROUND(r.horas_reservadas, 2)                                           AS horas_reservadas,
       ROUND(100.0 * r.horas_reservadas
             / ((julianday(pa.fim_periodo) - julianday(pa.inicio_periodo)) * pa.horas_funcionamento_dia), 2)
                                                                              AS taxa_ocupacao_pct,
       ROUND(r.horas_reservadas * r.valor_hora, 2)                            AS receita_locacao
FROM resumo AS r
CROSS JOIN parametros AS pa
ORDER BY taxa_ocupacao_pct DESC;

/* ---- C2. Agendamentos por status e taxa de cancelamento ---- */
SELECT a.status,
       COUNT(*) AS qtd_agendamentos,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentual
FROM Agendamento AS a
GROUP BY a.status
ORDER BY qtd_agendamentos DESC;

/* ---- C3. Bancadas sem nenhuma reserva futura confirmada ---- */
SELECT b.identificacao, b.status, b.valor_hora
FROM Bancada AS b
WHERE NOT EXISTS (
    SELECT 1
    FROM Agendamento AS a
    WHERE a.id_bancada = b.id_bancada
      AND a.status = 'Confirmado'
      AND a.data_hora_inicio >= datetime('now', 'localtime')
);
