# LoteCerto API

API Python em FastAPI para sincronizacao do app LoteCerto.

## O que entrega

- autenticacao simples por token bearer
- CRUD de fazendas, lotes, vacinas e registros de vacinacao
- dashboard resumido
- alertas de vacinas proximas ou atrasadas
- sincronizacao incremental por `updated_since`
- bootstrap automatico de usuario administrador

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

A API sobe por padrao em `http://127.0.0.1:8000`.

## Deploy no Railway

O backend ja esta preparado com [`railway.toml`](C:\developer.workspace\Projetos\lotecerto\backend\railway.toml).

Passo a passo recomendado:

1. Crie um novo projeto no Railway apontando para a pasta `backend`.
2. Adicione um volume persistente e monte em `/data`.
3. Configure as variaveis de ambiente:
   - `LOTECERTO_APP_NAME=LoteCerto API`
   - `LOTECERTO_API_PREFIX=/api/v1`
   - `LOTECERTO_DATABASE_URL=sqlite:////data/lotecerto_api.db`
   - `LOTECERTO_SECRET_KEY=troque-por-uma-chave-forte`
   - `LOTECERTO_ACCESS_TOKEN_EXPIRE_MINUTES=1440`
   - `LOTECERTO_DEFAULT_ADMIN_USERNAME=admin`
   - `LOTECERTO_DEFAULT_ADMIN_PASSWORD=troque-a-senha`
4. Faça o primeiro deploy.
5. Depois do deploy, copie a URL publica do Railway.

Testes uteis apos publicar:

- raiz da API: `/`
- healthcheck: `/health`
- login e rotas do app: `/api/v1/...`

URL para usar no app:

```text
https://SEU-SERVICO.up.railway.app/api/v1
```

Essa URL pode ser preenchida no onboarding ou em `Configuracoes` no aplicativo.

## Login padrao

- usuario: `admin`
- senha: `123456`

Troque esses valores no `.env` antes de publicar.
