"""
Flash Attention Drop-in Compatibility Layer using PyTorch 2.11 Native SDPA (FlashAttention-2 / CuDNN)
Fully optimized for NVIDIA RTX PRO 6000 Blackwell GPU (CUDA 12.8 / 13.0).
"""

import torch
import torch.nn.functional as F

__version__ = "2.7.4.post1"

def flash_attn_func(
    q,
    k,
    v,
    dropout_p=0.0,
    softmax_scale=None,
    causal=False,
    window_size=(-1, -1),
    softcap=0.0,
    alibi_slopes=None,
    deterministic=False,
    return_attn_probs=False,
    **kwargs
):
    """
    Args:
        q: (batch_size, seqlen_q, nheads, headdim)
        k: (batch_size, seqlen_k, nheads_k, headdim)
        v: (batch_size, seqlen_k, nheads_k, headdim)
    """
    # Transpose to PyTorch SDPA format: (batch_size, nheads, seqlen, headdim)
    q_t = q.transpose(1, 2)
    k_t = k.transpose(1, 2)
    v_t = v.transpose(1, 2)

    # Repeat KV heads for Grouped Query Attention (GQA) if necessary
    if q_t.shape[1] != k_t.shape[1]:
        ratio = q_t.shape[1] // k_t.shape[1]
        k_t = k_t.repeat_interleave(ratio, dim=1)
        v_t = v_t.repeat_interleave(ratio, dim=1)

    out = F.scaled_dot_product_attention(
        q_t,
        k_t,
        v_t,
        scale=softmax_scale,
        is_causal=causal,
        dropout_p=dropout_p if q.requires_grad else 0.0
    )

    out = out.transpose(1, 2).contiguous()
    if return_attn_probs:
        return out, None
    return out

def flash_attn_varlen_func(
    q,
    k,
    v,
    cu_seqlens_q,
    cu_seqlens_k,
    max_seqlen_q,
    max_seqlen_k,
    dropout_p=0.0,
    softmax_scale=None,
    causal=False,
    window_size=(-1, -1),
    softcap=0.0,
    alibi_slopes=None,
    deterministic=False,
    return_attn_probs=False,
    **kwargs
):
    """
    Varlen attention using slice iteration with SDPA.
    """
    batch_size = len(cu_seqlens_q) - 1
    outputs = []
    
    for i in range(batch_size):
        q_slice = q[cu_seqlens_q[i]:cu_seqlens_q[i+1]].unsqueeze(0) # (1, seqlen, nheads, dim)
        k_slice = k[cu_seqlens_k[i]:cu_seqlens_k[i+1]].unsqueeze(0)
        v_slice = v[cu_seqlens_k[i]:cu_seqlens_k[i+1]].unsqueeze(0)

        out_slice = flash_attn_func(
            q_slice,
            k_slice,
            v_slice,
            dropout_p=dropout_p,
            softmax_scale=softmax_scale,
            causal=causal,
            window_size=window_size
        )
        outputs.append(out_slice.squeeze(0))

    out = torch.cat(outputs, dim=0)
    if return_attn_probs:
        return out, None
    return out
