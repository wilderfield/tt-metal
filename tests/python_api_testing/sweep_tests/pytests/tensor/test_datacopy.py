import pytest
import sys
import torch
import tt_lib as ttl
from pathlib import Path
from functools import partial

f = f"{Path(__file__).parent}"
sys.path.append(f"{f}/..")
sys.path.append(f"{f}/../..")
sys.path.append(f"{f}/../../..")
sys.path.append(f"{f}/../../../..")


from python_api_testing.sweep_tests import comparison_funcs, generation_funcs
from python_api_testing.sweep_tests.run_pytorch_ci_tests import run_single_pytorch_test


@pytest.mark.parametrize("input_shapes", ([[1, 1, 32, 32]], [[1, 1, 256, 256]]))
@pytest.mark.parametrize("pcie_slot", (0,))
@pytest.mark.parametrize(
    "dtype", (ttl.tensor.DataType.BFLOAT16, ttl.tensor.DataType.BFLOAT8_B)
)
@pytest.mark.parametrize(
    "memory_config",
    (
        ttl.tensor.MemoryConfig(True, -1, ttl.tensor.BufferType.DRAM),
        ttl.tensor.MemoryConfig(True, -1, ttl.tensor.BufferType.L1),
        ttl.tensor.MemoryConfig(False, 1, ttl.tensor.BufferType.DRAM),
        ttl.tensor.MemoryConfig(False, 1, ttl.tensor.BufferType.L1),
    ),
)
def test_run_datacopy_test(
    input_shapes, pcie_slot, dtype, memory_config, function_level_defaults
):
    datagen_func = [
        generation_funcs.gen_func_with_cast(
            partial(generation_funcs.gen_rand, low=-100, high=100), torch.bfloat16
        )
    ]

    if dtype == ttl.tensor.DataType.BFLOAT8_B:
        comparison_func = partial(comparison_funcs.comp_allclose, atol=1.0)
    else:
        comparison_func = partial(comparison_funcs.comp_equal)

    run_single_pytorch_test(
        "datacopy",
        input_shapes,
        datagen_func,
        comparison_func,
        pcie_slot,
        {"dtype": dtype, "memory_config": memory_config},
    )
