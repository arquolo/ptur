__all__ = ['conv2d_ws', 'upscale2d']

import torch.nn.functional as F
from torch import Size, Tensor, nn
from torch.nn.utils import parametrize

_size = Size | list[int] | tuple[int, ...]


# @torch.jit.script
def upscale2d(x: Tensor, stride: int = 2) -> Tensor:
    # ! stride-aware fallback, works everywhere
    # x = F.interpolate(x, None, self.stride)
    # return F.avg_pool2d(x, self.stride, 1, 0)

    # ! matches to single libtorch op, complex torchscript op
    pad = 1 - stride
    size = [x.shape[2], x.shape[3]]
    size = [s * stride + pad for s in size]
    return F.interpolate(x, size, mode='bilinear', align_corners=True)


def conv2d_ws(x: Tensor,
              weight: Tensor,
              bias: Tensor | None = None,
              stride: _size | int = 1,
              padding: _size | int | str = 0,
              dilation: _size | int = 1,
              groups: int = 1):
    weight = F.layer_norm(weight, weight.shape[1:], eps=1e-5)
    return F.conv2d(x, weight, bias, stride, padding, dilation, groups)


def standartize_conv_weights(model: nn.Module) -> None:
    """Enforce weight standartization for all ConvNd modules"""
    for m in model.modules():
        if not isinstance(m, nn.modules.conv._ConvNd):
            continue
        shape = m.weight.shape
        parametrize.register_parametrization(
            m, 'weight', nn.LayerNorm(shape[1:], elementwise_affine=False))
