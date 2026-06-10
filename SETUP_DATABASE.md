# 🚀 Marcos Web — Sistema com Banco de Dados

Versão 3.0 com **SQLite** como banco de dados (escalável para PostgreSQL).

## 📋 O que mudou?

| Antes | Agora |
|-------|-------|
| Lê dados direto do Excel | Dados em banco de dados SQLite |
| Sem sincronização | Múltiplos usuários simultâneos |
| Apenas local | Deploy fácil na web |
| Sem backup | Backup simples de um arquivo |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────┐
│          Frontend (index.html)               │
│     (Vue.js + Dashboard interativo)         │
└──────────────┬──────────────────────────────┘
               │ API REST
┌──────────────▼──────────────────────────────┐
│        Flask (app_database.py)              │
│  (Models, Rotas, Lógica de negócio)        │
└──────────────┬──────────────────────────────┘
               │ SQLAlchemy ORM
┌──────────────▼──────────────────────────────┐
│         SQLite Database (marcos.db)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Despesas │  │Recebimts │  │Categorias│  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

---

## 🔧 Instalação Local

### 1️⃣ Pré-requisitos
- Python 3.9+
- pip

### 2️⃣ Clonar/baixar os arquivos

Você precisa desses arquivos:
```
projeto-marcos/
├── models.py                      ← Estrutura do banco
├── app_database.py                ← App Flask novo
├── migrate_excel_to_db.py          ← Script de migração
├── requirements_db.txt             ← Dependências
├── templates/
│   └── index.html                  ← Frontend (use o que você já tem)
├── PLANILHA_ESTRATEGICA_MARCOS_2026.xlsx  ← Para migrar dados
└── categorias.json                 ← Para migrar categorias (opcional)
```

### 3️⃣ Instalar dependências

```bash
pip install -r requirements_db.txt
```

### 4️⃣ Migrar dados do Excel para BD

```bash
python migrate_excel_to_db.py
```

Ou com caminho customizado:

```bash
python migrate_excel_to_db.py --xlsx /caminho/planilha.xlsx --db /caminho/marcos.db
```

**O que acontece:**
- Lê a planilha Excel
- Cria o banco de dados `marcos.db`
- Importa todas as despesas, recebimentos, categorias e clientes
- Calcula status e prioridades automaticamente

### 5️⃣ Rodar a aplicação

```bash
python app_database.py
```

Acesse: **http://localhost:5000**

---

## 🌍 Deploy na Web

### Opção A: Render.com (recomendado)

#### Passo 1: Prepare o repositório GitHub

1. Crie um repositório no GitHub com os arquivos
2. Crie um arquivo `.env` (não commite):
   ```
   DATABASE_PATH=marcos.db
   FLASK_ENV=production
   ```

3. Crie um arquivo `Procfile` (para indicar como rodar):
   ```
   web: gunicorn app_database:app
   release: python migrate_excel_to_db.py --db marcos.db
   ```

4. Commit e push:
   ```bash
   git add .
   git commit -m "Deploy com banco de dados"
   git push
   ```

#### Passo 2: Deploy no Render

1. Acesse **https://render.com** e faça login com GitHub
2. Clique em **"New Web Service"**
3. Conecte seu repositório GitHub
4. Configure assim:
   - **Name:** marcos-web
   - **Runtime:** Python 3.9
   - **Build command:** `pip install -r requirements_db.txt`
   - **Start command:** `gunicorn app_database:app`
5. Adicione variáveis de ambiente:
   - `PYTHON_VERSION=3.9.13`
   - `DATABASE_PATH=/tmp/marcos.db`
6. Deploy!

**URL final:** `https://marcos-web.onrender.com`

⚠️ **Nota:** SQLite em `/tmp` é **persistente por deploy**, mas será perdido se a instância reiniciar. Para produção, use PostgreSQL.

---

### Opção B: Heroku

1. Instale Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Login:
   ```bash
   heroku login
   ```

3. Crie o app:
   ```bash
   heroku create seu-app-marcos
   ```

4. Adicione PostgreSQL (banco de dados produção):
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev -a seu-app-marcos
   ```

5. Configure variáveis:
   ```bash
   heroku config:set DATABASE_PATH='postgresql://...' -a seu-app-marcos
   ```

6. Deploy:
   ```bash
   git push heroku main
   ```

---

### Opção C: Railway

1. Acesse **https://railway.app**
2. Conecte GitHub
3. Deploy é automático quando faz push

---

## 🔄 Migração: Excel → Banco de Dados

### Primeira vez (setup inicial)

```bash
python migrate_excel_to_db.py \
  --xlsx PLANILHA_ESTRATEGICA_MARCOS_2026.xlsx \
  --db marcos.db
```

### Posterior (atualizar dados)

Se adicionar dados no Excel depois que migrou:

```bash
# Opção 1: Recriar do zero (limpa tudo)
rm marcos.db
python migrate_excel_to_db.py

# Opção 2: Manual via UI (recomendado)
# Use a interface web para adicionar/editar dados
```

---

## 📊 Estrutura do Banco de Dados

### Tabela: `despesas`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PK | Identificador único |
| vencimento | DATE | Data de vencimento |
| mes | STRING | Mês em português |
| fornecedor | STRING | Nome do fornecedor |
| categoria | STRING | Categoria (ex: ABASTECIMENTO) |
| descricao | TEXT | Descrição da despesa |
| forma_pgto | STRING | Forma de pagamento (PIX, BOLETO, etc) |
| valor_previsto | FLOAT | Valor esperado |
| valor_pago | FLOAT | Valor já pago |
| liquidado | STRING | 'Sim' ou 'Não' |
| status | STRING | 'Pendente', 'Pago', 'Atrasado' |
| dias | INTEGER | Dias até vencimento |
| prioridade | STRING | '1-CRITICO', '2-ALTO', '3-MEDIO', '4-BAIXO' |
| data_criacao | DATETIME | Quando foi criado |
| data_update | DATETIME | Última atualização |

### Tabela: `recebimentos`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PK | Identificador único |
| vencimento | DATE | Data de vencimento |
| cliente | STRING | Nome do cliente |
| descricao | TEXT | Descrição do serviço |
| valor_esperado | FLOAT | Valor a receber |
| valor_recebido | FLOAT | Valor já recebido |
| status | STRING | 'A Receber', 'Recebido', 'Atrasado' |
| data_criacao | DATETIME | Quando foi criado |
| data_update | DATETIME | Última atualização |

### Tabela: `categorias`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PK | Identificador único |
| tipo | STRING | 'pagar', 'receber', 'cliente' |
| nome | STRING | Nome da categoria |
| data_criacao | DATETIME | Quando foi criado |

### Tabela: `clientes`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PK | Identificador único |
| nome | STRING | Nome do cliente (ÚNICO) |
| data_criacao | DATETIME | Quando foi criado |

### Tabela: `caixa`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PK | Sempre 1 |
| saldo | FLOAT | Saldo de caixa |
| data_update | DATETIME | Última atualização |

---

## 🔌 API REST (Mesma do app antigo!)

A API mantém compatibilidade. Alterações mínimas no frontend:

### Exemplos de uso

```bash
# Listar despesas
curl http://localhost:5000/api/despesas

# Adicionar despesa
curl -X POST http://localhost:5000/api/despesas \
  -H "Content-Type: application/json" \
  -d '{
    "vencimento": "2026-06-15",
    "fornecedor": "Fornecedor A",
    "categoria": "ABASTECIMENTO",
    "descricao": "Gasolina",
    "forma_pgto": "PIX",
    "valor_previsto": 500.00,
    "valor_pago": 0,
    "liquidado": "Não"
  }'

# Atualizar despesa ID 1
curl -X PUT http://localhost:5000/api/despesas/1 \
  -H "Content-Type: application/json" \
  -d '{"liquidado": "Sim", "valor_pago": 500.00}'

# Deletar despesa ID 1
curl -X DELETE http://localhost:5000/api/despesas/1

# Dashboard
curl http://localhost:5000/api/dashboard

# PDF report
curl http://localhost:5000/api/relatorio/pdf?tipo=completo > relatorio.pdf
```

---

## 🛡️ Backup e Restore

### Backup

```bash
# Copiar o arquivo do banco
cp marcos.db marcos_backup_$(date +%Y%m%d_%H%M%S).db
```

### Restore

```bash
# Substituir pelo backup
cp marcos_backup_20260609_143000.db marcos.db
```

---

## 🐛 Troubleshooting

### Erro: "database is locked"

**Solução:** Feche outras conexões
```bash
# Reinicie a app
pkill -f "python app_database"
```

### Erro: "ModuleNotFoundError: No module named 'models'"

**Solução:** Certifique-se que `models.py` está na mesma pasta

### Erro: "No such table: despesas"

**Solução:** Execute a migração
```bash
python migrate_excel_to_db.py
```

### Dados não aparecem após migração

**Solução:** Verifique se o Excel tem dados em:
- Aba `DADOS` (despesas)
- Aba `CONTAS A RECEBER` (recebimentos)
- Célula `B5` da aba `PAINEL DE CONTROLE` (caixa)

---

## 📈 Próximos passos (escalabilidade)

Se quiser escalar para mais usuários/dados:

### 1️⃣ Migrar para PostgreSQL

Apenas mude a connection string:

```python
# Em app_database.py
DATABASE_URI = "postgresql://user:password@localhost/marcos"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
```

### 2️⃣ Adicionar autenticação

```bash
pip install flask-login flask-jwt-extended
```

### 3️⃣ Deploy em produção com HTTPS

Usar Render.com ou Heroku automaticamente adiciona SSL.

---

## 📞 Suporte

Se tiver dúvidas:

1. Verifique o console da app (logs)
2. Teste a API direto com `curl`
3. Verifique se o banco existe: `sqlite3 marcos.db ".tables"`

---

**Pronto para a web!** 🚀
