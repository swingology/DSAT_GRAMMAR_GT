# Embeddings — Architecture & Overhead

## Where embeddings live

Embeddings are stored **permanently in PostgreSQL** (`question_embeddings` table), not in memory. Each row holds:
- `question_id` — FK to the question
- `embedding_type` — `full_item`, `passage_only`, `explanation`, `taxonomy_summary`, `generation_profile`
- `embedding vector(1536)` — the actual float array

No session memory. They're written once (when generated) and queried on demand.

---

## How recall/search works

When you POST to `/search` with a query string:

1. **Embed the query** — one API call to OpenAI (`text-embedding-3-small`) → 1536-dim vector
2. **Run a vector similarity query** in Postgres via pgvector:
   ```sql
   SELECT question_id, 1 - (embedding <=> $1) AS similarity
   FROM question_embeddings
   WHERE embedding_type = 'full_item'
   ORDER BY embedding <=> $1
   LIMIT 10;
   ```
   `<=>` is pgvector's cosine distance operator.
3. **Return the top-K matches** with their similarity scores.

---

## Overhead

| Step | Cost |
|------|------|
| Embedding the query | ~100–200ms (OpenAI API call) |
| IVFFlat vector search (66 questions) | <1ms — trivial at this scale |
| IVFFlat at 10K questions | ~5–20ms depending on `lists` config |
| IVFFlat at 100K questions | ~20–50ms |

**IVFFlat** is an approximate nearest-neighbor index — it partitions vectors into clusters (`lists`) and only searches the nearest cluster(s), not the full table. The trade-off is slight recall loss vs. flat scan, but at 66–1000 questions you'd barely notice either way.

No session or in-memory caching is planned. The bottleneck is always the embedding API call for the query, not the DB search. If you wanted to eliminate that, you could cache the query embedding in Redis for repeated identical searches, but that's overkill at this scale.

---

## Bottom line

The embeddings are a **persistent index in the database**, not RAM. The search overhead is dominated by the one outbound API call (~150ms), not the DB query. At 66–1000 questions, the vector search itself is essentially free.
