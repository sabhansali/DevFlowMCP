from pathlib import Path

import pytest


@pytest.fixture
def sample_project() -> str:
    return str(Path(__file__).parents[1] / "sample_quality_project")
