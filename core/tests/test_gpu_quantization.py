import pytest


def test_gpu_quantization_support():
    try:
        import torch
    except Exception:
        pytest.skip("torch not installed")
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    try:
        import bitsandbytes as bnb
    except Exception:
        pytest.skip("bitsandbytes not installed")
    assert hasattr(bnb.nn, "Linear4bit")
    assert hasattr(bnb.nn, "Linear8bitLt")
