"""Normalize deputado snapshots into a relational table."""

import argparse
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen

from backend.database import db_instance


def download_image(url: str, timeout: int = 20) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    req = Request(url, headers={"User-Agent": "br-manifest-app/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type")
            digest = hashlib.sha256(data).hexdigest() if data else None
            return data, content_type, digest
    except Exception:
        return None, None, None


def map_deputado_payload(payload: Dict[str, Any], with_image: bool) -> Dict[str, object]:
    status = payload.get("ultimoStatus") or {}
    gabinete = status.get("gabinete") or {}
    rede_social = payload.get("redeSocial") or []
    foto_url = status.get("urlFoto")
    foto_bytes: Optional[bytes] = None
    foto_content_type: Optional[str] = None
    foto_sha256: Optional[str] = None

    if with_image and foto_url:
        foto_bytes, foto_content_type, foto_sha256 = download_image(str(foto_url))

    return {
        "uri": payload.get("uri"),
        "nome_civil": payload.get("nomeCivil"),
        "cpf": payload.get("cpf"),
        "sexo": payload.get("sexo"),
        "url_website": payload.get("urlWebsite"),
        "rede_social_json": json.dumps(rede_social, ensure_ascii=False),
        "data_nascimento": payload.get("dataNascimento"),
        "data_falecimento": payload.get("dataFalecimento"),
        "uf_nascimento": payload.get("ufNascimento"),
        "municipio_nascimento": payload.get("municipioNascimento"),
        "escolaridade": payload.get("escolaridade"),
        "status_nome": status.get("nome"),
        "status_nome_eleitoral": status.get("nomeEleitoral"),
        "status_sigla_partido": status.get("siglaPartido"),
        "status_sigla_uf": status.get("siglaUf"),
        "status_id_legislatura": status.get("idLegislatura"),
        "status_situacao": status.get("situacao"),
        "status_condicao_eleitoral": status.get("condicaoEleitoral"),
        "status_data": status.get("data"),
        "status_email": status.get("email"),
        "foto_url": foto_url,
        "foto_bytes": foto_bytes,
        "foto_sha256": foto_sha256,
        "foto_content_type": foto_content_type,
        "gabinete_nome": gabinete.get("nome"),
        "gabinete_predio": gabinete.get("predio"),
        "gabinete_sala": gabinete.get("sala"),
        "gabinete_andar": gabinete.get("andar"),
        "gabinete_telefone": gabinete.get("telefone"),
        "gabinete_email": gabinete.get("email"),
    }


def choose_snapshots(limit: int, deputado_id: Optional[int]) -> List[Dict[str, object]]:
    rows = db_instance.list_camara_snapshots(endpoint="/deputados/{id}", limit=max(limit, 513))
    if deputado_id is not None:
        return [row for row in rows if str(row.get("item_id")) == str(deputado_id)]
    return rows[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize deputado snapshots")
    parser.add_argument("--limit", type=int, default=1, help="Quantidade maxima de deputados a normalizar")
    parser.add_argument("--deputado-id", type=int, default=None, help="Forca normalizacao de um deputado especifico")
    parser.add_argument("--no-image", action="store_true", help="Nao baixar imagem")
    args = parser.parse_args()

    snapshots = choose_snapshots(limit=args.limit, deputado_id=args.deputado_id)
    if not snapshots:
        print("Nenhum snapshot de deputado encontrado para normalizar.")
        return

    total = 0
    with_image = not args.no_image
    for row in snapshots[: args.limit]:
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        dep_id = payload.get("id")
        if dep_id is None:
            continue
        mapped = map_deputado_payload(payload, with_image=with_image)
        db_instance.upsert_deputado_normalizado(int(dep_id), mapped)
        print(f"normalizado deputado {dep_id} (imagem={'sim' if mapped.get('foto_bytes') else 'nao'})")
        total += 1

    print(f"Total normalizado: {total}")


if __name__ == "__main__":
    main()
