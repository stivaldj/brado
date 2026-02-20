# Visão geral da arquitetura

Este documento descreve a arquitetura do projeto **br_manifest_app**, que combina um frontend estático, um backend em Python, um banco de dados relacional e um mecanismo de agendamento de tarefas.

- **Frontend** – arquivos estáticos (`index.html`, `script.js`, `styles.css`) servidos pelo backend ou por um servidor web simples.
- **Backend** – camada escrita em Python, organizada no diretório `backend/`. O ponto de entrada é `backend/main.py` (FastAPI ou Flask, dependendo da implementação).
- **Banco de dados** – SQLite utilizado para desenvolvimento (`fallback.db`) e qualquer outro SGBD compatível com SQLAlchemy em produção. As migrações são gerenciadas pelo **Alembic**.
- **Cronjob** – tarefas recorrentes executadas pelo **APScheduler** definidas em `backend/cron_job.py`.

---

## Diagrama de componentes

```mermaid
flowchart TD
    subgraph Frontend
        FE[HTML/JS/CSS]
    end
    subgraph Backend
        BE[backend/main.py]
        DB[backend/database.py]
        PER[backend/persistence.py]
        CRON[backend/cron_job.py]
    end
    subgraph DB
        SQLITE[(SQLite / outro SGBD)]
    end
    FE -->|requisição HTTP| BE
    BE -->|acessa| DB
    DB -->|persistência| SQLITE
    PER -->|operções ORM| DB
    CRON -->|executa jobs| PER
    CRON -->|acessa| DB
```

---

## Módulos principais

| Módulo | Função |
|--------|-------|
| `backend/main.py` | Inicializa o servidor web (FastAPI/Flask), define rotas e injeta dependências. |
| `backend/database.py` | Configura o motor SQLAlchemy, cria a sessão (`SessionLocal`) e lê a variável `DB_URL` do `.env`. |
| `backend/persistence.py` | Implementa repositórios que utilizam SQLAlchemy para CRUD, abstraindo a camada de modelo. |
| `backend/cron_job.py` | Define jobs recorrentes (ex.: limpeza, geração de relatórios) e agenda‑os com APScheduler. |

---

## Camada de persistência com SQLAlchemy e Alembic

- **SQLAlchemy** é usado para mapear as classes definidas em `backend/models.py` para tabelas do banco de dados. O `Session` criado em `backend/database.py` é passado para os repositórios em `persistence.py`.
- **Alembic** gerencia migrações. O diretório `alembic/` contém o script de configuração (`alembic.ini`) e as versões de migração (`alembic/versions/`). Para criar ou aplicar migrações, use:
  ```bash
  alembic revision --autogenerate -m "descrição"
  alembic upgrade head
  ```
- O modelo de dados está definido em `backend/models.py`. Cada mudança estrutural deve ser refletida em uma nova migração Alembic.

---

## Configuração

O backend lê variáveis de ambiente a partir de `backend/.env`. As principais são:

- `DB_URL` – URL de conexão do banco de dados (ex.: `sqlite:///fallback.db` ou `postgresql://user:pass@host/db`).
- `SCHEDULER_TIMEZONE` – Fuso horário usado pelo APScheduler.
- `APP_HOST` e `APP_PORT` – Endereço e porta para o servidor web.

**Exemplo de `.env`**
```dotenv
DB_URL=sqlite:///fallback.db
SCHEDULER_TIMEZONE=America/Sao_Paulo
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## Como iniciar o servidor e o scheduler

1. **Instalar dependências** (caso ainda não tenha):
   ```bash
   pip install -r requirements.txt
   ```
2. **Iniciar o servidor web** (FastAPI com Uvicorn):
   ```bash
   uvicorn backend.main:app --host $APP_HOST --port $APP_PORT --reload
   ```
3. **Iniciar o scheduler** (executa jobs em background):
   ```bash
   python -m backend.cron_job
   ```
   - Alternativamente, o scheduler pode ser iniciado como parte da aplicação principal, dependendo da implementação.

---

## Dependências e requisitos

- **Python 3.9+**
- **FastAPI** (ou Flask, conforme o código)
- **Uvicorn** – servidor ASGI
- **SQLAlchemy** – ORM
- **Alembic** – migrações de banco de dados
- **APScheduler** – agendamento de tarefas
- **python-dotenv** – carregamento de variáveis de ambiente
- **pydantic** – validação de dados (se usado)

> **Nota:** Verifique o arquivo `requirements.txt` (ou `pyproject.toml`) para a lista completa de versões.

---

*Documentação criada automaticamente por Aurora Alpha – Document Writer.*