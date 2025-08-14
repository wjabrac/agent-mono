import json
from autoagent.util import function_to_json, merge_chunk


def sample_func(a: int, b: str) -> None:
    """Sample function"""
    return None


def test_function_to_json_basic():
    info = function_to_json(sample_func)
    func_info = info['function']
    assert func_info['name'] == 'sample_func'
    params = func_info['parameters']['properties']
    assert params['a']['type'] == 'integer'
    assert params['b']['type'] == 'string'
    assert set(func_info['parameters']['required']) == {'a', 'b'}


def test_merge_chunk_with_tool_calls():
    message = {
        'content': '',
        'tool_calls': {
            0: {
                'function': {'arguments': '', 'name': ''},
                'id': '',
                'type': ''
            }
        }
    }
    delta = {
        'content': 'Hello',
        'tool_calls': [
            {
                'index': 0,
                'function': {'arguments': '{}', 'name': 'do'},
                'id': '1',
                'type': 'tool'
            }
        ]
    }
    merge_chunk(message, delta)
    assert message['content'] == 'Hello'
    assert message['tool_calls'][0]['function']['name'] == 'do'
    assert message['tool_calls'][0]['id'] == '1'
