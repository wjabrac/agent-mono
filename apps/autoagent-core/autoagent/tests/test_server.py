import importlib

import pytest
from fastapi.testclient import TestClient

from autoagent.types import Agent, Response
from autoagent.registry import registry, register_tool, register_agent


@pytest.fixture(scope='module')
def client():
    import autoagent.server as server
    importlib.reload(server)
    from fastapi import FastAPI
    server.app = FastAPI()
    app = server.app

    # clear registry
    registry._registry['tools'].clear()
    registry._registry['agents'].clear()
    registry._registry_info['tools'].clear()
    registry._registry_info['agents'].clear()

    @register_tool(name='echo')
    def echo(text: str):
        return text

    @register_agent(name='echo_agent', func_name='echo_agent')
    def make_agent(model: str):
        return Agent(name='echo_agent', model=model, instructions='echo', functions=[])

    # Manually create endpoints on the new app
    server.create_tool_endpoints()
    server.create_agent_endpoints()

    def fake_run(self, agent, messages, context_storage=None, **kwargs):
        return Response(messages=[{'role': 'assistant', 'content': 'ok'}], agent=agent, context_variables={})

    from unittest.mock import patch
    with patch('autoagent.core.MetaChain.run', fake_run):
        with TestClient(app) as c:
            yield c


def test_tool_endpoint(client):
    resp = client.post('/tools/echo', json={'args': {'text': 'hi'}})
    assert resp.status_code == 200
    assert resp.json()['result'] == 'hi'

    resp2 = client.post('/tools/echo', json={'args': {}})
    assert resp2.status_code == 400


def test_agent_endpoint(client):
    payload = {'model': 'test', 'query': 'hi', 'context_variables': {}}
    resp = client.post('/agents/echo_agent/run', json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body['result'] == 'ok'
    assert body['agent_name'] == 'echo_agent'
