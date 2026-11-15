## Estrutura

| Pasta | Conteúdo |
|---|---|
| `backend/` | API Flask (app factory, blueprints, MVC + serviços, sessão + RBAC + CSRF) |
| `frontend/` | HTML5, CSS3 e JavaScript em módulos ES — **idêntico** ao da versão SQL Server |
| `database/` | Scripts SQLite: modelo físico, dados, relatórios e triggers |

## 1. Backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate            (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env            (Linux/macOS: cp .env.example .env)
flask --app run init-db           # cria backend/instance/sabor_clic.db (tabelas + dados + triggers)
python run.py
```

Não há servidor de banco nem driver ODBC para instalar: o banco é o arquivo `instance/sabor_clic.db`.
Teste: <http://127.0.0.1:5000/api/health>.

`init-db` executa `database/01_modelo_fisico.sql` → `02_insercoes_basicas.sql` → `20_triggers.sql`
**e apaga os dados atuais** (pede confirmação). Use `--sem-dados` para criar só tabelas e triggers.
Para abrir o banco e rodar os relatórios (`database/11_queries_relatorios.sql`), use o "DB Browser for SQLite"
ou o comando `sqlite3 instance/sabor_clic.db`.

Usuários de teste (senha de todos: `Senha@123`): `ana.admin@saborclic.com` (administrador),
`bruno.cliente@saborclic.com` e `daniela.cliente@saborclic.com` (clientes),
`carla.cozinha@saborclic.com` e `marcos.cozinha@saborclic.com` (cozinheiros).

Criar administrador/cozinheiro: `flask --app run criar-usuario --papel cozinheiro --turno Tarde`.

### Testes

```
pip install -r requirements-dev.txt
pytest -q
```

Os testes criam um SQLite em memória com o **mesmo schema e os mesmos triggers** dos scripts, então
a baixa de estoque, o total do pedido e o conflito de horário são testados no banco de verdade.

## 2. Frontend

```
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```

Acesse <http://127.0.0.1:5500>. Use sempre `127.0.0.1` (não `localhost`) para front e API.

## 3. Endpoints e segurança

Iguais aos da versão SQL Server (CSRF, RBAC, sessão HttpOnly, limite de login, validação de entrada).
Erros de regra de negócio do banco (estoque insuficiente, horário em conflito) continuam voltando como HTTP 409.

## 4. Telas por perfil (front-end)

| Perfil | O que aparece na página |
|---|---|
| Visitante | Cardápio, carrinho, login e cadastro |
| Cliente | Finalizar pedido + **Meus pedidos** (status em 4 etapas) |
| Cozinheiro | **Fila da cozinha**: avança o status (Aguardando → Iniciando Preparo → Em Preparo → Pronto para Entrega) |
| Administrador | Fila da cozinha só para acompanhar (sem botões de ação) |

As duas listas se atualizam sozinhas a cada 10 segundos, sem F5 (pausam quando a aba está oculta).
As regras de permissão valem no servidor; o front só decide o que mostrar.

Classes (POO, `frontend/js/models.js`): `Usuario` é a base e `Cliente`, `Cozinheiro` e `Administrador`
herdam dela, sobrescrevendo `podeFazerPedidos`, `podeVerFila` e `podeAtualizarStatus` (polimorfismo).
`Usuario.deApi()` escolhe a subclasse conforme o perfil devolvido pela API.
