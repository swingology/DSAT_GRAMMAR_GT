# DSAT Ingestion System: Frontend and Backend Responsibilities

Based on the architecture inside the project boundaries, the LLM "generation" (extracting question structure and annotating taxonomy metadata) relies on an asynchronous, **human-in-the-loop workflow** coordinating the frontend (SvelteKit) and the backend (FastAPI).

## The Specific Generation Flow

1. **Triggering Generation (Frontend `/ingest`):**
   - The user submits either an unstructured text block or a file block (PDF/MD) via `src/routes/ingest/+page.svelte`.
   - The frontend requests the backend via `POST /ingest` or `POST /ingest/file`.
   - The backend **immediately responds** with a Job ID, passing the heavy LLM processing to a background task so the frontend UI doesn't hang.

2. **The LLM Generation (Backend `pipeline`):**
   - The backend's orchestration runs a **Two-Pass Pipeline** on the background thread:
     - **Pass 1:** Submits the raw text to an LLM provider to extract the structural anatomy (stem, passage, choices, answers).
     - **Pass 2:** Submits the extracted output to the LLM to classify it against strict DSAT ontology bounds and rules.
   - Post-generation, the backend runs format validations and stores the pending results in a staging table (`question_ingestion_jobs`) under a `reviewed` or `draft` status.

3. **Coordination & Human Review (Frontend `/jobs`):**
   - The frontend's `src/routes/jobs/+page.svelte` acts as the system dashboard. It fetches the backend `GET /jobs` endpoint to reflect job status.
   - The human reviewer can open a job profile to inspect the LLM's Pass 1 extraction JSON alongside its Pass 2 annotation JSON.
   - The frontend interface delegates coordinate actions: 
     - **Rerun**: `POST /jobs/{id}/rerun` (commands the backend to rewrite the generation if it's flawed).
     - **Approve**: `PATCH /jobs/{id}/status` passing `approved`.

4. **Committing Generated Data (Backend `routers/jobs.py`):**
   - Upon receiving the frontend's approval, the backend maps the generated, cached JSON out of the staging job payload, performing irreversible structure upserts into the production tables (`questions`, `question_classifications`, `question_options`, `question_reasoning`, `question_generation_profiles`).

---

## Responsibilities Breakdown

### Frontend (SvelteKit)
* **Initiation Interface:** Provides the UX (`/ingest`) to dispatch unstructured test questions into the data pipeline constraints.
* **State Monitoring Coordination:** Observes asynchronous background processes by fetching statuses from the backend table endpoints, transforming them into color-coded job badges (`/jobs`).
* **Human-in-the-Loop Validation:** Supplies the side-by-side reading layout necessary for a subject matter expert to review the raw LLM output prior to database commit.
* **Flow Control:** Governs the "Approval pipeline"—instructing the backend when a generate job constitutes finalized production data or needs rerolling.

### Backend (FastAPI + Supabase)
* **Job Asynchronicity:** Prevents request timeouts by instantly registering API payloads into an ingest queue and executing generation requests (`router/ingest.py`) via `BackgroundTasks`.
* **LLM Prompt Strategy:** Houses system prompts and orchestrates inference calls dynamically ( Anthropic / OpenAI / OpenRouter / local Ollama ) based on config.
* **Sanity Testing / Data Validation:** Parses LLM outputs forcibly through resilient Pydantic schema validation. It catches hallucinated keylookups, incomplete enumerations, or invalid JSON, returning error feedback into the specific task.
* **Data Persistence:** Isolates all unvetted extraction inside of the staging jobs table, ensuring that AI hallucinations never break downstream logic.
* **Production Upserts:** Manages complicated 5-layer atomic SQL mappings when jobs are officially cleared by the frontend, preserving idempotent database logic.
* **Vector Embeddings (Out-of-band generation):** Asynchronously builds dense textual vectors across multiple text subsets (e.g., `passage_only`, `taxonomy_summary`) and serves them via pgvector cosine similarity (`POST /search`).
