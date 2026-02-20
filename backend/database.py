import os
import math
import secrets
import json
import logging
import time
from typing import Any, List, Tuple, Optional, Dict

from sqlalchemy.orm import Session, scoped_session
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError

from .hashing import generate_salt, hash_value
from .merkle import merkle_root
from .anchor import anchor_root

# Import the persistence module to access its symbols dynamically.
# This ensures that any runtime changes to SessionLocal (e.g., fallback to SQLite)
# are reflected in the Database class without stale imports.
from . import persistence
# Re‑export ORM components for backward compatibility within this module.
SessionLocal = persistence.SessionLocal
init_db = persistence.init_db
User = persistence.User
Event = persistence.Event
Theme = persistence.Theme
CheckIn = persistence.CheckIn
VoteToken = persistence.VoteToken
Vote = persistence.Vote
CamaraSnapshot = persistence.CamaraSnapshot
DeputadoNormalizado = persistence.DeputadoNormalizado
DeputadoDespesa = persistence.DeputadoDespesa
DeputadoDespesaSyncState = persistence.DeputadoDespesaSyncState

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Database wrapper that keeps the original in‑memory interface but delegates to SQLAlchemy ORM."""

    def __init__(self):
        # Initialise DB tables
        init_db()
        # Thread/request scoped session to avoid shared-session concurrency issues.
        self._scoped_session = scoped_session(persistence.SessionLocal)

    @property
    def db(self) -> Session:
        return self._scoped_session()

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # -----------------------------------------------------------------
    # User / login management
    # -----------------------------------------------------------------
    def register_user(self, token: str, cpf: str) -> None:
        """Associate a bearer token with a CPF (string)."""
        user = User(token=token, cpf=cpf)
        self.db.add(user)
        self._commit()
        logger.info('Registered user %s', token)

    def get_cpf(self, token: str) -> str:
        user = self.db.query(User).filter(User.token == token).first()
        if not user:
            raise KeyError('Token not found')
        return user.cpf

    def validate_token(self, token: str) -> bool:
        return self.db.query(User).filter(User.token == token).first() is not None

    # -----------------------------------------------------------------
    # Event management
    # -----------------------------------------------------------------
    def create_event(
        self,
        name: str,
        description: Optional[str],
        latitude: float,
        longitude: float,
        radius: float,
        start_time: float,
        end_time: float,
    ) -> int:
        salt = generate_salt()
        event = Event(
            name=name,
            description=description,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            start_time=start_time,
            end_time=end_time,
            salt=salt,
        )
        self.db.add(event)
        self._commit()
        self.db.refresh(event)
        logger.info('Created event %s', event.id)
        return event.id

    def get_event(self, event_id: int) -> dict:
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError('Event does not exist')
        return {
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'latitude': event.latitude,
            'longitude': event.longitude,
            'radius': event.radius,
            'start_time': event.start_time,
            'end_time': event.end_time,
        }

    def list_events(self) -> List[dict]:
        events = self.db.query(Event).all()
        return [
            {
                'id': e.id,
                'name': e.name,
                'description': e.description,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'radius': e.radius,
                'start_time': e.start_time,
                'end_time': e.end_time,
            }
            for e in events
        ]

    # -----------------------------------------------------------------
    # Theme management
    # -----------------------------------------------------------------
    def create_theme(
        self,
        question: str,
        options: List[str],
        open_time: float,
        close_time: float,
    ) -> int:
        # Store options as JSON string for simplicity
        theme = Theme(
            question=question,
            options=json.dumps(options),
            open_time=open_time,
            close_time=close_time,
        )
        self.db.add(theme)
        self._commit()
        self.db.refresh(theme)
        logger.info('Created theme %s', theme.id)
        return theme.id

    def get_theme(self, theme_id: int) -> dict:
        theme = self.db.query(Theme).filter(Theme.id == theme_id).first()
        if not theme:
            raise ValueError('Theme does not exist')
        return {
            'id': theme.id,
            'question': theme.question,
            'options': json.loads(theme.options),
            'open_time': theme.open_time,
            'close_time': theme.close_time,
        }

    def list_themes(self) -> List[dict]:
        themes = self.db.query(Theme).all()
        return [
            {
                'id': t.id,
                'question': t.question,
                'options': json.loads(t.options),
                'open_time': t.open_time,
                'close_time': t.close_time,
            }
            for t in themes
        ]

    # -----------------------------------------------------------------
    # Helper distance calculation (unchanged)
    # -----------------------------------------------------------------
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Return the great‑circle distance between two points (in meters)."""
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # -----------------------------------------------------------------
    # Check‑in handling
    # -----------------------------------------------------------------
    def create_checkin(
        self,
        token: str,
        event_id: int,
        latitude: float,
        longitude: float,
        timestamp: Optional[float],
        photo_hash: Optional[str],
    ) -> Tuple[str, str]:
        # Validate token and event existence
        user = self.db.query(User).filter(User.token == token).first()
        if not user:
            raise ValueError('Invalid token')
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError('Event does not exist')
        # Time window check
        now = timestamp if timestamp is not None else time.time()
        if not (event.start_time <= now <= event.end_time):
            raise ValueError('Check‑in outside event time window')
        # Geofence check
        distance = self._haversine(latitude, longitude, event.latitude, event.longitude)
        if distance > event.radius:
            raise ValueError('Location outside event radius')
        # Compute user hash using event salt
        user_hash = hash_value(user.cpf, event.salt)
        # Ensure unique check‑in per user per event
        existing = (
            self.db.query(CheckIn)
            .filter(CheckIn.event_id == event_id, CheckIn.user_id == user.id)
            .first()
        )
        if existing:
            raise ValueError('User already checked in')
        # Compute leaf hash
        leaf_input = f"{event_id}|{user_hash}|{int(now)}|{photo_hash or ''}"
        leaf_hash = hash_value(leaf_input, '')
        # Persist check‑in
        checkin = CheckIn(
            event_id=event_id,
            user_id=user.id,
            latitude=latitude,
            longitude=longitude,
            timestamp=now,
            photo_hash=photo_hash,
            leaf_hash=leaf_hash,
        )
        self.db.add(checkin)
        self._commit()
        # Compute Merkle root for all check‑ins of this event
        leaves = [ci.leaf_hash for ci in self.db.query(CheckIn).filter(CheckIn.event_id == event_id).all()]
        root = merkle_root(leaves)
        anchor_root(f"checkin:{event_id}", root)
        logger.info('Check‑in recorded for event %s, user %s', event_id, token)
        return leaf_hash, root

    def aggregate_checkins(self, event_id: int) -> Dict[str, int]:
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError('Event does not exist')
        count = self.db.query(CheckIn).filter(CheckIn.event_id == event_id).count()
        return {'event_id': event_id, 'count': count}

    # -----------------------------------------------------------------
    # Voting handling
    # -----------------------------------------------------------------
    def issue_vote_token(self, token: str, theme_id: int) -> str:
        user = self.db.query(User).filter(User.token == token).first()
        if not user:
            raise ValueError('Invalid token')
        theme = self.db.query(Theme).filter(Theme.id == theme_id).first()
        if not theme:
            raise ValueError('Theme does not exist')
        now = time.time()
        if not (theme.open_time <= now <= theme.close_time):
            raise ValueError('Theme is outside voting window')
        # Derive user hash using theme id as salt (mirrors previous logic)
        user_hash = hash_value(user.cpf, str(theme_id))
        # Check if a token already exists for this user/theme
        existing = (
            self.db.query(VoteToken)
            .filter(VoteToken.theme_id == theme_id, VoteToken.user_hash == user_hash)
            .first()
        )
        if existing:
            return existing.token
        vt = secrets.token_urlsafe(16)
        vote_token = VoteToken(token=vt, theme_id=theme_id, user_hash=user_hash, used=False)
        self.db.add(vote_token)
        self._commit()
        logger.info('Issued vote token %s for theme %s', vt, theme_id)
        return vt

    def cast_vote(self, vote_token: str, option: str, expected_theme_id: Optional[int] = None) -> Tuple[str, str]:
        vt = self.db.query(VoteToken).filter(VoteToken.token == vote_token).first()
        if not vt:
            raise ValueError('Invalid vote token')
        if vt.used:
            raise ValueError('Vote token already used')
        if expected_theme_id is not None and vt.theme_id != expected_theme_id:
            raise ValueError('Vote token does not belong to requested theme')
        theme = self.db.query(Theme).filter(Theme.id == vt.theme_id).first()
        if not theme:
            raise ValueError('Theme does not exist')
        now = time.time()
        if not (theme.open_time <= now <= theme.close_time):
            raise ValueError('Theme is outside voting window')
        options = json.loads(theme.options)
        if option not in options:
            raise ValueError('Invalid option for theme')
        # Mark token as used
        vt.used = True
        # Create vote record
        leaf_input = f"{theme.id}|{vote_token}|{option}"
        leaf_hash = hash_value(leaf_input, '')
        vote = Vote(
            theme_id=theme.id,
            token=vote_token,
            option=option,
            leaf_hash=leaf_hash,
        )
        self.db.add(vote)
        self._commit()
        # Compute Merkle root for all votes of this theme
        leaves = [v.leaf_hash for v in self.db.query(Vote).filter(Vote.theme_id == theme.id).all()]
        root = merkle_root(leaves)
        anchor_root(f"vote:{theme.id}", root)
        logger.info('Vote cast for theme %s, option %s', theme.id, option)
        return leaf_hash, root

    def aggregate_votes(self, theme_id: int) -> Dict[str, int]:
        theme = self.db.query(Theme).filter(Theme.id == theme_id).first()
        if not theme:
            raise ValueError('Theme does not exist')
        rows = (
            self.db.query(Vote.option, func.count(Vote.id))
            .filter(Vote.theme_id == theme_id)
            .group_by(Vote.option)
            .all()
        )
        result = {opt: 0 for opt in json.loads(theme.options)}
        for opt, cnt in rows:
            result[opt] = cnt
        return result

    # -----------------------------------------------------------------
    # Câmara ingest snapshots
    # -----------------------------------------------------------------
    def upsert_camara_snapshot(
        self,
        endpoint: str,
        item_id: str,
        source_url: str,
        payload: str,
        sort_value: Optional[str] = None,
    ) -> None:
        retries = 4
        for attempt in range(retries):
            try:
                existing = (
                    self.db.query(CamaraSnapshot)
                    .filter(CamaraSnapshot.endpoint == endpoint, CamaraSnapshot.item_id == item_id)
                    .first()
                )
                now = time.time()
                if existing:
                    existing.payload = payload
                    existing.source_url = source_url
                    existing.sort_value = sort_value
                    existing.fetched_at = now
                else:
                    self.db.add(
                        CamaraSnapshot(
                            endpoint=endpoint,
                            item_id=item_id,
                            source_url=source_url,
                            sort_value=sort_value,
                            payload=payload,
                            fetched_at=now,
                        )
                    )
                self._commit()
                return
            except OperationalError as exc:
                self.db.rollback()
                self._scoped_session.remove()
                if "database is locked" not in str(exc).lower() or attempt >= retries - 1:
                    raise
                time.sleep(0.1 * (attempt + 1))

    def camara_snapshot_counts(self) -> Dict[str, int]:
        rows = (
            self.db.query(CamaraSnapshot.endpoint, func.count(CamaraSnapshot.id))
            .group_by(CamaraSnapshot.endpoint)
            .all()
        )
        return {endpoint: count for endpoint, count in rows}

    def list_camara_snapshots(self, endpoint: Optional[str] = None, limit: int = 50) -> List[Dict[str, object]]:
        query = self.db.query(CamaraSnapshot)
        if endpoint:
            query = query.filter(CamaraSnapshot.endpoint == endpoint)
        rows = query.order_by(CamaraSnapshot.fetched_at.desc()).limit(limit).all()
        result: List[Dict[str, object]] = []
        for row in rows:
            try:
                parsed_payload = json.loads(row.payload)
            except Exception:
                parsed_payload = row.payload
            result.append(
                {
                    'id': row.id,
                    'endpoint': row.endpoint,
                    'item_id': row.item_id,
                    'source_url': row.source_url,
                    'sort_value': row.sort_value,
                    'fetched_at': row.fetched_at,
                    'payload': parsed_payload,
                }
            )
        return result

    def sync_with_external(self) -> None:
        """Sync hook used by scheduler/cron to refresh deputados data."""
        from .sync_deputados import sync_deputados

        summary = sync_deputados(delete_removed=True, with_image=False)
        logger.info('sync_with_external summary=%s', summary)

    # -----------------------------------------------------------------
    # Deputados normalizados
    # -----------------------------------------------------------------
    def upsert_deputado_normalizado(self, deputado_id: int, fields: Dict[str, object]) -> None:
        retries = 4
        for attempt in range(retries):
            try:
                row = self.db.query(DeputadoNormalizado).filter(DeputadoNormalizado.id == deputado_id).first()
                if row is None:
                    row = DeputadoNormalizado(id=deputado_id, atualizado_em=time.time())
                    self.db.add(row)
                for key, value in fields.items():
                    if hasattr(row, key):
                        setattr(row, key, value)
                row.atualizado_em = time.time()
                self._commit()
                return
            except OperationalError as exc:
                self.db.rollback()
                self._scoped_session.remove()
                if "database is locked" not in str(exc).lower() or attempt >= retries - 1:
                    raise
                time.sleep(0.1 * (attempt + 1))

    def list_deputados_normalizados(self, limit: int = 50, deputado_id: Optional[int] = None) -> List[Dict[str, object]]:
        query = self.db.query(DeputadoNormalizado)
        if deputado_id is not None:
            query = query.filter(DeputadoNormalizado.id == deputado_id)
        rows = query.order_by(DeputadoNormalizado.atualizado_em.desc()).limit(limit).all()
        result: List[Dict[str, object]] = []
        for row in rows:
            try:
                rede_social = json.loads(row.rede_social_json) if row.rede_social_json else []
            except Exception:
                rede_social = []
            result.append(
                {
                    'id': row.id,
                    'uri': row.uri,
                    'nome_civil': row.nome_civil,
                    'cpf': row.cpf,
                    'sexo': row.sexo,
                    'url_website': row.url_website,
                    'rede_social': rede_social,
                    'data_nascimento': row.data_nascimento,
                    'data_falecimento': row.data_falecimento,
                    'uf_nascimento': row.uf_nascimento,
                    'municipio_nascimento': row.municipio_nascimento,
                    'escolaridade': row.escolaridade,
                    'status_nome': row.status_nome,
                    'status_nome_eleitoral': row.status_nome_eleitoral,
                    'status_sigla_partido': row.status_sigla_partido,
                    'status_sigla_uf': row.status_sigla_uf,
                    'status_id_legislatura': row.status_id_legislatura,
                    'status_situacao': row.status_situacao,
                    'status_condicao_eleitoral': row.status_condicao_eleitoral,
                    'status_data': row.status_data,
                    'status_email': row.status_email,
                    'foto_url': row.foto_url,
                    'foto_sha256': row.foto_sha256,
                    'foto_content_type': row.foto_content_type,
                    'gabinete_nome': row.gabinete_nome,
                    'gabinete_predio': row.gabinete_predio,
                    'gabinete_sala': row.gabinete_sala,
                    'gabinete_andar': row.gabinete_andar,
                    'gabinete_telefone': row.gabinete_telefone,
                    'gabinete_email': row.gabinete_email,
                    'atualizado_em': row.atualizado_em,
                }
            )
        return result

    def count_deputados_normalizados(self) -> int:
        return int(self.db.query(func.count(DeputadoNormalizado.id)).scalar() or 0)

    # -----------------------------------------------------------------
    # Deputados despesas (2023+)
    # -----------------------------------------------------------------
    @staticmethod
    def build_despesa_dedupe_key(deputado_id: int, payload: Dict[str, Any]) -> str:
        fields = [
            str(deputado_id),
            str(payload.get("ano") or ""),
            str(payload.get("mes") or ""),
            str(payload.get("codLote") or ""),
            str(payload.get("codDocumento") or ""),
            str(payload.get("parcela") or ""),
            str(payload.get("tipoDespesa") or ""),
            str(payload.get("valorLiquido") or ""),
            str(payload.get("nomeFornecedor") or ""),
            str(payload.get("numDocumento") or ""),
            str(payload.get("numRessarcimento") or ""),
        ]
        return "|".join(fields)

    def upsert_deputado_despesa(self, deputado_id: int, payload: Dict[str, Any]) -> None:
        dedupe_key = self.build_despesa_dedupe_key(deputado_id, payload)
        retries = 4
        for attempt in range(retries):
            try:
                row = self.db.query(DeputadoDespesa).filter(DeputadoDespesa.dedupe_key == dedupe_key).first()
                now = time.time()
                if row is None:
                    row = DeputadoDespesa(
                        deputado_id=deputado_id,
                        dedupe_key=dedupe_key,
                        fetched_at=now,
                    )
                    self.db.add(row)

                row.ano = int(payload.get("ano") or 0)
                row.mes = int(payload.get("mes") or 0)
                row.data_documento = payload.get("dataDocumento")
                row.tipo_despesa = payload.get("tipoDespesa")
                row.nome_fornecedor = payload.get("nomeFornecedor")
                row.cnpj_cpf_fornecedor = payload.get("cnpjCpfFornecedor")
                row.cod_lote = int(payload["codLote"]) if payload.get("codLote") is not None else None
                row.cod_documento = str(payload["codDocumento"]) if payload.get("codDocumento") is not None else None
                row.parcela = int(payload["parcela"]) if payload.get("parcela") is not None else None
                row.tipo_documento = payload.get("tipoDocumento")
                row.num_documento = payload.get("numDocumento")
                row.num_ressarcimento = payload.get("numRessarcimento")
                row.valor_documento = float(payload["valorDocumento"]) if payload.get("valorDocumento") is not None else None
                row.valor_glosa = float(payload["valorGlosa"]) if payload.get("valorGlosa") is not None else None
                row.valor_liquido = float(payload["valorLiquido"]) if payload.get("valorLiquido") is not None else None
                row.url_documento = payload.get("urlDocumento")
                row.raw_json = json.dumps(payload, ensure_ascii=False)
                row.fetched_at = now
                self._commit()
                return
            except OperationalError as exc:
                self.db.rollback()
                self._scoped_session.remove()
                if "database is locked" not in str(exc).lower() or attempt >= retries - 1:
                    raise
                time.sleep(0.1 * (attempt + 1))

    def upsert_deputado_despesa_sync_state(
        self,
        deputado_id: int,
        ano: int,
        pagina_atual: int,
        status: str,
        erro: Optional[str] = None,
    ) -> None:
        retries = 4
        for attempt in range(retries):
            try:
                row = (
                    self.db.query(DeputadoDespesaSyncState)
                    .filter(
                        DeputadoDespesaSyncState.deputado_id == deputado_id,
                        DeputadoDespesaSyncState.ano == ano,
                    )
                    .first()
                )
                if row is None:
                    row = DeputadoDespesaSyncState(
                        deputado_id=deputado_id,
                        ano=ano,
                        pagina_atual=pagina_atual,
                        status=status,
                        erro=erro,
                        updated_at=time.time(),
                    )
                    self.db.add(row)
                else:
                    row.pagina_atual = pagina_atual
                    row.status = status
                    row.erro = erro
                    row.updated_at = time.time()
                self._commit()
                return
            except OperationalError as exc:
                self.db.rollback()
                self._scoped_session.remove()
                if "database is locked" not in str(exc).lower() or attempt >= retries - 1:
                    raise
                time.sleep(0.1 * (attempt + 1))

    def list_deputado_despesas(
        self,
        deputado_id: int,
        ano: Optional[int] = None,
        mes: Optional[int] = None,
        limit: int = 200,
        page: int = 1,
    ) -> List[Dict[str, object]]:
        query = self.db.query(DeputadoDespesa).filter(DeputadoDespesa.deputado_id == deputado_id)
        if ano is not None:
            query = query.filter(DeputadoDespesa.ano == ano)
        if mes is not None:
            query = query.filter(DeputadoDespesa.mes == mes)

        safe_page = max(1, int(page))
        safe_limit = min(1000, max(1, int(limit)))
        offset = (safe_page - 1) * safe_limit
        rows = (
            query.order_by(
                DeputadoDespesa.ano.desc(),
                DeputadoDespesa.mes.desc(),
                DeputadoDespesa.data_documento.desc(),
                DeputadoDespesa.id.desc(),
            )
            .offset(offset)
            .limit(safe_limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "deputado_id": row.deputado_id,
                "ano": row.ano,
                "mes": row.mes,
                "data_documento": row.data_documento,
                "tipo_despesa": row.tipo_despesa,
                "nome_fornecedor": row.nome_fornecedor,
                "cnpj_cpf_fornecedor": row.cnpj_cpf_fornecedor,
                "cod_lote": row.cod_lote,
                "cod_documento": row.cod_documento,
                "parcela": row.parcela,
                "tipo_documento": row.tipo_documento,
                "num_documento": row.num_documento,
                "num_ressarcimento": row.num_ressarcimento,
                "valor_documento": row.valor_documento,
                "valor_glosa": row.valor_glosa,
                "valor_liquido": row.valor_liquido,
                "url_documento": row.url_documento,
            }
            for row in rows
        ]

    def list_deputados_despesas_resumo(self, limit: int = 600) -> List[Dict[str, object]]:
        safe_limit = min(2000, max(1, int(limit)))
        rows = (
            self.db.query(
                DeputadoDespesa.deputado_id,
                DeputadoDespesa.ano,
                DeputadoDespesa.mes,
                func.sum(DeputadoDespesa.valor_liquido).label("total_liquido"),
            )
            .group_by(DeputadoDespesa.deputado_id, DeputadoDespesa.ano, DeputadoDespesa.mes)
            .all()
        )
        by_dep: Dict[int, List[Tuple[int, int, float]]] = {}
        for dep_id, ano, mes, total in rows:
            if dep_id is None or ano is None or mes is None:
                continue
            by_dep.setdefault(int(dep_id), []).append((int(ano), int(mes), float(total or 0.0)))

        result: List[Dict[str, object]] = []
        for dep_id in sorted(by_dep.keys())[:safe_limit]:
            ordered = sorted(by_dep[dep_id], key=lambda item: (item[0], item[1]), reverse=True)
            latest = ordered[0]
            last_three = ordered[:3]
            avg_three = sum(item[2] for item in last_three) / max(1, len(last_three))
            result.append(
                {
                    "id": dep_id,
                    "latest_year": latest[0],
                    "latest_month": latest[1],
                    "latest_total_liquido": round(latest[2], 2),
                    "avg_last_3_months_liquido": round(avg_three, 2),
                    "months_considered": len(last_three),
                }
            )
        return result

    def count_deputado_despesas(self, deputado_id: Optional[int] = None, ano_min: Optional[int] = None) -> int:
        query = self.db.query(func.count(DeputadoDespesa.id))
        if deputado_id is not None:
            query = query.filter(DeputadoDespesa.deputado_id == deputado_id)
        if ano_min is not None:
            query = query.filter(DeputadoDespesa.ano >= ano_min)
        return int(query.scalar() or 0)

    def db_health(self) -> Dict[str, object]:
        try:
            self.db.execute(text("SELECT 1"))
            return {"ok": True}
        except Exception as exc:
            self.db.rollback()
            return {"ok": False, "error": str(exc)}

# Instantiate a singleton database for the API
db_instance = Database()
