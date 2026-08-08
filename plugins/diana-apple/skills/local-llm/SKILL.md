---
name: local-llm
description: "Run any LLM locally on Apple Silicon, even models larger than available RAM — picks quantization, engine, and offloading, then tunes throughput."
triggers: ["run model locally", "local llm", "запустить модель локально", "local inference", "llm in a flash"]
---

# Local LLM Runner

Run any LLM on Apple Silicon hardware, including models that exceed available RAM. Combines hardware analysis, smart quantization selection, engine choice, and iterative optimization.

## Background

Based on Apple's ["LLM in a Flash"](https://arxiv.org/abs/2312.11514) research: store model weights in flash/SSD, load only active neurons to DRAM on demand. Key techniques:
- **Windowing** — reuse recently activated neurons across tokens, load only incremental changes
- **Row-column bundling** — concatenate up/down projection matrices for larger sequential reads
- **Sparsity-aware loading** — predict which neurons activate, skip the rest (>90% sparsity in FFN layers)
- **Result**: run models 2x larger than DRAM, 4-25x faster than naive loading

## Workflow

### Phase 1: Hardware Analysis

```bash
# Unified memory
sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}'
# Chip
sysctl -n machdep.cpu.brand_string
# Available memory
memory_pressure | head -5
# SSD speed (approximate)
diskutil info disk0 | grep "Disk Size"
# GPU cores
system_profiler SPDisplaysDataType 2>/dev/null | grep "Total Number of Cores"
```

Collect into a hardware profile:
- **Total unified memory** (e.g., 48GB, 96GB, 128GB, 192GB)
- **Available memory** (subtract ~4GB for OS overhead)
- **Chip** (M1/M2/M3/M4/M5, Pro/Max/Ultra)
- **SSD capacity and speed** (~3-7 GB/s read on modern Macs)

### Phase 2: Model Analysis

For the requested model, determine:
1. **Total parameters** (e.g., 397B)
2. **Architecture** — dense vs MoE (Mixture of Experts)
3. **Active parameters** for MoE (e.g., Qwen3.5-397B has only 17B active)
4. **Available quantizations** on HuggingFace

**Memory estimation formula:**
```
weights_gb = params_billions * bytes_per_param
  Q2_K: ~0.31 bytes/param
  Q3_K_M: ~0.44 bytes/param
  Q4_K_M: ~0.56 bytes/param
  Q5_K_M: ~0.69 bytes/param
  Q6_K: ~0.81 bytes/param
  Q8_0: ~1.06 bytes/param
  FP16: ~2.0 bytes/param

total_gb = weights_gb + kv_cache_gb + overhead_gb
kv_cache_gb ≈ 2 * n_layers * n_heads * head_dim * context_len * bytes / 1e9
overhead_gb ≈ max(1.0, weights_gb * 0.1)
```

### Phase 3: Strategy Selection

Based on `total_gb` vs `available_memory_gb`:

| Scenario | Strategy |
|----------|----------|
| Model fits in 80% of RAM | **MLX** — fastest, native Apple Silicon |
| Model fits in 100% of RAM | **MLX** with reduced context, or **llama.cpp** with full GPU offload |
| Model is 1-1.5x RAM | **llama.cpp** with partial GPU offload (`--ngl` < max) + mmap |
| Model is 1.5-2x RAM | **llama.cpp** with minimal GPU + aggressive mmap + lower quant |
| Model is >2x RAM | **Flash offloading** — custom implementation or extreme quantization |
| MoE model | Check active params only — often fits comfortably |

**Engine comparison:**

| Engine | Best for | Install |
|--------|----------|---------|
| **mlx-lm** | Models that fit in RAM, fastest tok/s | `uv pip install mlx-lm` |
| **llama.cpp** | Partial offloading, mmap, GGUF | `brew install llama.cpp` |
| **ollama** | Easy setup, good defaults | `brew install ollama` |
| **omlx** | Server mode, SSD KV cache | `brew install omlx` |
| **lm-studio** | GUI, easy model management | Download from lmstudio.ai |

### Phase 4: Download & Setup

**For MLX:**
```bash
# Find MLX variant on HuggingFace
# Pattern: mlx-community/<model>-<quant>
mlx_lm.generate --model mlx-community/<model> --prompt "Hello" --max-tokens 10
```

**For llama.cpp (GGUF):**
```bash
# Download GGUF from HuggingFace (unsloth or bartowski quants)
huggingface-cli download <repo> <file.gguf> --local-dir ~/.diana/models/

# Run with optimal settings
llama-cli \
  --model ~/.diana/models/<file.gguf> \
  --n-gpu-layers <calculated> \
  --ctx-size 4096 \
  --threads $(sysctl -n hw.perflevel0.logicalcpu) \
  --mmap \
  --prompt "Hello"
```

**GPU layers calculation:**
```
available_gpu_gb = available_memory_gb * 0.85
gpu_layers = min(total_layers, floor(available_gpu_gb / per_layer_gb))
per_layer_gb = weights_gb / total_layers
```

### Phase 5: Benchmark & Optimize (Autoresearch Loop)

After initial setup, run iterative optimization:

1. **Baseline benchmark:**
```bash
llama-bench --model <path> -ngl <N> -t <threads> -p 512 -n 128
# or for MLX:
mlx_lm.generate --model <model> --prompt "<long prompt>" --max-tokens 128 --verbose
```

2. **Record metrics:** prompt tok/s (prefill), generation tok/s, peak memory

3. **Optimization levers to try iteratively:**
   - Adjust `--n-gpu-layers` (more GPU = faster, but may OOM)
   - Adjust `--ctx-size` (smaller = less KV cache memory)
   - Try different quantization levels
   - Adjust thread count
   - For llama.cpp: `--flash-attn` flag
   - For llama.cpp: `--no-mmap` vs `--mmap` (counterintuitive — sometimes no-mmap is faster)
   - For MoE: `--override-kv` for expert offloading ratios
   - Batch size for prefill (`-b` flag)

4. **Compare and keep best config**

### Phase 6: Serve (Optional)

For ongoing use, set up as a server:

```bash
# llama.cpp server
llama-server --model <path> --n-gpu-layers <N> --port 8080

# ollama
ollama run <model>

# omlx (with SSD KV cache)
omlx serve --model-dir ~/.diana/models/
```

## MoE Models — Special Handling

MoE models (Qwen3.5-397B-A17B, DeepSeek-V3, Mixtral) are ideal for limited RAM:
- Total params ≠ active params. Qwen3.5-397B activates only 17B per token
- With Q4 quantization: ~214GB on disk, but only ~10GB active weights in memory
- **llama.cpp MoE offloading**: keeps active experts in GPU, inactive on disk
- Key flag: `--override-kv` for expert placement control

## Troubleshooting

| Issue | Fix |
|-------|-----|
| OOM / killed | Reduce `--n-gpu-layers`, lower quant, smaller context |
| Very slow (<0.5 tok/s) | Too much swap — reduce model size or increase GPU layers |
| Metal errors | Update macOS, check `--n-gpu-layers` not exceeding model layers |
| Model won't load | Check disk space, GGUF format compatibility |

## Key Resources

- [LLM in a Flash paper](https://arxiv.org/abs/2312.11514)
- [mlx-lm](https://github.com/ml-explore/mlx-lm)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [omlx](https://github.com/jundot/omlx)
- [Unsloth quants](https://huggingface.co/unsloth) — optimized GGUF variants
- [WWDC 2025: Explore LLM on Apple Silicon with MLX](https://developer.apple.com/videos/play/wwdc2025/298/)

## Example: Qwen3.5-397B on M3 Max 48GB

```
Hardware: M3 Max, 48GB unified memory, 40 GPU cores
Model: Qwen3.5-397B-A17B (MoE, 17B active)
Strategy: llama.cpp, Q4_K_M GGUF (~214GB on disk)
  → Active weights ~10GB in GPU memory
  → Inactive experts mmap'd from SSD
  → --n-gpu-layers 64 --ctx-size 4096 --flash-attn
Expected: ~1-5 tok/s depending on optimization level
```
