"""AI copilot chat endpoint with engineering decision guardrails (AI-04).

Provides:
- POST /copilot/chat: process natural language queries about hydraulic structures
  with guardrails that prevent the AI from making final engineering decisions.

The copilot retrieves and synthesizes evidence but NEVER makes final engineering
decisions. All condition assignments, risk overrides, and inspection conclusions
require human confirmation.
"""

from fastapi import APIRouter

from api.schemas.copilot import CopilotRequest, CopilotResponse
from api.services.copilot_service import copilot_service

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


@router.post("/chat", response_model=CopilotResponse)
async def copilot_chat(request: CopilotRequest) -> CopilotResponse:
    """AI copilot chat endpoint with guardrails (AI-04).

    The copilot retrieves and synthesizes evidence but never makes
    final engineering decisions. All condition assignments,
    risk overrides, and inspection conclusions require human confirmation.

    When the query involves an engineering decision:
    - requires_confirmation=True
    - confirmation_type is set (condition_assignment, risk_override, inspection_conclusion)
    - Response includes explicit statement that human confirmation is required

    When the query is informational only:
    - requires_confirmation=False
    - Direct answer with evidence sources
    """
    return await copilot_service.chat(request)
