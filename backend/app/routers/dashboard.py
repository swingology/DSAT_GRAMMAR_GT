"""HTMX ingestion dashboard.

Serves a single-page admin UI at GET /dashboard.
The jobs fragment at GET /dashboard/jobs returns an HTML table
refreshed every 5 s by HTMX — requires the admin API key header.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import admin_required
from app.models.db import QuestionJob

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_STATUS_CLASS = {
    "approved":     "bg-green-100 text-green-700",
    "failed":       "bg-red-100 text-red-700",
    "needs_review": "bg-yellow-100 text-yellow-800",
    "pending":      "bg-slate-100 text-slate-500",
}
_IN_PROGRESS = {
    "parsing", "extracting", "generating",
    "annotating", "overlap_checking", "validating",
}


@router.get("", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(_PAGE)


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_fragment(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    result = await db.execute(
        select(QuestionJob).order_by(QuestionJob.created_at.desc()).limit(30)
    )
    jobs = result.scalars().all()

    if not jobs:
        return HTMLResponse(
            '<p class="text-sm text-slate-400 text-center py-6">No jobs yet.</p>'
        )

    rows = []
    for j in jobs:
        cls = _STATUS_CLASS.get(
            j.status,
            "bg-blue-100 text-blue-700" if j.status in _IN_PROGRESS else "bg-slate-100 text-slate-500",
        )
        q_cell = (
            f'<span class="font-mono text-xs text-blue-500">{str(j.question_id)[:8]}…</span>'
            if j.question_id else '<span class="text-slate-300">—</span>'
        )
        created = j.created_at.strftime("%m/%d %H:%M:%S") if j.created_at else "—"
        rows.append(f"""
        <tr class="border-b border-slate-50 hover:bg-slate-50 transition-colors">
          <td class="py-2 pr-4 font-mono text-xs text-slate-400">{str(j.id)[:8]}…</td>
          <td class="py-2 pr-4 text-sm">{j.job_type}</td>
          <td class="py-2 pr-4 text-sm">{j.content_origin}</td>
          <td class="py-2 pr-4">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium {cls}">{j.status}</span>
          </td>
          <td class="py-2 pr-4">{q_cell}</td>
          <td class="py-2 text-xs text-slate-400 tabular-nums">{created}</td>
        </tr>""")

    return HTMLResponse(f"""
    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-xs text-slate-400 uppercase tracking-wide border-b">
          <th class="pb-2 pr-4 font-medium">Job</th>
          <th class="pb-2 pr-4 font-medium">Type</th>
          <th class="pb-2 pr-4 font-medium">Origin</th>
          <th class="pb-2 pr-4 font-medium">Status</th>
          <th class="pb-2 pr-4 font-medium">Question</th>
          <th class="pb-2 font-medium">Created</th>
        </tr>
      </thead>
      <tbody>{"".join(rows)}</tbody>
    </table>""")


# ── HTML page ──────────────────────────────────────────────────────────────

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DSAT Grammar — Ingestion Dashboard</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    [x-cloak] { display: none; }
    .field label { display:block; font-size:.7rem; color:#94a3b8; margin-bottom:.2rem; }
    .inp {
      width:100%; border:1px solid #e2e8f0; border-radius:.375rem;
      padding:.35rem .6rem; font-size:.85rem; color:#1e293b;
      outline:none; transition:box-shadow .15s;
    }
    .inp:focus { box-shadow: 0 0 0 3px #bfdbfe; border-color:#93c5fd; }
    select.inp { background:#fff; }
    textarea.inp { resize:vertical; font-family:monospace; font-size:.78rem; }
    .btn {
      display:block; width:100%; padding:.5rem; border-radius:.375rem;
      font-size:.85rem; font-weight:600; text-align:center;
      cursor:pointer; transition:filter .15s;
    }
    .btn:hover { filter:brightness(.92); }
    .btn-blue   { background:#2563eb; color:#fff; }
    .btn-amber  { background:#d97706; color:#fff; }
    .btn-green  { background:#059669; color:#fff; }
    .htmx-indicator { opacity:0; transition:opacity .2s; }
    .htmx-request .htmx-indicator { opacity:1; }
  </style>
</head>
<body class="bg-slate-100 min-h-screen font-sans">

<!-- ── Header ── -->
<header class="bg-slate-800 text-white px-6 py-3 flex items-center justify-between shadow">
  <div class="flex items-center gap-3">
    <span class="text-lg font-bold tracking-tight">DSAT Grammar</span>
    <span class="text-slate-400 text-sm">/ Ingestion Dashboard</span>
  </div>
  <div class="flex items-center gap-2">
    <label for="api-key" class="text-xs text-slate-400">Admin API Key</label>
    <input id="api-key" type="password" placeholder="enter key…"
           class="px-3 py-1.5 rounded bg-slate-700 border border-slate-600
                  text-sm text-white placeholder-slate-500 w-44 focus:outline-none
                  focus:ring-2 focus:ring-blue-400"
           oninput="localStorage.setItem('dsatKey', this.value)">
  </div>
</header>

<main class="max-w-7xl mx-auto px-6 py-6 space-y-6">

  <!-- ── Three upload panels ── -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-5">

    <!-- 1. Official PDF -->
    <div class="bg-white rounded-xl shadow-sm border-t-4 border-blue-500 p-5 space-y-4">
      <h2 class="font-semibold text-slate-700 flex items-center gap-2">
        <span class="text-blue-500">📄</span> Official PDF
      </h2>
      <form id="pdf-form"
            hx-post="/ingest/official/pdf"
            hx-encoding="multipart/form-data"
            hx-swap="none"
            hx-indicator="#pdf-spinner"
            class="space-y-3">

        <div class="grid grid-cols-3 gap-2">
          <div class="field">
            <label>Exam</label>
            <input name="source_exam_code" class="inp" placeholder="PT01">
          </div>
          <div class="field">
            <label>Section</label>
            <input name="source_section_code" class="inp" placeholder="S1">
          </div>
          <div class="field">
            <label>Module</label>
            <input name="source_module_code" class="inp" placeholder="M1">
          </div>
        </div>

        <div class="field">
          <label>Provider</label>
          <select name="provider_name" class="inp" onchange="syncModel(this)">
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
        </div>
        <div class="field">
          <label>Model</label>
          <input name="model_name" class="inp" value="claude-sonnet-4-6">
        </div>
        <div class="field">
          <label>PDF File <span class="text-red-400">*</span></label>
          <input type="file" name="file" accept=".pdf" required
                 class="text-sm text-slate-600 file:mr-3 file:py-1 file:px-3
                        file:rounded file:border-0 file:bg-blue-50 file:text-blue-700
                        file:text-sm file:font-medium hover:file:bg-blue-100">
        </div>

        <button type="submit" class="btn btn-blue">
          Upload &amp; Ingest
          <span id="pdf-spinner" class="htmx-indicator ml-1">⏳</span>
        </button>
      </form>
      <div id="pdf-result" class="text-sm"></div>
    </div>

    <!-- 2. Image Upload -->
    <div class="bg-white rounded-xl shadow-sm border-t-4 border-amber-400 p-5 space-y-4">
      <h2 class="font-semibold text-slate-700 flex items-center gap-2">
        <span class="text-amber-500">🖼</span> Image Upload
      </h2>

      <div class="flex gap-2">
        <button onclick="setImgOrigin('unofficial')" id="btn-img-unofficial"
                class="flex-1 py-1.5 rounded text-xs font-semibold border
                       bg-amber-100 text-amber-700 border-amber-300">
          Unofficial
        </button>
        <button onclick="setImgOrigin('official')" id="btn-img-official"
                class="flex-1 py-1.5 rounded text-xs font-semibold border
                       bg-slate-100 text-slate-500 border-slate-200">
          Official
        </button>
      </div>

      <div class="bg-amber-50 border border-amber-200 rounded p-2.5 text-xs text-amber-700">
        ⚠️ Image OCR is not yet implemented. Uploads will return a 422 error.
        Convert to PDF or paste text in the Text Entry panel instead.
      </div>

      <form id="img-form"
            hx-post="/ingest/unofficial/file"
            hx-encoding="multipart/form-data"
            hx-swap="none"
            hx-indicator="#img-spinner"
            class="space-y-3">

        <div class="field">
          <label>Provider</label>
          <select name="provider_name" class="inp" onchange="syncModel(this)">
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
        </div>
        <div class="field">
          <label>Model</label>
          <input name="model_name" class="inp" value="claude-sonnet-4-6">
        </div>
        <div class="field">
          <label>Image File <span class="text-red-400">*</span></label>
          <input type="file" name="file" accept="image/*" required
                 class="text-sm text-slate-600 file:mr-3 file:py-1 file:px-3
                        file:rounded file:border-0 file:bg-amber-50 file:text-amber-700
                        file:text-sm file:font-medium hover:file:bg-amber-100">
        </div>

        <button type="submit" class="btn btn-amber">
          Upload Image
          <span id="img-spinner" class="htmx-indicator ml-1">⏳</span>
        </button>
      </form>
      <div id="img-result" class="text-sm"></div>
    </div>

    <!-- 3. Text Entry -->
    <div class="bg-white rounded-xl shadow-sm border-t-4 border-emerald-500 p-5 space-y-4">
      <h2 class="font-semibold text-slate-700 flex items-center gap-2">
        <span class="text-emerald-500">✏️</span> Text Entry
      </h2>
      <form id="text-form"
            hx-post="/ingest/text"
            hx-swap="none"
            hx-indicator="#text-spinner"
            class="space-y-3">

        <div class="field">
          <label>Origin</label>
          <select name="content_origin" class="inp">
            <option value="unofficial">Unofficial</option>
            <option value="official">Official</option>
          </select>
        </div>

        <div class="grid grid-cols-3 gap-2">
          <div class="field">
            <label>Exam</label>
            <input name="source_exam_code" class="inp" placeholder="PT01">
          </div>
          <div class="field">
            <label>Section</label>
            <input name="source_section_code" class="inp" placeholder="S1">
          </div>
          <div class="field">
            <label>Module</label>
            <input name="source_module_code" class="inp" placeholder="M1">
          </div>
        </div>

        <div class="field">
          <label>Provider</label>
          <select name="provider_name" class="inp" onchange="syncModel(this)">
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
        </div>
        <div class="field">
          <label>Model</label>
          <input name="model_name" class="inp" value="claude-sonnet-4-6">
        </div>
        <div class="field">
          <label>Question Text <span class="text-red-400">*</span></label>
          <textarea name="text" rows="7" required
                    class="inp"
                    placeholder="Paste or type question text here…&#10;&#10;Include the passage, question stem, and all four answer choices."></textarea>
        </div>

        <button type="submit" class="btn btn-green">
          Submit for Ingestion
          <span id="text-spinner" class="htmx-indicator ml-1">⏳</span>
        </button>
      </form>
      <div id="text-result" class="text-sm"></div>
    </div>

  </div><!-- /grid -->

  <!-- ── Job queue ── -->
  <div class="bg-white rounded-xl shadow-sm p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-semibold text-slate-700">Recent Jobs</h2>
      <span class="text-xs text-slate-400 tabular-nums" id="last-refresh">—</span>
    </div>
    <div id="jobs-table"
         hx-get="/dashboard/jobs"
         hx-trigger="load, every 5s"
         hx-swap="innerHTML">
      <p class="text-sm text-slate-400 py-4 text-center">Loading…</p>
    </div>
  </div>

</main>

<script>
// ── Restore API key ────────────────────────────────────────────
const stored = localStorage.getItem('dsatKey');
if (stored) document.getElementById('api-key').value = stored;

// ── Inject API key into every HTMX request ─────────────────────
document.addEventListener('htmx:configRequest', function (evt) {
  const key = document.getElementById('api-key').value.trim();
  if (key) evt.detail.headers['X-API-Key'] = key;
});

// ── Update "last refreshed" timestamp ──────────────────────────
document.addEventListener('htmx:afterSettle', function (evt) {
  if (evt.detail.target.id === 'jobs-table') {
    document.getElementById('last-refresh').textContent =
      'last updated ' + new Date().toLocaleTimeString();
  }
});

// ── Render form responses as inline banners ─────────────────────
const RESULT_MAP = {
  'pdf-form':  'pdf-result',
  'img-form':  'img-result',
  'text-form': 'text-result',
};

document.addEventListener('htmx:afterRequest', function (evt) {
  const formId = evt.detail.elt.id;
  const resultId = RESULT_MAP[formId];
  if (!resultId) return;

  const target = document.getElementById(resultId);
  const xhr = evt.detail.xhr;

  let html;
  try {
    const data = JSON.parse(xhr.responseText);
    if (xhr.status >= 200 && xhr.status < 300) {
      html = `<div class="mt-2 flex items-start gap-2 bg-green-50 border border-green-200
                          rounded-lg p-3 text-xs text-green-800">
        <span class="text-green-500 text-base leading-none">✓</span>
        <div>
          Job <code class="font-mono font-bold">${data.id.slice(0,8)}…</code>
          created &mdash; status: <strong>${data.status}</strong>
        </div>
      </div>`;
    } else {
      html = `<div class="mt-2 flex items-start gap-2 bg-red-50 border border-red-200
                          rounded-lg p-3 text-xs text-red-700">
        <span class="text-red-500 text-base leading-none">✗</span>
        <div>${data.detail || xhr.responseText}</div>
      </div>`;
    }
  } catch (_) {
    html = `<pre class="mt-2 text-xs bg-slate-50 rounded p-2 overflow-auto">${xhr.responseText}</pre>`;
  }
  target.innerHTML = html;
});

// ── Sync default model when provider changes ────────────────────
const MODEL_DEFAULTS = {
  anthropic: 'claude-sonnet-4-6',
  openai:    'gpt-4o',
  ollama:    'qwen3.5:cloud',
};
function syncModel(sel) {
  const form = sel.closest('form');
  const modelInput = form.querySelector('[name="model_name"]');
  if (modelInput) modelInput.value = MODEL_DEFAULTS[sel.value] || '';
}

// ── Image origin toggle ─────────────────────────────────────────
function setImgOrigin(origin) {
  const unofficialBtn = document.getElementById('btn-img-unofficial');
  const officialBtn   = document.getElementById('btn-img-official');
  if (origin === 'unofficial') {
    unofficialBtn.className = unofficialBtn.className
      .replace(/bg-slate-100 text-slate-500 border-slate-200/, 'bg-amber-100 text-amber-700 border-amber-300');
    officialBtn.className = officialBtn.className
      .replace(/bg-amber-100 text-amber-700 border-amber-300/, 'bg-slate-100 text-slate-500 border-slate-200');
  } else {
    officialBtn.className = officialBtn.className
      .replace(/bg-slate-100 text-slate-500 border-slate-200/, 'bg-blue-100 text-blue-700 border-blue-300');
    unofficialBtn.className = unofficialBtn.className
      .replace(/bg-amber-100 text-amber-700 border-amber-300/, 'bg-slate-100 text-slate-500 border-slate-200');
  }
}
</script>

</body>
</html>"""
