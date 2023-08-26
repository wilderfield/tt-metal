import math
from pathlib import Path
import sys
from typing import Optional, Tuple, Union
import torch
import torch.nn as nn
import numpy as np
from loguru import logger

f = f"{Path(__file__).parent}"
sys.path.append(f"{f}/..")
sys.path.append(f"{f}/../..")
sys.path.append(f"{f}/../../..")
sys.path.append(f"{f}/../../../..")

from tt_models.utility_functions import (
    torch2tt_tensor,
    tt2torch_tensor,
)
from python_api_testing.models.roberta.roberta_common import (
    torch2tt_tensor,
    tt2torch_tensor,
)
import tt_lib
from tt_lib.fallback_ops import fallback_ops

from python_api_testing.models.roberta.roberta_self_attention import (
    TtRobertaSelfAttention,
)
from python_api_testing.models.roberta.roberta_self_output import TtRobertaSelfOutput


# Copied from transformers.models.bert.modeling_bert.BertAttention with Bert->Roberta
class TtRobertaAttention(nn.Module):
    def __init__(
        self, config, state_dict, base_address, device, position_embedding_type=None
    ):
        super().__init__()
        self.device = device

        self.self = TtRobertaSelfAttention(
            config=config,
            state_dict=state_dict,
            base_address=f"{base_address}.self",
            device=device,
            position_embedding_type=position_embedding_type,
        )

        self.output = TtRobertaSelfOutput(
            config, state_dict, f"{base_address}.output", device
        )
        self.pruned_heads = set()

    """
    Method prune_heads:
    Not used for now. If some of the models from roberta use it we will implement it.
    """
    # def prune_heads(self, heads):
    #     if len(heads) == 0:
    #         return
    #     heads, index = find_pruneable_heads_and_indices(
    #         heads, self.self.num_attention_heads, self.self.attention_head_size, self.pruned_heads
    #     )

    #     # Prune linear layers
    #     self.self.query = prune_linear_layer(self.self.query, index)
    #     self.self.key = prune_linear_layer(self.self.key, index)
    #     self.self.value = prune_linear_layer(self.self.value, index)
    #     self.output.dense = prune_linear_layer(self.output.dense, index, dim=1)

    #     # Update hyper params and store pruned heads
    #     self.self.num_attention_heads = self.self.num_attention_heads - len(heads)
    #     self.self.all_head_size = self.self.attention_head_size * self.self.num_attention_heads
    #     self.pruned_heads = self.pruned_heads.union(heads)

    def forward(
        self,
        hidden_states: tt_lib.tensor.Tensor,
        attention_mask: Optional[tt_lib.tensor.Tensor] = None,
        head_mask: Optional[tt_lib.tensor.Tensor] = None,
        encoder_hidden_states: Optional[tt_lib.tensor.Tensor] = None,
        encoder_attention_mask: Optional[tt_lib.tensor.Tensor] = None,
        past_key_value: Optional[Tuple[Tuple[tt_lib.tensor.Tensor]]] = None,
        output_attentions: Optional[bool] = False,
    ) -> Tuple[tt_lib.tensor.Tensor]:
        self_outputs = self.self(
            hidden_states,
            attention_mask,
            head_mask,
            encoder_hidden_states,
            encoder_attention_mask,
            past_key_value,
            output_attentions,
        )
        attention_output = self.output(self_outputs[0], hidden_states)
        outputs = (attention_output,) + self_outputs[
            1:
        ]  # add attentions if we output them
        return outputs
