---
name: local-llm
description: "Run any LLM locally on Apple Silicon, even models larger than available RAM — picks quantization, engine, and offloading, then tunes throughput."
triggers: ["run model locally", "local llm", "запустить модель локально", "local inference", "llm in a flash"]
---

# Local LLM Runner

Pick a quantization, engine and offload split for a model on this Mac, then measure and tune.
Engine flags change between releases — read `<engine> --help` on the installed build, never
flags from memory (llama.cpp 0.7.0 replaced `--mmap/--no-mmap` with `--load-mode`; MoE expert
placement is `--n-cpu-moe` / `--cpu-moe` / `-ot`, not `--override-kv`).

## This machine (verified 2026-11-18 — re-check)

- Apple M3 Max, 128 GB unified memory.
- Installed: `llama-cli` / `llama-server` / `llama-bench` (Homebrew llama.cpp), `ollama`, `hf`,
  `lms` + LM Studio.app, Feynt.app. Not installed: `mlx_lm.*` (`uv tool install mlx-lm`), `omlx`.
- Model dir: `~/.diana/models/` (GGUFs in `gguf/`). LM Studio downloads to `~/.lmstudio/models`
  (chat models deleted 2026-11-16; `lms ls` shows only an embedding model).
- Roman's rule: local models are Qwen3.5-family only, never Qwen3.
- Feynt = Roman's MLX menu-bar app, OpenAI API on `127.0.0.1:19234/v1` when running; pi uses it
  as provider `feynt` (see `pi-dev`).

## Workflow

1. **Hardware profile** (free memory decides everything):
   ```bash
   sysctl -n machdep.cpu.brand_string; sysctl -n hw.memsize | awk '{print $1/1073741824 " GB"}'
   memory_pressure | tail -1; df -h ~ | tail -1
   ```
2. **Size it.** `weights_GB ≈ params_B × bits_per_weight / 8`; add KV cache for the context and
   ~10% overhead. Bits per quant type: [llama.cpp quantize README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md).
   MoE: every expert must still be stored; active params set speed, not footprint.
3. **Pick the engine.**

   | Fits in RAM? | Engine |
   |---|---|
   | ≤ ~75% of RAM | MLX (`mlx-lm`, Feynt) or LM Studio — fastest on Apple Silicon |
   | ~75–100% | llama.cpp GGUF, full GPU offload, smaller context |
   | 1–2× RAM | llama.cpp GGUF, partial offload (`-ngl`), MoE experts on CPU (`--n-cpu-moe N`), weights mmapped from SSD |
   | > 2× RAM | Lower quant or a smaller model; SSD streaming ("LLM in a Flash") is research, not a tool |

4. **Get weights:** `hf download <repo> <file.gguf> --local-dir ~/.diana/models/gguf/`
   (MLX: `mlx-community/<model>-<quant>`; GGUF: unsloth or bartowski repos).
5. **Benchmark, then iterate one lever at a time** (`-ngl`, `--n-cpu-moe`, context, quant,
   `-fa`, threads, `-b`), keeping the best — use the `iterate` skill for the loop:
   ```bash
   llama-bench -m <file.gguf> -ngl <N> -p 512 -n 128
   ```
   Record prefill tok/s, generation tok/s and peak memory per config.
6. **Serve** (optional): `llama-server -m <file.gguf> -ngl <N> --port 8080`, `lms server start`,
   or Feynt.

## References

- [llama.cpp](https://github.com/ggml-org/llama.cpp) · [server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) · [llama-bench](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md)
- [mlx-lm](https://github.com/ml-explore/mlx-lm) · [WWDC25: LLMs on Apple Silicon with MLX](https://developer.apple.com/videos/play/wwdc2025/298/)
- [LM Studio CLI](https://lmstudio.ai/docs/cli) · [Ollama](https://github.com/ollama/ollama) · [omlx](https://github.com/jundot/omlx) (SSD KV cache server)
- [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) · [Unsloth quants](https://huggingface.co/unsloth)
- [LLM in a Flash](https://arxiv.org/abs/2312.11514) — flash offloading research behind the >RAM case
