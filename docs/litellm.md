# Local inference via LiteLLM

Routes every LLM call in the backend to a local Ollama model (`qwen3.6:27b`)
through a LiteLLM proxy, instead of hosted APIs.

Nothing changes unless you opt in. With the `llm` profile stopped and the
`*_BASE_URL` vars unset, the OpenAI and Anthropic providers call their real
vendor endpoints exactly as before.

## Why a proxy rather than just editing config

The backend asks for models by name (`gpt-4o`, `claude-sonnet-4-6`,
`deepseek-v4-pro:cloud`) in several places — the annotation path, the generation
path, and the review swarm. LiteLLM maps those names onto local models in one
YAML file, so a name can be re-pointed without touching application code, and
switching back is a config edit rather than a revert.

## Quick start

Local `qwen3.6:27b` is now the **default**. Start the stack with the `llm`
profile and everything routes on-box, no env vars required:

```bash
docker compose --profile llm up -d
```

The backend waits for the proxy's healthcheck before starting. Verify:

```bash
curl -s localhost:4000/health/liveliness     # {"status":"healthy"...}
curl -s localhost:11434/api/ps               # qwen3.6:27b resident in VRAM
```

### Reverting to hosted models

```bash
DSAT_OPENAI_BASE_URL= DSAT_ANTHROPIC_BASE_URL= \
DSAT_OPENAI_API_KEY=$OPENAI_API_KEY \
DSAT_ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
DSAT_ANNOTATION_MODEL=deepseek-v4-pro:cloud \
DSAT_OLLAMA_MODEL=deepseek-v4-pro:cloud \
docker compose up -d backend
```

Also restore `generation_review_providers` to `"openai,anthropic,ollama"` in
`config.py` if you want the real three-way review swarm back.

## What maps to what

`litellm/config.yaml` maps four request names onto local `qwen3.6:27b`:

| Requested name | Served by | Why the name exists |
|---|---|---|
| `deepseek-v4-pro:cloud` | `qwen3.6:27b` | the backend's `default_ollama_model` |
| `gpt-4o` | `qwen3.6:27b` | requested by the review swarm |
| `claude-sonnet-4-6` | `qwen3.6:27b` | requested by the review swarm + span annotator |
| `qwen3.6:27b` | `qwen3.6:27b` | explicit alias, bypasses the shadowed names |

Note that `deepseek-v4-pro:cloud` was already an Ollama-routed name, but the
`:cloud` suffix means it executed **remotely**. Pointing it at `qwen3.6:27b` is
what actually moves that work on-box.

## Code changes this required

- `llm/openai_provider.py` and `llm/anthropic_provider.py` — both constructors
  accepted an `api_key` but silently discarded `base_url`, so neither could be
  aimed at a local endpoint. Both now accept and forward it.
- `llm/factory.py` — added `resolve_base_url(provider_name, settings)`, which
  centralizes endpoint selection. It previously lived at each call site with
  slightly different logic.
- `routers/generate.py` — passed `settings.ollama_base_url` unconditionally,
  meaning OpenAI and Anthropic jobs were handed the Ollama URL. Now uses the
  resolver.
- `config.py` — added `openai_base_url` and `anthropic_base_url`, both empty by
  default.

## Two bugs this surfaced (both fixed)

**API keys must equal the proxy's master key.** The backend presents
`OPENAI_API_KEY` to LiteLLM, not to OpenAI. A real `OPENAI_API_KEY` exported in
the host shell overrode the compose default, and LiteLLM rejected it as an
unknown virtual key with the misleading error `No connected db.` — nothing to do
with Postgres. Compose now pins both keys to `LITELLM_MASTER_KEY` rather than
using a `:-` fallback that a host env var can win.

**`AnthropicProvider` crashed on reasoning output.** It read
`response.content[0].text` in three places, assuming the first content block is
text. That holds for Anthropic's own models but not for qwen3.6, which returns a
`ThinkingBlock` first — producing `AttributeError: 'ThinkingBlock' object has no
attribute 'text'`. Now selects the first block that actually has `.text`.

## Three things that will bite you

**1. `qwen3.6` is a reasoning model.** It emits a thinking block billed to
`completion_tokens` before any visible content. Verified: the same prompt at
`max_tokens=40` returned `content=''` with all 40 tokens spent reasoning; at
`max_tokens=600` it answered after 123. A caller with a tight budget gets an
empty string, not an error. Repo defaults (`max_tokens=4096`) are ample, but do
not lower them, and be careful with strict JSON parsing of responses.

**2. The review swarm's consensus becomes fake.** `generation_review_providers`
is `"openai,anthropic,ollama"` and fans out to three providers expecting
independent opinions. Map all three onto one local model and you get one
opinion counted three times — agreement still gets reported, but it no longer
carries information. Either keep genuinely different models behind those names
(`config.yaml` makes this a one-line change per entry), or shrink the swarm
honestly.

**3. OCR does not route through the proxy.** `ocr_strategy` and
`parsers/ocr.py::DeepSeekOCRClient` use a separate vision path that is not built
on the `LLMProvider` interface, so it still talks to Ollama directly via
`deepseek_ocr_base_url`. A `glm-ocr` entry exists in `config.yaml` for when that
client is refactored, but today it is unused.

## Throughput

`config.py` records hard-won limits: Ollama 429s at roughly 20 concurrent, and
`annotation_max_concurrent` is pinned to 1 because GPU inference serializes. A
proxy queues requests; it does not add GPU capacity. `rpm` and
`max_parallel_requests` in `config.yaml` stay under those limits deliberately.
Raising them reintroduces the 429s rather than increasing throughput.

Also expect local `qwen3.6:27b` to be substantially slower per request than a
hosted frontier model — `request_timeout` is set to 600s for that reason. Bulk
jobs like full-test ingestion will take proportionally longer.

## Verified

- All four mapped names return content through the proxy.
- `gpt-4o` → LiteLLM → local `qwen3.6:27b` returns the expected string.
- Backend container reaches `http://litellm:4000/v1/models` by service name (200).
- With the proxy env unset, providers still resolve to `https://api.openai.com/v1/`
  and `https://api.anthropic.com`.
