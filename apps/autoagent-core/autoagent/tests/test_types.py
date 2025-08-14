from autoagent.types import Agent, Response, Result


def test_agent_defaults():
    agent = Agent()
    assert agent.model == 'gpt-4o'
    assert 'helpful agent' in agent.instructions


def test_response_instances_isolated():
    r1 = Response()
    r2 = Response()
    r1.messages.append({'role': 'assistant', 'content': 'hi'})
    assert r2.messages == []


def test_result_fields():
    res = Result(value='ok', context_variables={'a': 1})
    assert res.value == 'ok'
    assert res.context_variables['a'] == 1
