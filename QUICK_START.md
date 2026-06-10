# ⚡ Guia Rápido — Marcos Web com Banco de Dados

## 📦 O que você recebe

Arquivos para colocar sua aplicação **na web com banco de dados próprio** (sem Excel):

```
📁 arquivos/
├── models.py                      ← Estrutura do banco (NÃO EDITE)
├── app_database.py                ← Aplicação Flask (RENOMEAR para app.py)
├── migrate_excel_to_db.py          ← Importar dados do Excel para BD
├── requirements_db.txt             ← Dependências Python
├── SETUP_DATABASE.md               ← Documentação completa
├── Procfile                        ← Para deploy em produção
├── .gitignore                      ← Ignorar arquivos desnecessários
└── index.html                      ← (Use o que você já tem)
```

---

## 🚀 Quick Start (5 minutos)

### 1️⃣ Preparar no seu PC

```bash
# Abrir PowerShell/Terminal na pasta do projeto
cd C:\caminho\seu\projeto

# Instalar dependências
pip install -r requirements_db.txt

# Migrar dados DO EXCEL para o banco de dados
python migrate_excel_to_db.py

# Renomear a app
# (Windows) ren app_database.py app.py
# (Mac/Linux) mv app_database.py app.py

# Rodar
python app.py
```

**Acesse:** http://localhost:5000

---

### 2️⃣ Deploy na Nuvem (Render.com)

#### A. Criar repositório no GitHub

1. Crie um repo novo vazio em **github.com**
2. **Clone para seu PC:**
   ```bash
   git clone https://github.com/seu-usuario/marcos-web.git
   cd marcos-web
   ```

3. **Copie os arquivos** para essa pasta:
   - `models.py`
   - `app_database.py` (renomear para `app.py`)
   - `migrate_excel_to_db.py`
   - `requirements_db.txt`
   - `Procfile`
   - `.gitignore`
   - `templates/index.html`
   - `static/` (se tiver CSS/JS)

4. **Commit e push:**
   ```bash
   git add .
   git commit -m "Deploy inicial com banco de dados"
   git push origin main
   ```

#### B. Deploy no Render

1. Acesse **https://render.com**
2. Faça login com GitHub
3. Clique **"New Web Service"**
4. Conecte seu repositório
5. Preencha:
   - **Name:** marcos-web
   - **Environment:** Python 3.9
   - **Build command:** `pip install -r requirements_db.txt`
   - **Start command:** `gunicorn app:app`
6. Clique **"Deploy"**

⏱️ Aguarde 2-3 minutos...

**Sua URL:** `https://marcos-web.onrender.com`

---

## ❓ Perguntas frequentes

### P: Preciso fazer migração toda vez que rodar?
**R:** Não, apenas UMA VEZ na primeira instalação. Depois edita pelo site.

### P: Posso usar com PostgreSQL em produção?
**R:** Sim! Mude a connection string em `app.py`. SQLite é para começar rápido.

### P: Como faço backup?
**R:** Copie o arquivo `marcos.db`. Pronto!

### P: Posso sincronizar com o Excel?
**R:** Não automaticamente. Exporte dados do banco para Excel se precisar.

### P: Múltiplos usuários funcionam?
**R:** Sim, com SQLite funciona bem até ~10 usuários simultâneos. Para mais, use PostgreSQL.

---

## 🔄 Fluxo de dados

```
┌─────────────────────┐
│  PLANILHA EXCEL     │
│  (arquivo original) │
└──────────┬──────────┘
           │ (UMA VEZ via migrate_excel_to_db.py)
           ▼
┌─────────────────────┐
│   marcos.db         │ ◄─── Banco de dados SQLite
│  (novo, apenas BD)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Flask App        │ ◄─── app_database.py
│  (web/API)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   index.html        │ ◄─── Frontend (igual ao antes)
│  (interface)        │
└─────────────────────┘
```

**A partir de agora:**
- ✅ Edita tudo via web
- ✅ Sem sincronização manual
- ✅ Múltiplos usuários
- ✅ Deploy em qualquer cloud

---

## 📋 Checklist de Deploy

- [ ] Instalou `requirements_db.txt`
- [ ] Rodou `migrate_excel_to_db.py` (uma vez!)
- [ ] Testou `python app.py` localmente
- [ ] Criou repo no GitHub
- [ ] Conectou ao Render.com
- [ ] Acessou URL pública com sucesso
- [ ] Testou CRUD (criar, editar, deletar despesa)

---

## 🎉 Pronto!

Sua aplicação está:
- ✅ Na web
- ✅ Com banco de dados
- ✅ Acessível de qualquer lugar
- ✅ Múltiplos usuários
- ✅ Pronta para escalar

**Próximas melhorias (opcional):**
1. Adicionar login/autenticação
2. Migrar para PostgreSQL
3. Adicionar mais relatórios
4. Integração com APIs de pagamento

---

## 📞 Troubleshooting rápido

| Erro | Solução |
|------|---------|
| "No module named 'flask'" | `pip install -r requirements_db.txt` |
| "No such table: despesas" | `python migrate_excel_to_db.py` |
| "Address already in use" | Porta 5000 ocupada, use: `python app.py --port 8000` |
| Render não faz deploy | Verifique `git push` foi bem-sucedido |
| Dados não aparecem | Certifique-se que migrou antes |

---

**Dúvidas?** Leia `SETUP_DATABASE.md` para documentação completa.

**Sucesso!** 🚀
