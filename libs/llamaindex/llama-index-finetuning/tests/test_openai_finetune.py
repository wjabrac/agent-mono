import os
import pathlib
import importlib.util
from unittest.mock import MagicMock

base_path = pathlib.Path(__file__).resolve().parents[1] / "llama_index" / "finetuning" / "openai" / "base.py"
spec = importlib.util.spec_from_file_location("openai_base", base_path)
openai_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openai_base)  # type: ignore
OpenAIFinetuneEngine = openai_base.OpenAIFinetuneEngine


def test_finetune_uses_filename(tmp_path):
    data_file = tmp_path / "data.jsonl"
    data_file.write_text('{"messages": []}\n')

    engine = OpenAIFinetuneEngine(
        base_model="gpt-3.5-turbo", data_path=str(data_file), validate_json=False
    )

    client = MagicMock()
    client.files.create.return_value.id = "file1"
    client.fine_tuning.jobs.create.return_value = MagicMock(id="job1")
    engine._client = client

    engine.finetune()

    assert client.files.create.called
    _, kwargs = client.files.create.call_args
    assert kwargs["filename"] == data_file.name
    assert client.fine_tuning.jobs.create.call_count == 1
