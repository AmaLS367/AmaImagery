from __future__ import annotations

from typing import Any

import torch


def get_unet_dtype(pipe: Any) -> torch.dtype:
    try:
        dtype = next(pipe.unet.parameters()).dtype

        # If dtype is float16 but device is CPU, convert to float32
        if dtype == torch.float16:
            device = next(pipe.unet.parameters()).device
            if device.type == "cpu":
                return torch.float32

        return dtype
    except Exception:
        # Fallback: check device type
        try:
            device = next(pipe.unet.parameters()).device
            return torch.float16 if device.type == "cuda" else torch.float32
        except Exception:
            return torch.float32


def align_to_unet_dtype(tensor: torch.Tensor, pipe: Any) -> torch.Tensor:
    try:
        return tensor.to(dtype=get_unet_dtype(pipe), device=pipe.device)
    except Exception:
        return tensor

