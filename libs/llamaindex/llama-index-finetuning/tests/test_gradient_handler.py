import pathlib
import importlib.util
from types import SimpleNamespace

base_path = pathlib.Path(__file__).resolve().parents[1] / "llama_index" / "finetuning" / "callbacks" / "finetuning_handler.py"
spec = importlib.util.spec_from_file_location("finetuning_handler", base_path)
finetuning_handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finetuning_handler)  # type: ignore
GradientAIFineTuningHandler = finetuning_handler.GradientAIFineTuningHandler


def test_custom_serializer(tmp_path):
    handler = GradientAIFineTuningHandler(serializer=lambda msgs: "SERIALIZED")
    handler._finetuning_events["1"] = [
        SimpleNamespace(role="user", text="hi"),
        SimpleNamespace(role="assistant", text="there"),
    ]

    path = tmp_path / "out.jsonl"
    handler.save_finetuning_events(str(path))

    assert path.read_text().strip() == '{"inputs": "SERIALIZED"}'
