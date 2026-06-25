"""Tool registry for the agent."""

from agent.tools.retrieval import search_knowledge, search_user_memory, save_to_memory
from agent.tools.api import (
    search_structures,
    get_structure_details,
    get_risk_explanation,
    get_inspection_schedule,
    get_top_risk_objects,
    get_objects_without_coordinates,
    get_district_report,
    get_repair_queue,
)


def get_tools() -> list:
    """Get all available tools.

    Returns:
        List of LangChain tools.
    """
    return [
        search_knowledge,
        search_user_memory,
        save_to_memory,
        search_structures,
        get_structure_details,
        get_risk_explanation,
        get_inspection_schedule,
        get_top_risk_objects,
        get_objects_without_coordinates,
        get_district_report,
        get_repair_queue,
    ]
