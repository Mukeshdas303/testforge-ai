import asyncio
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.models.schemas import (TestCaseRequest, GenerationResult, ExportResponse, TestCaseType)
from app.services.llm_service    import llm_service
from app.services.prompt_service  import PROMPT_BUILDERS
from app.services.parser_service  import parser_service
from app.services.export_service  import export_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Test Generation"])

# In-memory store: session_id → GenerationResult
# In production, replace with Redis or a DB.
_session_store: dict[str, GenerationResult] = {}


async def _generate_for_type(
    case_type: TestCaseType,
    ui_description: str,
    requirements: str,
    max_per_type: int
) -> list:
    """Run a single prompt pipeline for one test case type."""
    builder = PROMPT_BUILDERS[case_type]
    system_prompt, user_prompt = builder(ui_description, requirements, max_per_type)

    logger.info(f"Calling LLM for {case_type.value} test cases...")
    raw_output = await llm_service.generate(
        prompt        = user_prompt,
        system_prompt = system_prompt
    )

    cases = parser_service.parse(raw_output, case_type)
    logger.info(f"Parsed {len(cases)} {case_type.value} test cases")
    return cases


@router.post("/generate-tests", response_model=GenerationResult)
async def generate_test_cases(request: TestCaseRequest):
    """
    Generate positive, negative, and/or edge-case test scenarios
    from a UI description and product requirements using Ollama phi3.
    """
    # Verify Ollama is reachable before running
    if not await llm_service.health_check():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve"
        )

    # Run all requested types concurrently (asyncio.gather)
    tasks = [
        _generate_for_type(
            case_type      = t,
            ui_description = request.ui_description,
            requirements   = request.product_requirements,
            max_per_type   = request.max_per_type or 5
        )
        for t in request.test_types
    ]

    results_per_type = await asyncio.gather(*tasks, return_exceptions=True)

    all_test_cases = []
    for i, result in enumerate(results_per_type):
        if isinstance(result, Exception):
            logger.error(f"Generation failed for {request.test_types[i]}: {result}")
        else:
            all_test_cases.extend(result)

    if not all_test_cases:
        raise HTTPException(
            status_code=500,
            detail="LLM failed to generate any valid test cases. Check Ollama logs."
        )

    generation = GenerationResult(
        ui_description       = request.ui_description,
        product_requirements = request.product_requirements,
        test_cases           = all_test_cases,
    ).compute_counts()

    _session_store[generation.session_id] = generation
    return generation


@router.get("/export/{session_id}", response_model=ExportResponse)
async def export_test_cases(
    session_id: str,
    format: str = Query(default="json", pattern="^(json|csv)$")
):
    """
    Export a previously generated test suite as JSON or CSV.
    """
    result = _session_store.get(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if format == "csv":
        return export_service.to_csv(result)
    return export_service.to_json(result)


@router.get("/download/{session_id}")
async def download_test_cases(
    session_id: str,
    format: str = Query(default="json", pattern="^(json|csv)$")
):
    """Return raw file content as plain text (ready for file download)."""
    result = _session_store.get(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    export = export_service.to_csv(result) if format == "csv" else export_service.to_json(result)

    media_type = "text/csv" if format == "csv" else "application/json"
    return PlainTextResponse(
        content    = export.content,
        media_type = media_type,
        headers    = {"Content-Disposition": f'attachment; filename="{export.filename}"'}
    )


@router.get("/health")
async def health():
    ollama_ok = await llm_service.health_check()
    return {
        "api":    "ok",
        "ollama": "ok" if ollama_ok else "unreachable",
        "model":  llm_service.model,
    }