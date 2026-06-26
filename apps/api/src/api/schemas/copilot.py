"""Pydantic schemas for AI copilot chat endpoint (AI-04).

Provides:
- CopilotMessage: single message in conversation history
- CopilotRequest: request body for POST /copilot/chat
- EvidenceItem: evidence source returned by hybrid search
- CopilotResponse: response with guardrails (requires_confirmation, confirmation_type)
"""

from pydantic import BaseModel, Field


class CopilotMessage(BaseModel):
    """Single message in conversation history."""

    role: str = Field(..., description='Message role: "user" or "assistant"')
    content: str = Field(..., description="Message text")


class CopilotRequest(BaseModel):
    """Request body for POST /copilot/chat — AI copilot with guardrails."""

    message: str = Field(..., description="User query about hydraulic structures", min_length=1)
    conversation_id: str | None = Field(
        None,
        description="Conversation ID for continuity (new conversation if None)",
    )
    context: dict | None = Field(
        None,
        description="Optional context: structure_id, filters, etc.",
    )


class EvidenceItem(BaseModel):
    """Evidence source retrieved by hybrid search."""

    source_type: str = Field(
        ...,
        description='Source entity type: "structure" | "inspection" | "document" | "risk_assessment"',
    )
    source_id: str = Field(..., description="UUID of the source record")
    relevance: float = Field(
        ...,
        description="Relevance score 0-1",
        ge=0.0,
        le=1.0,
    )
    snippet: str = Field("", description="Text snippet from the matching content")


class CopilotResponse(BaseModel):
    """Response from AI copilot with engineering decision guardrails (AI-04).

    requires_confirmation=True when the response involves an engineering decision
    that requires human confirmation per AI-04 policy.
    """

    message: str = Field(..., description="Copilot response text")
    requires_confirmation: bool = Field(
        ...,
        description="True if response suggests an engineering decision requiring human confirmation",
    )
    confirmation_type: str | None = Field(
        None,
        description='Type of decision: "condition_assignment" | "risk_override" | "inspection_conclusion" | None',
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence sources backing the response",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable next steps for the user",
    )
    conversation_id: str = Field(
        ...,
        description="Conversation ID for continuity",
    )
