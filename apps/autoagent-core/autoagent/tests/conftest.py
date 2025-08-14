import os
import sys
import types

# Ensure package path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Stub heavy optional modules that may not be installed
sys.modules.setdefault('autoagent.tools', types.ModuleType('tools'))
sys.modules.setdefault('autoagent.agents', types.ModuleType('agents'))
sys.modules.setdefault('autoagent.workflows', types.ModuleType('workflows'))

import pytest
from autoagent.types import Agent, Result
from autoagent.core import MetaChain


@pytest.fixture
def sample_tool():
    def add(a: int, b: int, context_variables: dict | None = None):
        return Result(value=str(a + b), context_variables={'sum': a + b})
    return add


@pytest.fixture
def sample_agent(sample_tool):
    return Agent(
        name='adder',
        model='gpt-4o',
        instructions='Add numbers',
        functions=[sample_tool],
    )


@pytest.fixture
def mc():
    return MetaChain()
