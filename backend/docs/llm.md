# LLM Providers

## Provider Protocol

`app/llm/base.py` defines the `LLMProvider` Protocol:

```python
@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        ...
```

`LLMResponse` is a dataclass with:
- `raw_text: str`
- `model: str`
- `provider: str`
- `latency_ms: int`
- `token_usage: Optional[Dict[str, int]]`
- `error: Optional[str]`

## Factory

`app/llm/factory.py` dispatches by name:

```python
from app.llm.factory import get_provider

provider = get_provider("anthropic", api_key="...")
result = await provider.complete(system=..., user=...)
```

| Provider | Module | Default Model |
|---|---|---|
| `anthropic` | `anthropic_provider.py` | `claude-sonnet-4-6` |
| `openai` | `openai_provider.py` | `gpt-4o` |
| `ollama` | `ollama_provider.py` | `kimi-k2` |

## Configuration

Set in `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434

DEFAULT_ANNOTATION_PROVIDER=anthropic
DEFAULT_ANNOTATION_MODEL=claude-sonnet-4-6
RULES_VERSION=rules_agent_dsat_grammar_ingestion_generation_v3
```

## Prompts

### `extract_prompt.py`
- System: DSAT question extraction specialist
- Output schema: `question_text`, `passage_text`, `options[4]`, `correct_option_label`, source metadata, stimulus/stem keys
- Rules: exactly 4 options labeled A-D, preserve original wording

### `annotate_prompt.py`
- System: DSAT annotation specialist following V3 rules
- Loads `rules_agent_dsat_grammar_ingestion_generation_v3.md` dynamically
- Output: full V3 annotation including classification, option analysis, reasoning, generation profile, confidence
- Rules context truncated to 8000 chars if file is large

### `generate_prompt.py`
- System: DSAT generation specialist
- Output: complete question + full V3 annotation
- Rules: 20-40 word passages for sentence_only, formal register, self-contained, at least one distractor targets the syntactic trap, no duplicate failure reasons
