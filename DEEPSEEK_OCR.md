# DeepSeek OCR — Local Setup Guide

**Model:** DeepSeek-OCR-2 (primary) / DeepSeek-VL2-Tiny (fallback for general vision)
**Date:** 2026-05-09

---

## Which Model to Use

| Model | Purpose | Size | VRAM |
|---|---|---|---|
| **DeepSeek-OCR-2** | Document OCR, exam PDFs, Markdown extraction | 3B params | ~6–8 GB |
| DeepSeek-VL2-Tiny | General vision QA, mixed image/text tasks | 3.37B params | ~10–16 GB |
| DeepSeek-VL2-Small | High-accuracy vision, dense layouts | 16.1B params | ~40 GB |

**Use DeepSeek-OCR-2 for this project.** It is purpose-built for document text extraction,
produces Markdown-structured output, has a dedicated vLLM recipe, and runs on a single
consumer GPU. VL2-Tiny is an option only if you need general visual QA beyond OCR.

---

## Hardware Requirements

### Minimum (DeepSeek-OCR-2)
- **GPU:** Any NVIDIA GPU with 8 GB VRAM (RTX 3070, RTX 4060, A10)
- **GPU compute:** Ampere (sm_80+) required for bfloat16. GTX 1080/Pascal will fail.
  Use `float16` as a workaround on older cards (see §Troubleshooting).
- **RAM:** 16 GB system RAM
- **Disk:** ~7 GB for model weights

### For VL2-Tiny
- **GPU:** 16 GB VRAM minimum (RTX 3090, RTX 4080, A5000)
- **GPU compute:** Ampere (sm_80+) — mandatory, not optional
- **RAM:** 32 GB system RAM recommended

### Apple Silicon
- DeepSeek-OCR-2 runs via **PyTorch MPS** (Metal) on Apple Silicon — use `float16`, not `bfloat16`
- DeepSeek-VL2 has no working GPU path on Mac; vLLM/Docker do not support Metal
- See §Mac Setup for the supported path

---

## Linux Setup (NVIDIA GPU)

### Option 1: Docker + vLLM (Recommended for Production)

**Prerequisites:** CUDA 12.1+, Docker, `nvidia-container-toolkit`

**DeepSeek-OCR-2:**

```bash
docker run -d \
  --runtime nvidia \
  --gpus all \
  --ipc=host \
  -p 8001:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model deepseek-ai/DeepSeek-OCR-2 \
  --logits-processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --trust-remote-code \
  --max-model-len 4096
```

The custom `--logits-processors` flag is required for OCR-2's specialized decoding. Without it,
output quality degrades significantly. Do not omit `--no-enable-prefix-caching`.

**DeepSeek-VL2-Tiny (if using VL2 instead):**

```bash
docker run -d \
  --runtime nvidia \
  --gpus all \
  --ipc=host \
  -p 8001:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model deepseek-ai/deepseek-vl2-tiny \
  --hf_overrides '{"architectures": ["DeepseekVLV2ForCausalLM"]}' \
  --trust-remote-code \
  --max-model-len 4096
```

The `--hf_overrides` flag is required for VL2. Without it, vLLM cannot identify the
architecture and refuses to load the model. Use vLLM v0.7.2 or later.

Once running, the API is available at `http://localhost:8001/v1`.

---

### Option 2: LMDeploy (Best Documentation for VL2, Works for OCR-2)

LMDeploy has first-party VL2 documentation and exposes an OpenAI-compatible server.

```bash
# Install dependencies — transformers version pin is critical
pip install git+https://github.com/deepseek-ai/DeepSeek-VL2.git --no-deps
pip install attrdict timm 'transformers<4.48.0' accelerate einops
pip install lmdeploy

# Launch API server on port 23333
# For DeepSeek-OCR-2:
lmdeploy serve api_server deepseek-ai/DeepSeek-OCR-2 \
  --backend pytorch \
  --server-port 23333

# For VL2-Tiny:
lmdeploy serve api_server deepseek-ai/deepseek-vl2-tiny \
  --backend pytorch \
  --server-port 23333
```

API available at `http://localhost:23333/v1`.

**Important:** The `transformers<4.48.0` pin is non-negotiable. Version 4.48.0 and later
broke VL2 weight loading. Pin it before installing anything else.

---

### Option 3: Ollama

> **DeepSeek-VL2 and DeepSeek-OCR-2 are not in the Ollama model registry** as of May 2026.
> The architectures have not been implemented in llama.cpp and no official GGUF weights exist.
> `ollama pull deepseek-ocr-2` will fail.

**If GGUF weights appear on Hugging Face in the future**, you can import them:

```bash
# Download GGUF from HuggingFace (when available)
huggingface-cli download <repo-id> deepseek-ocr-2-Q4_K_M.gguf \
  --local-dir ~/models/deepseek-ocr-2

# Create Modelfile
cat > ~/models/deepseek-ocr-2/Modelfile <<'EOF'
FROM ./deepseek-ocr-2-Q4_K_M.gguf
EOF

# Import and run
ollama create deepseek-ocr-2 -f ~/models/deepseek-ocr-2/Modelfile
ollama run deepseek-ocr-2
```

Monitor [mlx-community on HuggingFace](https://huggingface.co/mlx-community) and the
[Ollama model library](https://ollama.com/library) for when this becomes available.

---

## Mac Setup (Apple Silicon)

### What Works

| Path | DeepSeek-OCR-2 | DeepSeek-VL2 |
|---|---|---|
| Docker + vLLM | No — no Metal GPU passthrough | No |
| Ollama | No — model not in registry | No |
| LMDeploy + PyTorch MPS | Yes (float16) | Tiny only, slow |
| LM Studio | No — no GGUF available | No |
| MLX (future) | Watch mlx-community | Watch mlx-community |

### PyTorch MPS — DeepSeek-OCR-2 (Recommended for Mac)

```bash
# Install dependencies (Python 3.10+ via pyenv or conda)
pip install 'transformers<4.48.0' torch accelerate einops

# Run inference with MPS
python3 - <<'EOF'
from transformers import AutoModel, AutoTokenizer
import torch

model_id = "deepseek-ai/DeepSeek-OCR-2"

# Use float16 — bfloat16 has limited MPS support
model = AutoModel.from_pretrained(
    model_id,
    trust_remote_code=True,
    torch_dtype=torch.float16
)
model = model.eval().to("mps")

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
print("Model loaded on MPS successfully")
EOF
```

**Mac RAM requirements for OCR-2:**
- 16 GB unified memory: works (tight — close other apps)
- 24 GB+ unified memory: comfortable
- Works on M1/M2/M3/M4 Pro and Max; marginal on M1/M2 base with 16 GB

### LMDeploy Server on Mac (OpenAI-Compatible API)

```bash
pip install 'transformers<4.48.0' torch lmdeploy attrdict timm

lmdeploy serve api_server deepseek-ai/DeepSeek-OCR-2 \
  --backend pytorch \
  --server-port 23333
```

The PyTorch backend will use MPS automatically on Apple Silicon. Once running, the API
is at `http://localhost:23333/v1` — the same interface as Linux.

### Future: MLX Path

Apple's MLX framework provides native Metal acceleration and is the best long-term path
for Mac. Watch:
- `https://huggingface.co/mlx-community` — for MLX-converted weights
- `https://github.com/waybarrios/vllm-mlx` — OpenAI-compatible MLX server
- `https://github.com/raullenchai/Rapid-MLX` — alternative MLX server

When an `mlx-community/deepseek-ocr-2` or `mlx-community/deepseek-vl2-tiny` model
appears, it will be the preferred Mac path, providing Metal GPU acceleration without
the PyTorch MPS workarounds.

---

## API Usage

All three serving options (vLLM Docker, LMDeploy, MLX servers) expose an
OpenAI-compatible `/v1/chat/completions` endpoint. No API key is required for local.

### Test Connection

```bash
curl http://localhost:8001/v1/models
```

### OCR — Text Extraction from a Local Image

```bash
IMAGE_B64=$(base64 -w0 /path/to/scanned-page.jpg)   # Linux
# IMAGE_B64=$(base64 -i /path/to/scanned-page.jpg)  # Mac (no -w0)

curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"deepseek-ai/DeepSeek-OCR-2\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": [
          {
            \"type\": \"image_url\",
            \"image_url\": {
              \"url\": \"data:image/jpeg;base64,${IMAGE_B64}\"
            }
          },
          {
            \"type\": \"text\",
            \"text\": \"Extract all text from this document. Preserve formatting. Output Markdown.\"
          }
        ]
      }
    ],
    \"max_tokens\": 2048
  }"
```

### OCR — Image via URL

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-OCR-2",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {"url": "http://localhost/path/to/image.png"}
          },
          {
            "type": "text",
            "text": "Extract the question text, answer options, and correct answer from this exam image."
          }
        ]
      }
    ],
    "max_tokens": 1024
  }'
```

### Python Client (matches DSAT backend integration)

```python
from openai import AsyncOpenAI
import base64, pathlib

client = AsyncOpenAI(
    base_url="http://localhost:8001/v1",
    api_key="not-required",  # local server, no auth
)

async def ocr_image(image_path: str) -> str:
    b64 = base64.b64encode(pathlib.Path(image_path).read_bytes()).decode()
    mime = "image/jpeg" if image_path.endswith(".jpg") else "image/png"

    response = await client.chat.completions.create(
        model="deepseek-ai/DeepSeek-OCR-2",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract all text from this document page. "
                            "Preserve question structure, answer choices (A/B/C/D), and passage text. "
                            "Output plain text only, no commentary."
                        ),
                    },
                ],
            }
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content
```

---

## Integration with DSAT Backend

Set these env vars to point the DSAT ingest pipeline at the local DeepSeek OCR-2 server:

```bash
# .env
OCR_STRATEGY=deepseek              # or "auto" to allow admin selection per-job
DEEPSEEK_OCR_BASE_URL=http://localhost:8001   # vLLM Docker
# DEEPSEEK_OCR_BASE_URL=http://localhost:23333  # LMDeploy
DEEPSEEK_OCR_MODEL=deepseek-ai/DeepSeek-OCR-2
```

Admin can override per-job by passing `ocr_strategy=deepseek` in the ingest form data.
The selected strategy and model are recorded in `pass1_json._ocr_meta`.

---

## Troubleshooting

### `bfloat16` error on older NVIDIA GPU

```
RuntimeError: "weight_norm_cuda" not implemented for 'BFloat16'
# or
ValueError: requires device with capability > (8, 0)
```

**Cause:** Pre-Ampere NVIDIA GPUs (GTX 1080, GTX 1080 Ti, RTX 2080, P40, V100 pre-SXM2)
do not support bfloat16 natively.

**Fix:** Force float16 at load time:
```python
model = AutoModel.from_pretrained(
    "deepseek-ai/DeepSeek-OCR-2",
    trust_remote_code=True,
    torch_dtype=torch.float16,  # instead of bfloat16
)
```
For vLLM Docker, add `--dtype float16` to the serve command.

---

### vLLM refuses to load VL2 (`architecture not recognized`)

```
ValueError: The checkpoint you are trying to load has model type `deepseek_vl_v2`
but Transformers does not recognize this architecture.
```

**Fix:** Add `--hf_overrides '{"architectures": ["DeepseekVLV2ForCausalLM"]}'` to the
vLLM serve command. Requires vLLM v0.7.2+.

---

### Multi-GPU tensor device mismatch (VL2 only)

```
RuntimeError: Expected all tensors to be on the same device, but found cuda:0 and cuda:1
```

**Cause:** The VL2 MoE routing layer has a known bug with tensor parallelism.

**Fix:** Run on a single GPU. Remove `--tensor-parallel-size` or set it to 1.
Do not use `device_map="auto"` in Python — manually place all layers on one device.

---

### `transformers` version conflict

```
AttributeError: 'DeepseekVLV2Config' object has no attribute ...
```

**Fix:** Pin `transformers<4.48.0` before installing any other package that may upgrade it.
Check with `pip show transformers`. If already at 4.48+, downgrade:

```bash
pip install 'transformers==4.46.3'
```

---

### Mac: `bfloat16` not supported on MPS

```
RuntimeError: MPS does not support bfloat16
```

**Fix:** Pass `torch_dtype=torch.float16` when loading the model. MPS supports float16
but has limited bfloat16 support. Minor precision differences are expected.

---

## Port Reference

| Runtime | Default port | API base URL |
|---|---|---|
| vLLM Docker | 8001 (mapped from 8000 in container) | `http://localhost:8001/v1` |
| LMDeploy | 23333 | `http://localhost:23333/v1` |
| LM Studio (future) | 1234 | `http://localhost:1234/v1` |
| Ollama (future) | 11434 | `http://localhost:11434/v1` |

All endpoints accept the same OpenAI `POST /v1/chat/completions` schema.
