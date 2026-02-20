
"""FastAPI application exposing endpoints for the civic platform prototype."""
import json
import os
import time
from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import db_instance
from .auth import login_user, get_current_token
from .sync_status import read_sync_status
from . import persistence
from .interview import engine as interview_engine

app = FastAPI(title='Brazilian Civic Manifestation & Voting API',
              description='Prototype implementation of a public demonstration and voting platform.',
              version='0.2.0')

cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:13000,http://127.0.0.1:13000")
cors_allow_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYNC_STALE_SECONDS = int(os.getenv("SYNC_STALE_SECONDS", "2700"))
AUTH_TOKEN_TTL = 1800  # 30 minutos


def _public_deputado(row: dict) -> dict:
    safe = dict(row)
    safe.pop("cpf", None)
    safe.pop("status_email", None)
    safe.pop("gabinete_email", None)
    return safe


def _get_db_session():
    sess = persistence.SessionLocal()
    try:
        yield sess
    finally:
        sess.close()


# =========================================================================
# Router /api/v1 — endpoints consumidos pelo frontend Next.js
# =========================================================================
v1 = APIRouter(prefix="/api/v1")


# -------------------------------------------------------------------------
# Auth v2 — autenticação anônima por client_id
# -------------------------------------------------------------------------
@v1.post('/auth/token', response_model=models.AuthTokenResponse)
def auth_token(request: models.AuthTokenRequest) -> models.AuthTokenResponse:
    """Emite um bearer token para um client_id anônimo.

    O frontend usa este endpoint para autenticar sessões sem CPF.
    Para fins de prototipagem, o client_id é armazenado como identificador do usuário.
    """
    client_id = request.client_id.strip()
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id must be provided')
    token = login_user(client_id)
    return models.AuthTokenResponse(
        access_token=token,
        expires_in=AUTH_TOKEN_TTL,
        token_type='bearer',
    )


@v1.get('/auth/me', response_model=models.AuthMeResponse)
def auth_me(token: str = Depends(get_current_token)) -> models.AuthMeResponse:
    """Retorna informações do usuário autenticado pela sessão atual."""
    client_id = db_instance.get_cpf(token)
    if not client_id:
        raise HTTPException(status_code=401, detail='Token inválido')
    return models.AuthMeResponse(subject=client_id, ttl=AUTH_TOKEN_TTL)


# -------------------------------------------------------------------------
# Interview — questionário político e matching de partidos
# -------------------------------------------------------------------------
@v1.post('/interview/start', response_model=models.InterviewStartResponse)
def interview_start(
    request: models.InterviewStartRequest,
    token: str = Depends(get_current_token),
    db=Depends(_get_db_session),
) -> models.InterviewStartResponse:
    """Inicia uma nova sessão de entrevista e retorna a primeira questão."""
    client_id = db_instance.get_cpf(token)
    result = interview_engine.start_session(
        db, client_id,
        persistence.InterviewSession,
        persistence.InterviewAnswer,
    )
    q = result.get("question")
    first_q = models.InterviewQuestion(**q) if q else None
    return models.InterviewStartResponse(
        session_id=result["session_id"],
        question=first_q,
        next_question=first_q,
        answered_count=0,
    )


@v1.post('/interview/{session_id}/answer', response_model=models.InterviewAnswerResponse)
def interview_answer(
    session_id: str,
    request: models.InterviewAnswerRequest,
    token: str = Depends(get_current_token),
    db=Depends(_get_db_session),
) -> models.InterviewAnswerResponse:
    """Registra a resposta Likert (1-7) para a questão atual e retorna a próxima."""
    try:
        result = interview_engine.answer_question(
            db=db,
            session_id=session_id,
            question_id=request.question_id or "",
            answer=request.answer,
            InterviewSession=persistence.InterviewSession,
            InterviewAnswer=persistence.InterviewAnswer,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    nq_raw = result.get("next_question")
    nq = models.InterviewQuestion(**nq_raw) if nq_raw else None
    return models.InterviewAnswerResponse(
        session_id=result["session_id"],
        next_question=nq,
        answered_count=result["answered_count"],
        done=result["done"],
    )


@v1.post('/interview/{session_id}/finish', response_model=models.InterviewResult)
def interview_finish(
    session_id: str,
    token: str = Depends(get_current_token),
    db=Depends(_get_db_session),
) -> models.InterviewResult:
    """Finaliza a sessão, calcula o vetor 8D e retorna o ranking de partidos."""
    try:
        result = interview_engine.finish_session(
            db=db,
            session_id=session_id,
            InterviewSession=persistence.InterviewSession,
            InterviewAnswer=persistence.InterviewAnswer,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _build_interview_result(result)


@v1.get('/interview/{session_id}/result', response_model=models.InterviewResult)
def interview_result(
    session_id: str,
    token: str = Depends(get_current_token),
    db=Depends(_get_db_session),
) -> models.InterviewResult:
    """Retorna o resultado calculado de uma sessão finalizada."""
    try:
        result = interview_engine.get_result(
            db=db,
            session_id=session_id,
            InterviewSession=persistence.InterviewSession,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _build_interview_result(result)


@v1.get('/interview/{session_id}/export')
def interview_export(
    session_id: str,
    format: str = Query("json", description="Formato: json ou pdf"),
    token: str = Depends(get_current_token),
    db=Depends(_get_db_session),
):
    """Exporta o resultado da entrevista em JSON."""
    try:
        result = interview_engine.get_result(
            db=db,
            session_id=session_id,
            InterviewSession=persistence.InterviewSession,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from fastapi.responses import JSONResponse
    return JSONResponse(content=result)


def _build_interview_result(raw: dict) -> models.InterviewResult:
    metricas_raw = raw.get("metricas", {})
    ranking_raw = raw.get("ranking", [])
    return models.InterviewResult(
        session_id=raw["session_id"],
        metricas=models.InterviewMetricas(
            esquerda_direita=metricas_raw.get("esquerda_direita", 0.0),
            confianca=metricas_raw.get("confianca", 0.0),
            consistencia=metricas_raw.get("consistencia", 0.0),
        ),
        vetor=raw.get("vetor", {}),
        ranking=[
            models.RankingItem(
                tipo=r.get("tipo", "partido"),
                nome=r["nome"],
                sigla=r.get("sigla"),
                similaridade=r["similaridade"],
                explicacao=r.get("explicacao"),
            )
            for r in ranking_raw
        ],
    )


# -------------------------------------------------------------------------
# Budget — simulador de alocação orçamentária
# -------------------------------------------------------------------------
_BUDGET_TRADEOFFS = {
    "Saúde": {
        "high": "Mais recursos em Saúde reduzem mortalidade evitável e aumentam produtividade.",
        "low": "Cortes em Saúde impactam diretamente o atendimento básico à população.",
    },
    "Educação": {
        "high": "Investimento em Educação gera retorno econômico de longo prazo.",
        "low": "Redução em Educação compromete formação de capital humano para as próximas décadas.",
    },
    "Segurança": {
        "high": "Mais recursos em Segurança Pública podem reduzir criminalidade no curto prazo.",
        "low": "Menos recursos em Segurança exigem investimento preventivo em outras áreas sociais.",
    },
    "Infraestrutura": {
        "high": "Infraestrutura amplia competitividade e reduz custos logísticos da economia.",
        "low": "Subinvestimento em Infraestrutura aumenta custos Brasil e reduz crescimento.",
    },
    "Assistência Social": {
        "high": "Assistência Social reduz extrema pobreza e estimula consumo local.",
        "low": "Cortes em Assistência Social aprofundam desigualdade e vulnerabilidade.",
    },
    "Meio Ambiente": {
        "high": "Investimento ambiental preserva ativos naturais e abre mercados sustentáveis.",
        "low": "Desinvestimento ambiental compromete acordos climáticos e imagem do Brasil no exterior.",
    },
}


@v1.post('/budget/simulate', response_model=models.BudgetSimulationResponse)
def budget_simulate(
    request: models.BudgetSimulationRequest,
    token: str = Depends(get_current_token),
) -> models.BudgetSimulationResponse:
    """Simula tradeoffs de uma alocação orçamentária entre categorias."""
    total = sum(a.percent for a in request.allocations)
    valid = abs(total - 100.0) < 0.01

    tradeoffs: List[str] = []
    for alloc in request.allocations:
        cat_tradeoffs = _BUDGET_TRADEOFFS.get(alloc.category)
        if not cat_tradeoffs:
            continue
        if alloc.percent >= 20:
            tradeoffs.append(f"[{alloc.category}] {cat_tradeoffs['high']}")
        elif alloc.percent <= 5:
            tradeoffs.append(f"[{alloc.category}] {cat_tradeoffs['low']}")

    if not valid:
        tradeoffs.insert(0, f"Atenção: a soma das alocações é {total:.1f}%, deve ser 100%.")

    return models.BudgetSimulationResponse(
        valid=valid,
        total_percent=round(total, 2),
        tradeoffs=tradeoffs,
    )


# -------------------------------------------------------------------------
# Legislative — proposições parlamentares
# -------------------------------------------------------------------------
@v1.get('/legislative/propositions', response_model=models.PropositionsResponse)
def list_propositions(
    limit: int = Query(20, ge=1, le=100),
    token: str = Depends(get_current_token),
) -> models.PropositionsResponse:
    """Lista proposições parlamentares armazenadas ou buscadas da API da Câmara."""
    snapshots = db_instance.list_camara_snapshots(endpoint="/proposicoes", limit=limit)

    items: List[models.PropositionItem] = []
    for snap in snapshots:
        try:
            payload = json.loads(snap.get("payload", "{}")) if isinstance(snap.get("payload"), str) else snap.get("payload", {})
        except Exception:
            payload = {}

        items.append(models.PropositionItem(
            id=payload.get("id") or snap.get("item_id"),
            sigla=payload.get("siglaTipo") or payload.get("sigla"),
            title=payload.get("ementa") or payload.get("titulo"),
            summary=payload.get("ementa"),
            kind=payload.get("siglaTipo"),
        ))

    return models.PropositionsResponse(items=items)


# =========================================================================
# Rotas legadas (sem prefixo /api/v1) — mantidas para compatibilidade
# =========================================================================

@app.post('/login', response_model=models.LoginResponse)
def login(request: models.LoginRequest) -> models.LoginResponse:
    """Authenticate a user by CPF and issue a bearer token (legacy endpoint)."""
    cpf = request.cpf.strip()
    if not cpf:
        raise HTTPException(status_code=400, detail='CPF must be provided')
    token = login_user(cpf)
    return models.LoginResponse(token=token)


@app.post('/events', response_model=models.EventResponse)
def create_event(request: models.EventCreateRequest, token: str = Depends(get_current_token)) -> models.EventResponse:
    start_ts = request.start_time.timestamp()
    end_ts = request.end_time.timestamp()
    if end_ts <= start_ts:
        raise HTTPException(status_code=400, detail='end_time must be greater than start_time')
    eid = db_instance.create_event(
        name=request.name,
        description=request.description,
        latitude=request.latitude,
        longitude=request.longitude,
        radius=request.radius,
        start_time=start_ts,
        end_time=end_ts,
    )
    event = db_instance.get_event(eid)
    return models.EventResponse(
        id=event['id'],
        name=event['name'],
        description=event['description'],
        latitude=event['latitude'],
        longitude=event['longitude'],
        radius=event['radius'],
        start_time=datetime.fromtimestamp(event['start_time']),
        end_time=datetime.fromtimestamp(event['end_time']),
    )


@app.get('/events', response_model=List[models.EventResponse])
def list_events() -> List[models.EventResponse]:
    events = db_instance.list_events()
    return [models.EventResponse(
        id=e['id'],
        name=e['name'],
        description=e.get('description'),
        latitude=e['latitude'],
        longitude=e['longitude'],
        radius=e['radius'],
        start_time=datetime.fromtimestamp(e['start_time']),
        end_time=datetime.fromtimestamp(e['end_time']),
    ) for e in events]


@app.post('/checkin', response_model=models.CheckinResponse)
def checkin(request: models.CheckinRequest, token: str = Depends(get_current_token)) -> models.CheckinResponse:
    timestamp = request.timestamp.timestamp() if request.timestamp else None
    try:
        leaf, root = db_instance.create_checkin(
            token=token,
            event_id=request.event_id,
            latitude=request.latitude,
            longitude=request.longitude,
            timestamp=timestamp,
            photo_hash=request.photo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return models.CheckinResponse(message='Check‑in recorded', root=root)


@app.get('/checkins/{event_id}/aggregate')
def aggregate_checkins(event_id: int) -> dict:
    try:
        result = db_instance.aggregate_checkins(event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@app.post('/voteThemes', response_model=models.VoteThemeResponse)
def create_vote_theme(request: models.VoteThemeCreateRequest, token: str = Depends(get_current_token)) -> models.VoteThemeResponse:
    open_ts = request.open_time.timestamp()
    close_ts = request.close_time.timestamp()
    if close_ts <= open_ts:
        raise HTTPException(status_code=400, detail='close_time must be greater than open_time')
    tid = db_instance.create_theme(
        question=request.question,
        options=request.options,
        open_time=open_ts,
        close_time=close_ts,
    )
    t = db_instance.get_theme(tid)
    return models.VoteThemeResponse(
        id=t['id'],
        question=t['question'],
        options=t['options'],
        open_time=datetime.fromtimestamp(t['open_time']),
        close_time=datetime.fromtimestamp(t['close_time']),
    )


@app.get('/voteThemes', response_model=List[models.VoteThemeResponse])
def list_vote_themes() -> List[models.VoteThemeResponse]:
    themes = db_instance.list_themes()
    return [models.VoteThemeResponse(
        id=t['id'],
        question=t['question'],
        options=t['options'],
        open_time=datetime.fromtimestamp(t['open_time']),
        close_time=datetime.fromtimestamp(t['close_time']),
    ) for t in themes]


@app.post('/voting/token', response_model=models.VoteTokenResponse)
def issue_vote_token(request: models.VoteTokenRequest, token: str = Depends(get_current_token)) -> models.VoteTokenResponse:
    try:
        vt = db_instance.issue_vote_token(token, request.theme_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return models.VoteTokenResponse(token=vt)


@app.post('/vote', response_model=models.VoteResponse)
def cast_vote(request: models.VoteRequest) -> models.VoteResponse:
    try:
        leaf, root = db_instance.cast_vote(
            request.token,
            request.option,
            expected_theme_id=request.theme_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return models.VoteResponse(message='Vote recorded', root=root)


@app.get('/votes/{theme_id}/aggregate')
def aggregate_votes(theme_id: int) -> dict:
    try:
        result = db_instance.aggregate_votes(theme_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@app.get('/merkleRoots')
def list_merkle_roots() -> List[dict]:
    from pathlib import Path
    import json
    from .anchor import ANCHOR_FILE
    if not ANCHOR_FILE.exists():
        return []
    try:
        return json.loads(ANCHOR_FILE.read_text())
    except Exception:
        return []


@app.get('/camara/snapshots')
def list_camara_snapshots(
    endpoint: str = Query('', description='Filtro opcional por endpoint'),
    limit: int = Query(50, ge=1, le=200),
) -> List[dict]:
    normalized_endpoint = endpoint.strip() or None
    return db_instance.list_camara_snapshots(endpoint=normalized_endpoint, limit=limit)


@app.get('/deputados/normalizados')
def list_deputados_normalizados(
    id: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=600),
) -> List[dict]:
    deputado_id = id if id > 0 else None
    rows = db_instance.list_deputados_normalizados(limit=limit, deputado_id=deputado_id)
    return [_public_deputado(row) for row in rows]


@app.get('/deputados/normalizados/{deputado_id}')
def get_deputado_normalizado(deputado_id: int) -> dict:
    rows = db_instance.list_deputados_normalizados(limit=1, deputado_id=deputado_id)
    if not rows:
        raise HTTPException(status_code=404, detail='Deputado normalizado nao encontrado')
    return _public_deputado(rows[0])


@app.get('/deputados/despesas/resumo')
def list_deputados_despesas_resumo(
    limit: int = Query(600, ge=1, le=2000),
) -> List[dict]:
    return db_instance.list_deputados_despesas_resumo(limit=limit)


@app.get('/deputados/{deputado_id}/despesas')
def list_deputado_despesas(
    deputado_id: int,
    ano: int = Query(0, ge=0),
    mes: int = Query(0, ge=0, le=12),
    limit: int = Query(200, ge=1, le=1000),
    page: int = Query(1, ge=1),
) -> List[dict]:
    ano_filter = ano if ano > 0 else None
    mes_filter = mes if mes > 0 else None
    return db_instance.list_deputado_despesas(
        deputado_id=deputado_id,
        ano=ano_filter,
        mes=mes_filter,
        limit=limit,
        page=page,
    )


@app.get('/deputados/sync-status')
def deputados_sync_status() -> dict:
    status = read_sync_status()
    now = datetime.utcnow().timestamp()
    updated_at = status.get("updated_at")
    age_seconds = None
    if isinstance(updated_at, (int, float)):
        age_seconds = max(0, int(now - float(updated_at)))
    stale = age_seconds is None or age_seconds > SYNC_STALE_SECONDS
    return {
        "ok": bool(status.get("ok")) if status else None,
        "total_normalizados": db_instance.count_deputados_normalizados(),
        "last_sync": status or None,
        "age_seconds": age_seconds,
        "stale": stale,
        "stale_after_seconds": SYNC_STALE_SECONDS,
    }


@app.get("/health")
def health() -> dict:
    db = db_instance.db_health()
    sync = deputados_sync_status()
    sync_ok = bool(sync.get("ok")) if sync.get("ok") is not None else False
    sync_fresh = not bool(sync.get("stale"))
    ok = bool(db.get("ok")) and sync_ok and sync_fresh
    return {
        "ok": ok,
        "db": db,
        "sync": {
            "ok": sync_ok,
            "stale": bool(sync.get("stale")),
            "age_seconds": sync.get("age_seconds"),
            "stale_after_seconds": sync.get("stale_after_seconds"),
            "total_normalizados": sync.get("total_normalizados"),
        },
    }


@app.get("/api/test")
def test_endpoint():
    return {"status": "Backend operational"}


# Registrar o router /api/v1 na aplicação principal
app.include_router(v1)
