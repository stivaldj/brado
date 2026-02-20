from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from ...political_interview.schemas import (
    AnswerRequest,
    AnswerResponse,
    BudgetSimulationRequest,
    BudgetSimulationResponse,
    InterviewResultResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    LegislativeQueryResponse,
    UpsertLegislatorProfile,
    UpsertPartyProfile,
)
from ...political_interview.service import InterviewService
from ...security.api_v1_auth import enforce_session_rate_limit, require_api_v1_token

router = APIRouter(prefix="/api/v1", tags=["political-interview"], dependencies=[Depends(require_api_v1_token)])
service = InterviewService()


@router.post("/interview/start", response_model=InterviewStartResponse)
def start_interview(request: InterviewStartRequest) -> dict:
    return service.start_session(user_id=request.user_id, metadata=request.metadata)


@router.post("/interview/{session_id}/answer", response_model=AnswerResponse)
def answer_interview(session_id: str, request: AnswerRequest, raw_request: Request) -> dict:
    try:
        enforce_session_rate_limit(raw_request, session_id)
        return service.submit_answer(session_id=session_id, question_id=request.question_id, answer=request.answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/interview/{session_id}/finish", response_model=InterviewResultResponse)
def finish_interview(session_id: str, raw_request: Request) -> dict:
    try:
        enforce_session_rate_limit(raw_request, session_id)
        return service.finish_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/interview/{session_id}/result", response_model=InterviewResultResponse)
def get_interview_result(session_id: str, raw_request: Request) -> dict:
    try:
        enforce_session_rate_limit(raw_request, session_id)
        return service.get_result(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/interview/{session_id}/export", response_model=None)
def export_interview_result(
    session_id: str,
    raw_request: Request,
    format: str = Query(default="json", pattern="^(json|pdf)$"),
) -> Response:
    try:
        enforce_session_rate_limit(raw_request, session_id)
        if format == "pdf":
            content = service.export_result_pdf(session_id)
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="interview-{session_id}.pdf"'},
            )
        return JSONResponse(content=service.export_result_json(session_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/budget/simulate", response_model=BudgetSimulationResponse)
def simulate_budget(request: BudgetSimulationRequest) -> dict:
    allocations = [item.model_dump() for item in request.allocations]
    return service.run_budget_simulation(allocations)


@router.get("/legislative/propositions", response_model=LegislativeQueryResponse)
def list_propositions(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return service.query_legislative_items(limit=limit)


@router.post("/profiles/legislators")
def upsert_legislator_profiles(payload: list[UpsertLegislatorProfile]) -> dict:
    return service.upsert_legislator_profiles([item.model_dump() for item in payload])


@router.post("/profiles/parties")
def upsert_party_profiles(payload: list[UpsertPartyProfile]) -> dict:
    return service.upsert_party_profiles([item.model_dump() for item in payload])
