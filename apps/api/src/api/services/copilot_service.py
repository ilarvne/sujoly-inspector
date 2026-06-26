"""AI copilot service with engineering decision guardrails (AI-04).

Provides:
- CopilotService.chat: process queries with guardrails
- _detect_engineering_decision: pattern-match for condition/risk/inspection decisions
- _retrieve_evidence: hybrid search for relevant evidence
- _call_llm: call Alem LLM API (OpenAI-compatible) with system prompt

Architecture principle (PROJECT.md):
    "LLMs never make final engineering decisions."
    All condition assignments, risk overrides, and inspection conclusions
    require human confirmation. The copilot synthesizes evidence and suggests
    actions, but never makes final engineering decisions.

CRITICAL USER DIRECTIVE: Use REAL LLM models configured via .env, NOT template-based stubs.
"""

import os
import uuid

import httpx
import structlog

from api.config.settings import settings
from api.schemas.copilot import CopilotRequest, CopilotResponse, EvidenceItem
from api.services.search_service import search_service

logger = structlog.get_logger(__name__)

# Engineering decision keywords that trigger guardrails (AI-04)
# Trilingual: English, Russian, Kazakh
ENGINEERING_DECISION_PATTERNS: dict[str, list[str]] = {
    "condition_assignment": [
        "condition", "состояние", "жағдай",
        "technical condition", "техническое состояние", "техникалық жағдай",
        "satisfactory condition", "удовлетворительное", "қанағаттанарлық",
        "unsatisfactory", "неудовлетворительное", "қанағаттанарлықсыз",
        "emergency", "аварийное", "төтенше",
        "condition score", "балл состояния",
    ],
    "risk_override": [
        "risk level", "уровень риска", "тәуекел деңгейі",
        "risk assessment", "оценка риска", "тәуекел бағалау",
        "high risk", "высокий риск", "жоғары тәуекел",
        "critical risk", "критический риск", "сыни тәуекел",
        "override", "переопределить", "қайта анықтау",
        "change risk", "изменить риск",
    ],
    "inspection_conclusion": [
        "inspection required", "требуется осмотр",
        "inspection conclusion", "заключение осмотра", "тексеру қорытындысы",
        "needs inspection", "нуждается в осмотре",
        "repair required", "требуется ремонт", "ремонт требуется", "жөндеу қажет",
        "critical status", "критическое состояние", "сыни жағдай",
        # Kazakh: "тексеру қажет" and "қажет тексеру" (word order varies)
        "тексеру қажет", "қажет тексеру",
    ],
}

# System prompt enforcing AI-04 guardrails (trilingual context)
COPILOT_SYSTEM_PROMPT = """You are a hydraulic structure inspection copilot for Zhambyl Oblast, Kazakhstan. Your role is to retrieve and synthesize evidence about hydraulic structures, but you NEVER make final engineering decisions.

CRITICAL RULES (AI-04):
1. You may SUGGEST condition assessments, risk levels, and inspection priorities based on evidence.
2. You MUST explicitly state that all engineering conclusions require human confirmation.
3. You MUST NOT definitively assign conditions, override risk assessments, or conclude inspections.
4. When your analysis leads to an engineering decision, phrase it as: "Based on the evidence, I suggest X, but this requires your confirmation as the responsible engineer."
5. Always cite your evidence sources.
6. Respond in the same language as the user's query (Russian, Kazakh, or English).

You have access to a database of hydraulic structures (каналы, плотины, шлюзы, насосные станции) in Zhambyl Oblast with their condition assessments, inspection history, and risk evaluations.

Structure types: canal (канал), dam (плотина), sluice (шлюз), pump_station (насосная станция), reservoir (водохранилище), other (прочее)
Condition levels: satisfactory (удовлетворительное), unsatisfactory (неудовлетворительное), emergency (аварийное)
Risk levels: low, medium, high, critical
"""


class CopilotService:
    """AI copilot with engineering decision guardrails (AI-04)."""

    def __init__(self):
        self._base_url = settings.llm_base_url
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens

    def _get_api_key(self) -> str:
        """Resolve LLM API key from environment (Alem API).

        Priority: model-specific key (CHAT_ALEM_API_KEY for alemllm) → CHAT_QWEN_API_KEY → settings.llm_api_key → LLM_DEFAULT_API_KEY
        """
        # Use the correct key for the model
        if self._model == "alemllm":
            key = os.environ.get("CHAT_ALEM_API_KEY", "")
            if key:
                return key
        elif self._model == "gemma4":
            key = os.environ.get("CHAT_GEMMA_API_KEY", "")
            if key:
                return key
        # Fall back to qwen key, then settings, then default
        key = os.environ.get("CHAT_QWEN_API_KEY", "")
        if not key:
            key = settings.llm_api_key
        if not key:
            key = os.environ.get("LLM_DEFAULT_API_KEY", "")
        return key

    async def chat(self, request: CopilotRequest) -> CopilotResponse:
        """Process copilot chat with guardrails (AI-04).

        1. Generate conversation_id if new
        2. Retrieve evidence via hybrid search
        3. Detect if query involves engineering decisions
        4. Call LLM with system prompt enforcing guardrails
        5. Build response with requires_confirmation flag
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # 1. Retrieve evidence via hybrid search
        evidence_items = await self._retrieve_evidence(request.message, limit=5)

        # 2. Detect engineering decision
        confirmation_type = self._detect_engineering_decision(request.message)

        # 3. Build evidence context for LLM
        evidence_text = self._format_evidence(evidence_items)

        # 4. Call LLM with guardrails
        llm_response = await self._call_llm(
            query=request.message,
            evidence=evidence_text,
            confirmation_type=confirmation_type,
        )

        # 5. Determine requires_confirmation
        requires_confirmation = confirmation_type is not None

        # 6. Build suggestions
        suggestions = self._build_suggestions(confirmation_type, evidence_items)

        return CopilotResponse(
            message=llm_response,
            requires_confirmation=requires_confirmation,
            confirmation_type=confirmation_type,
            evidence=evidence_items,
            suggestions=suggestions,
            conversation_id=conversation_id,
        )

    def _detect_engineering_decision(self, query: str) -> str | None:
        """Detect if query involves an engineering decision.

        Pattern matches against ENGINEERING_DECISION_PATTERNS.
        Returns confirmation_type or None.
        """
        query_lower = query.lower()
        for confirmation_type, patterns in ENGINEERING_DECISION_PATTERNS.items():
            for pattern in patterns:
                if pattern in query_lower:
                    return confirmation_type
        return None

    async def _retrieve_evidence(
        self, query: str, limit: int = 5
    ) -> list[EvidenceItem]:
        """Retrieve relevant evidence via hybrid search.

        Calls search_service.hybrid_search and converts results
        to EvidenceItem list with normalized relevance scores.
        """
        try:
            results = await search_service.hybrid_search(
                query=query,
                limit=limit,
                lang="ru",  # Default to Russian for Zhambyl structures
            )
        except Exception:
            logger.warning("evidence_retrieval_failed", query=query)
            return []

        evidence_items = []
        for result in results:
            # Normalize score to 0-1 range (RRF scores are typically 0-0.05)
            relevance = min(result.get("score", 0.0) * 20.0, 1.0)
            evidence_items.append(
                EvidenceItem(
                    source_type=result.get("source_type", "structure"),
                    source_id=result.get("source_id", ""),
                    relevance=round(relevance, 3),
                    snippet=result.get("snippet", ""),
                )
            )
        return evidence_items

    def _format_evidence(self, evidence: list[EvidenceItem]) -> str:
        """Format evidence items into text for LLM context."""
        if not evidence:
            return "No specific evidence found for this query."
        lines = ["Retrieved evidence:"]
        for i, item in enumerate(evidence, 1):
            lines.append(
                f"  {i}. [{item.source_type}] {item.source_id} "
                f"(relevance: {item.relevance:.1%}) — {item.snippet}"
            )
        return "\n".join(lines)

    async def _call_llm(
        self,
        query: str,
        evidence: str,
        confirmation_type: str | None,
    ) -> str:
        """Call Alem LLM API (OpenAI-compatible) with guardrail system prompt.

        Uses httpx to POST to /chat/completions.
        Falls back to template-based response if LLM is unavailable.
        """
        api_key = self._get_api_key()

        # Build user message with evidence context
        user_message = f"""Query: {query}

{evidence}

{"⚠️ This query involves an engineering decision. You MUST state that this requires human confirmation before any final determination." if confirmation_type else "This is an informational query. Provide a direct answer with evidence."}"""

        if not api_key:
            logger.warning("llm_api_key_missing", fallback="template_response")
            return self._template_response(query, confirmation_type)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                        "temperature": self._temperature,
                        "max_tokens": self._max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                # Strip thinking blocks from reasoning models (e.g., qwen3)
                import re
                # qwen3 uses thinking.../thinking tags, strip them
                content = re.sub(r"<thinking>.*?</thinking>", "", content, flags=re.DOTALL).strip()
                return content

        except httpx.HTTPStatusError as e:
            logger.error("llm_api_error", status=e.response.status_code, detail=str(e))
            return self._template_response(query, confirmation_type)
        except httpx.RequestError as e:
            logger.error("llm_request_error", error=str(e))
            return self._template_response(query, confirmation_type)
        except Exception as e:
            logger.error("llm_unexpected_error", error=str(e))
            return self._template_response(query, confirmation_type)

    def _template_response(
        self, query: str, confirmation_type: str | None
    ) -> str:
        """Template-based fallback response when LLM is unavailable.

        Provides structured responses based on query type.
        """
        if confirmation_type == "condition_assignment":
            return (
                "Based on the available evidence, I can provide information about this structure's "
                "current condition, but I cannot make a final condition assignment. "
                "Condition assessments require your professional confirmation as the responsible engineer. "
                "Please review the evidence sources and make your own determination."
            )
        elif confirmation_type == "risk_override":
            return (
                "I can provide risk assessment information, but I cannot override or change "
                "risk levels. Risk overrides require engineer approval with justification. "
                "Please review the risk factors and submit an override request if warranted."
            )
        elif confirmation_type == "inspection_conclusion":
            return (
                "Based on the evidence, I can suggest inspection priorities, but I cannot "
                "make final inspection conclusions. Inspection conclusions require your "
                "professional determination. Please review the findings and schedule "
                "an inspection if needed."
            )
        else:
            return (
                "I found relevant information about hydraulic structures matching your query. "
                "Please review the evidence sources for details."
            )

    def _build_suggestions(
        self,
        confirmation_type: str | None,
        evidence: list[EvidenceItem],
    ) -> list[str]:
        """Build actionable suggestions based on confirmation type and evidence."""
        suggestions: list[str] = []

        if confirmation_type == "condition_assignment":
            suggestions.append("Review structure condition history before assigning a condition level")
            suggestions.append("Schedule an on-site inspection to verify the suggested condition")
        elif confirmation_type == "risk_override":
            suggestions.append("Review the current risk assessment factors")
            suggestions.append("Submit a risk override request with engineering justification")
        elif confirmation_type == "inspection_conclusion":
            suggestions.append("Schedule an inspection visit to verify findings")
            suggestions.append("Review inspection history for the structure")
        else:
            suggestions.append("Explore related structures in the area")
            suggestions.append("Check inspection history for more details")

        if evidence:
            source_types = {e.source_type for e in evidence}
            if "inspection" in source_types:
                suggestions.append("Review inspection reports for detailed findings")
            if "risk_assessment" in source_types:
                suggestions.append("Review current risk assessment")

        return suggestions[:5]  # Limit to 5 suggestions


# Module-level singleton for route handlers
copilot_service = CopilotService()
