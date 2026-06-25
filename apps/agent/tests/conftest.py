"""Test configuration."""

import pytest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_vector_store():
    """Mock the vector store."""
    with pytest.MonkeyPatch.context() as m:
        mock_store = MagicMock()
        # Patch where it is used in the tools module
        m.setattr("agent.tools.retrieval.get_vector_store", lambda: mock_store)
        yield mock_store
