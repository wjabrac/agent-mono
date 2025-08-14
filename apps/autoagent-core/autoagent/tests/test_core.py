import json
from types import SimpleNamespace

import pytest
from tenacity import Retrying, stop_after_attempt, wait_none, retry_if_exception
from litellm.exceptions import APIError
from litellm.types.utils import Function, ChatCompletionMessageToolCall

from autoagent.core import MetaChain, should_retry_error
from autoagent.types import Agent, Result


def test_handle_tool_calls_executes_function_and_updates_context(mc, sample_agent):
    tool_call = ChatCompletionMessageToolCall(
        id='1',
        type='tool',
        function=Function(name='add', arguments=json.dumps({'a': 1, 'b': 2}))
    )
    response = mc.handle_tool_calls([tool_call], sample_agent.functions, {}, debug=False)
    assert response.messages[0]['content'] == '3'
    assert response.context_variables['sum'] == 3


def test_get_chat_completion_retries_on_api_error(monkeypatch):
    agent = Agent(name='test', model='gpt-4o', instructions='hi', functions=[])
    call_count = {'n': 0}

    class DummyCompletion:
        def __init__(self):
            self.choices = [SimpleNamespace(message=SimpleNamespace(content='ok'))]

    def fake_completion(**kwargs):
        call_count['n'] += 1
        if call_count['n'] < 2:
            raise APIError(500, 'boom', 'test', 'gpt-4o')
        return DummyCompletion()

    monkeypatch.setattr('autoagent.core.completion', fake_completion)
    monkeypatch.setattr('autoagent.core.litellm.supports_function_calling', lambda model: True)

    mc = MetaChain()
    retryer = Retrying(stop=stop_after_attempt(2), wait=wait_none(), retry=retry_if_exception(should_retry_error), reraise=True)
    completion = retryer(mc.get_chat_completion, agent=agent, history=[], context_variables={}, model_override=None, stream=False, debug=False)
    assert call_count['n'] == 2
    assert completion.choices[0].message.content == 'ok'
