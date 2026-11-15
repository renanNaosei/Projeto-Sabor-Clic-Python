/* 
   Usuários de teste: todos usam a senha  Senha@123  (somente para
   desenvolvimento — os valores abaixo são hashes reais gerados com
   werkzeug.security, compatíveis com o login do Flask).

   Observação sobre o estoque: as quantidades de INGREDIENTE representam
   o saldo atual, já descontados os pedidos de exemplo abaixo. Esses
   pedidos são anteriores à criação dos triggers (20_triggers.sql), por isso
   não geram baixa automática; a partir dos triggers, todo novo item de
   pedido baixa o estoque sozinho.

   ===================================================================== */

/* ---------------------------------------------------------------------
   Usuários (1 administrador, 2 clientes, 2 cozinheiros)
   --------------------------------------------------------------------- */
INSERT INTO Usuario (nome, email, senha_hash, tipo_usuario) VALUES
    ('Ana Souza',      'ana.admin@saborclic.com',
     'scrypt:32768:8:1$dO6NJcksBJljTlAV$a6c55713f3d3fde6bc42daf871fe4f51cae76b4c1afd5250264815442b6c7f2f7d132b065484dc73f7ea6fea193493b78a1757a317a1843034baf196c85c5a3b',
     'administrador'),
    ('Bruno Lima',     'bruno.cliente@saborclic.com',
     'scrypt:32768:8:1$KO6wZ2eU9Fx82Mr6$130c37839174873e18ce947d039c8e917ef0eeb06b03c0938d29186151a42d7407e0403d2e6635a39f3e012b6bc25ceac94308575e5c5e98fd964d56fe18e139',
     'cliente'),
    ('Daniela Costa',  'daniela.cliente@saborclic.com',
     'scrypt:32768:8:1$azoA3RoCxdc8nROe$4c2e890f40a7a5f4e9988a7c400e4dcae3cd0953be0255bdaf60d6b19ec38a130589df41b1035cdcc8ab4557ea15d27ea726fd234b12011278492dc393f80149',
     'cliente'),
    ('Carla Nunes',    'carla.cozinha@saborclic.com',
     'scrypt:32768:8:1$OjHKBI2ZbTDcZJfJ$f89949e2ff2b07777b7c25f9ba2d474cbf5f139019aea308dde0228ade203793de069891b7c139f953dead3fb04700bd33eb059d36c53232fab23077bf80b14f',
     'cozinheiro'),
    ('Marcos Pereira', 'marcos.cozinha@saborclic.com',
     'scrypt:32768:8:1$La3Syrjx7MtTEIgJ$45d1842e4bff1356d64393ee44fdf2bc625e24fc4f7fc2c5bba89314fc966a066e0700c6a8a572afb7b5d305f45b672f5ea22b4b146680d5f3fd874cc196fdb5',
     'cozinheiro');

INSERT INTO Administrador (id_usuario, nivel_permissao)
SELECT id_usuario, 'gestor_catalogo'
FROM Usuario WHERE email = 'ana.admin@saborclic.com';

INSERT INTO Cliente (id_usuario, endereco_entrega, telefone)
SELECT id_usuario, 'Rua das Flores, 123 - São Paulo/SP', '(11) 90000-0001'
FROM Usuario WHERE email = 'bruno.cliente@saborclic.com';

INSERT INTO Cliente (id_usuario, endereco_entrega, telefone)
SELECT id_usuario, 'Av. Paulista, 1500 - São Paulo/SP', '(11) 90000-0002'
FROM Usuario WHERE email = 'daniela.cliente@saborclic.com';

INSERT INTO Cozinheiro (id_usuario, turno_trabalho, especialidade)
SELECT id_usuario, 'Manhã', 'Massas'
FROM Usuario WHERE email = 'carla.cozinha@saborclic.com';

INSERT INTO Cozinheiro (id_usuario, turno_trabalho, especialidade)
SELECT id_usuario, 'Tarde', 'Grelhados'
FROM Usuario WHERE email = 'marcos.cozinha@saborclic.com';

/* ---------------------------------------------------------------------
   Cardápio: 31 pratos do protótipo HTML (ids 1 a 31, na mesma ordem e com os
   mesmos preços) + Marmita Executiva e Strogonoff de Frango (ids 32 e 33),
   --------------------------------------------------------------------- */
INSERT INTO Prato (nome, descricao, preco, categoria, disponivel, imagem_url, id_usuario_admin) VALUES
    ('X-Burguer', 'Pão brioche, hambúrguer artesanal, queijo e molho da casa.', 24.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('X-Bacon', 'Hambúrguer, queijo derretido, bacon crocante e maionese especial.', 29.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1551782450-a2132b4ba21d?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Cheeseburger Duplo', 'Dois discos de carne, cheddar, cebola e pão macio.', 34.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1571091718767-18b5b1457add?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Hot Dog Especial', 'Pão, salsicha, purê cremoso, milho, batata palha e molhos.', 19.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1612392062798-2dbaa8f6b3f0?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Chicken Burger', 'Frango empanado crocante, alface e molho cremoso.', 27.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1606755962773-d324e0a13086?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Pizza Margherita', 'Molho de tomate, muçarela, tomate fresco e manjericão.', 42.90, 'Pizzas', 1, 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Pizza Calabresa', 'Calabresa fatiada, cebola, muçarela e orégano.', 44.90, 'Pizzas', 1, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Pizza Quatro Queijos', 'Uma combinação cremosa de quatro queijos selecionados.', 49.90, 'Pizzas', 1, 'https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Pizza Pepperoni', 'Muçarela, pepperoni e molho de tomate da casa.', 48.90, 'Pizzas', 1, 'https://images.unsplash.com/photo-1628840042765-356cda07504e?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Lasanha à Bolonhesa', 'Camadas de massa, molho bolonhesa e queijo gratinado.', 36.90, 'Massas', 1, 'https://images.unsplash.com/photo-1574894709920-11b28e7367e3?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Espaguete ao Sugo', 'Espaguete com molho de tomate, manjericão e parmesão.', 29.90, 'Massas', 1, 'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Penne ao Molho Branco', 'Penne envolvido em molho branco cremoso e parmesão.', 34.90, 'Massas', 1, 'https://images.unsplash.com/photo-1555949258-eb67b1ef0ceb?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Fettuccine ao Pesto', 'Massa delicada com pesto de manjericão e parmesão.', 37.90, 'Massas', 1, 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Batata Frita', 'Batatas douradas e crocantes, com sal na medida.', 18.90, 'Porções', 1, 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Onion Rings', 'Anéis de cebola empanados e crocantes.', 22.90, 'Porções', 1, 'https://images.unsplash.com/photo-1639024471283-03518883512d?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Frango Crocante', 'Tiras de frango empanadas, acompanhadas de molho especial.', 32.90, 'Porções', 1, 'https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Salada Caesar', 'Alface, frango grelhado, croutons e molho caesar.', 27.90, 'Saladas', 1, 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Salada Tropical', 'Folhas frescas, tomate, cenoura e frutas da estação.', 25.90, 'Saladas', 1, 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Brownie com Sorvete', 'Brownie de chocolate servido com sorvete cremoso.', 19.90, 'Sobremesas', 1, 'https://images.unsplash.com/photo-1564355808539-22fda35bed7e?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Cheesecake', 'Cheesecake cremoso com cobertura de frutas vermelhas.', 18.90, 'Sobremesas', 1, 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Pudim', 'Pudim tradicional com calda de caramelo.', 12.90, 'Sobremesas', 1, 'https://images.unsplash.com/photo-1511911063855-2bf39afa5b2e?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Refrigerante Lata', 'Lata gelada de refrigerante 350 ml.', 6.90, 'Bebidas', 1, 'https://images.unsplash.com/photo-1581636625402-29b2a704ef13?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Suco de Laranja', 'Suco de laranja preparado na hora, 300 ml.', 9.90, 'Bebidas', 1, 'https://images.unsplash.com/photo-1600271886742-f049cd451bba?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Limonada', 'Limonada refrescante, feita com limões frescos.', 8.90, 'Bebidas', 1, 'https://images.unsplash.com/photo-1513558161293-cdaf765edfd4?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Milk-shake de Chocolate', 'Milk-shake gelado e cremoso de chocolate.', 17.90, 'Bebidas', 1, 'https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Café Gelado', 'Café gelado com leite e toque de baunilha.', 13.90, 'Bebidas', 1, 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('X-Salada', 'Hambúrguer artesanal, queijo, alface, tomate e maionese da casa.', 27.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1553979459-d2229ba7433a?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('X-Egg', 'Pão brioche, hambúrguer, queijo, ovo e salada fresca.', 28.90, 'Lanches', 1, 'https://images.unsplash.com/photo-1561758033-d89a9ad46330?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Burger Vegetariano', 'Hambúrguer de grão-de-bico, queijo, alface e molho especial.', 28.90, 'Vegetarianos', 1, 'https://images.unsplash.com/photo-1520072959219-c595dc870360?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Pizza Vegetariana', 'Muçarela, abobrinha, tomate, champignon, cebola e azeitonas.', 46.90, 'Vegetarianos', 1, 'https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Salada Verde', 'Mix de folhas, pepino, tomate-cereja, cenoura e molho cítrico.', 22.90, 'Vegetarianos', 1, 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=85', (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Marmita Executiva', 'Arroz, feijão, proteína e acompanhamento.', 24.90, 'Marmitas', 1, NULL, (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com')),
    ('Strogonoff de Frango', 'Frango ao molho cremoso com arroz e batata palha.', 29.90, 'Pratos principais', 1, NULL, (SELECT id_usuario FROM Usuario WHERE email = 'ana.admin@saborclic.com'));

/* ---------------------------------------------------------------------
   Bancadas
   --------------------------------------------------------------------- */
INSERT INTO Bancada (identificacao, descricao, capacidade, equipamentos, valor_hora, status) VALUES
    ('Bancada 01', 'Cozinha equipada com fogão industrial e coifa.', 4, 'Fogão 4 bocas, forno, coifa, geladeira', 45.00, 'Disponível'),
    ('Bancada 02', 'Bancada ampla para produção de marmitas.',        6, 'Fogão 6 bocas, forno combinado, freezer', 60.00, 'Disponível'),
    ('Bancada 03', 'Espaço em reforma da exaustão.',                  3, 'Fogão 2 bocas, geladeira',                35.00, 'Manutenção');

/* ---------------------------------------------------------------------
   Ingredientes (saldo atual e estoque mínimo)
   Queijo mussarela e creme de leite ficam propositalmente abaixo do
   mínimo, para o relatório de reposição ter o que mostrar.
   --------------------------------------------------------------------- */
INSERT INTO Ingrediente (nome, unidade_medida, quantidade_estoque, estoque_minimo) VALUES
    ('Arroz',             'kg', 18.500, 10.000),
    ('Feijão',            'kg', 12.000,  8.000),
    ('Peito de frango',   'kg', 14.750, 10.000),
    ('Carne moída',       'kg',  9.200,  6.000),
    ('Massa de lasanha',  'kg',  5.400,  4.000),
    ('Molho de tomate',   'L',   7.000,  5.000),
    ('Queijo mussarela',  'kg',  3.100,  4.000),
    ('Creme de leite',    'L',   1.500,  2.000),
    ('Batata palha',      'kg',  2.000,  1.000);

/* ---------------------------------------------------------------------
   Fichas técnicas (consumo de ingredientes por porção)
   --------------------------------------------------------------------- */
WITH f (prato, ingrediente, quantidade) AS (
    VALUES
        ('Marmita Executiva',    'Arroz',            0.150),
        ('Marmita Executiva',    'Feijão',           0.100),
        ('Marmita Executiva',    'Peito de frango',  0.200),
        ('Strogonoff de Frango', 'Peito de frango',  0.250),
        ('Strogonoff de Frango', 'Creme de leite',   0.100),
        ('Strogonoff de Frango', 'Arroz',            0.150),
        ('Strogonoff de Frango', 'Batata palha',     0.030),
        ('Strogonoff de Frango', 'Molho de tomate',  0.050),
        ('Lasanha à Bolonhesa',  'Massa de lasanha', 0.150),
        ('Lasanha à Bolonhesa',  'Carne moída',      0.180),
        ('Lasanha à Bolonhesa',  'Molho de tomate',  0.150),
        ('Lasanha à Bolonhesa',  'Queijo mussarela', 0.120)
)
INSERT INTO Ficha_Tecnica (id_prato, id_ingrediente, quantidade_utilizada)
SELECT p.id_prato, i.id_ingrediente, f.quantidade
FROM f
JOIN Prato AS p        ON p.nome = f.prato
JOIN Ingrediente AS i  ON i.nome = f.ingrediente;

/* ---------------------------------------------------------------------
   Pedidos de exemplo (histórico para os relatórios de vendas)
   --------------------------------------------------------------------- */
WITH u AS (
    SELECT
        (SELECT id_usuario FROM Usuario WHERE email = 'bruno.cliente@saborclic.com')   AS bruno,
        (SELECT id_usuario FROM Usuario WHERE email = 'daniela.cliente@saborclic.com') AS daniela,
        (SELECT id_usuario FROM Usuario WHERE email = 'carla.cozinha@saborclic.com')   AS carla,
        (SELECT id_usuario FROM Usuario WHERE email = 'marcos.cozinha@saborclic.com')  AS marcos
)
INSERT INTO Pedido (id_pedido, id_usuario_cliente, id_usuario_cozinheiro, data_hora_pedido, status)
SELECT 1, bruno,   carla,  '2026-10-26 12:10:00.000000', 'Pronto para Entrega' FROM u UNION ALL
SELECT 2, daniela, marcos, '2026-10-28 19:30:00.000000', 'Pronto para Entrega' FROM u UNION ALL
SELECT 3, bruno,   carla,  '2026-11-02 12:45:00.000000', 'Pronto para Entrega' FROM u UNION ALL
SELECT 4, bruno,   marcos, '2026-11-03 13:05:00.000000', 'Em Preparo'          FROM u UNION ALL
SELECT 5, daniela, carla,  '2026-11-04 11:50:00.000000', 'Iniciando Preparo'   FROM u UNION ALL
SELECT 6, bruno,   NULL,   '2026-11-04 12:20:00.000000', 'Aguardando'          FROM u;

WITH i (id_pedido, prato, qtd, tempo_min) AS (
    VALUES
        (1, 'Marmita Executiva',    2, 20),
        (1, 'Lasanha à Bolonhesa',  1, 40),
        (2, 'Strogonoff de Frango', 1, 30),
        (2, 'Marmita Executiva',    1, 20),
        (3, 'Lasanha à Bolonhesa',  3, 40),
        (4, 'Strogonoff de Frango', 2, 30),
        (5, 'Lasanha à Bolonhesa',  1, 40),
        (5, 'Marmita Executiva',    2, 20),
        (6, 'Marmita Executiva',    1, 20),
        (6, 'Strogonoff de Frango', 1, 30)
)
INSERT INTO Item_Pedido (id_pedido, id_prato, quantidade, preco_unitario, tempo_estimado_preparo)
SELECT i.id_pedido, pr.id_prato, i.qtd, pr.preco, i.tempo_min
FROM i
JOIN Prato AS pr ON pr.nome = i.prato;

UPDATE Pedido
SET valor_total = ROUND((
        SELECT SUM(ip.quantidade * ip.preco_unitario)
        FROM Item_Pedido AS ip
        WHERE ip.id_pedido = Pedido.id_pedido
    ), 2);

/* ---------------------------------------------------------------------
   Agendamentos de bancada (sem sobreposição entre os confirmados)
   --------------------------------------------------------------------- */
WITH r (cliente, bancada, inicio, fim, status) AS (
    VALUES
        ('bruno.cliente@saborclic.com',   'Bancada 01', '2026-10-20 08:00:00.000000', '2026-10-20 12:00:00.000000', 'Concluído'),
        ('daniela.cliente@saborclic.com', 'Bancada 01', '2026-10-27 14:00:00.000000', '2026-10-27 18:00:00.000000', 'Concluído'),
        ('bruno.cliente@saborclic.com',   'Bancada 01', '2026-11-06 08:00:00.000000', '2026-11-06 11:00:00.000000', 'Confirmado'),
        ('daniela.cliente@saborclic.com', 'Bancada 01', '2026-11-06 13:00:00.000000', '2026-11-06 17:00:00.000000', 'Confirmado'),
        ('bruno.cliente@saborclic.com',   'Bancada 01', '2026-11-12 09:00:00.000000', '2026-11-12 13:00:00.000000', 'Cancelado'),
        ('daniela.cliente@saborclic.com', 'Bancada 02', '2026-11-05 09:00:00.000000', '2026-11-05 15:00:00.000000', 'Confirmado'),
        ('bruno.cliente@saborclic.com',   'Bancada 02', '2026-11-10 08:00:00.000000', '2026-11-10 12:00:00.000000', 'Confirmado')
)
INSERT INTO Agendamento (id_usuario_cliente, id_bancada, data_hora_inicio, data_hora_fim, status)
SELECT u.id_usuario, b.id_bancada, r.inicio, r.fim, r.status
FROM r
JOIN Usuario AS u  ON u.email = r.cliente
JOIN Bancada AS b  ON b.identificacao = r.bancada;
