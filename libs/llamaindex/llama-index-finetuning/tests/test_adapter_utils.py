import pathlib
import sys

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

torch = pytest.importorskip("torch")
from torch.utils.data import DataLoader, TensorDataset

from llama_index.finetuning.embeddings.adapter_utils import train_model
from llama_index.embeddings.adapter.utils import BaseAdapter


class DummyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.lin = torch.nn.Linear(4, 4, bias=False)

    def forward(self, x):
        return self.lin(x)

    def save(self, output_path: str) -> None:  # pragma: no cover - not needed
        pass


class DummyLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.called = False

    def forward(self, query, context):
        self.called = True
        return (query - context).pow(2).mean()


def test_custom_loss_used(tmp_path):
    adapter = DummyAdapter()
    data = torch.zeros((2, 4))
    loader = DataLoader(TensorDataset(data, data), batch_size=1)
    loss = DummyLoss()

    train_model(
        adapter,
        loader,
        torch.device("cpu"),
        epochs=1,
        steps_per_epoch=1,
        warmup_steps=0,
        show_progress_bar=False,
        loss_model=loss,
        output_path=str(tmp_path),
    )

    assert loss.called
