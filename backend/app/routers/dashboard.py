"""Local admin dashboard for ingestion, generation, and inspection."""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import admin_required
from app.database import get_db
from app.models.db import QuestionJob, Question, QuestionOption

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_STATUS_CLASS = {
    "approved": "bg-green-100 text-green-700",
    "failed": "bg-red-100 text-red-700",
    "needs_review": "bg-yellow-100 text-yellow-800",
    "pending": "bg-slate-100 text-slate-500",
}
_IN_PROGRESS = {
    "parsing",
    "extracting",
    "generating",
    "annotating",
    "overlap_checking",
    "validating",
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
    for job in jobs:
        cls = _STATUS_CLASS.get(
            job.status,
            (
                "bg-blue-100 text-blue-700"
                if job.status in _IN_PROGRESS
                else "bg-slate-100 text-slate-500"
            ),
        )
        source_meta = (job.pass1_json or {}).get("source_metadata", {}) if isinstance(job.pass1_json, dict) else {}
        subject_code = source_meta.get("source_subject_code") or "—"
        section_code = source_meta.get("source_section_code") or "—"
        module_code = source_meta.get("source_module_code") or "—"
        q_cell = (
            f'<button class="font-mono text-xs text-blue-600 hover:text-blue-800" '
            f'onclick="loadQuestion(\\"{job.question_id}\\")">{str(job.question_id)[:8]}…</button>'
            if job.question_id
            else '<span class="text-slate-300">—</span>'
        )
        created = job.created_at.strftime("%m/%d %H:%M:%S") if job.created_at else "—"
        rows.append(
            f"""
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
          <td class="py-2 pr-4">
            <button class="font-mono text-xs text-slate-500 hover:text-slate-700"
                    onclick="loadJob('{job.id}')">{str(job.id)[:8]}…</button>
          </td>
          <td class="py-2 pr-4 text-sm">{job.job_type}</td>
          <td class="py-2 pr-4 text-sm">{job.content_origin}</td>
          <td class="py-2 pr-4 text-xs text-slate-500">{subject_code}</td>
          <td class="py-2 pr-4 text-xs text-slate-500">{section_code}</td>
          <td class="py-2 pr-4 text-xs text-slate-500">{module_code}</td>
          <td class="py-2 pr-4">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium {cls}">{job.status}</span>
          </td>
          <td class="py-2 pr-4">{q_cell}</td>
          <td class="py-2 text-xs text-slate-400 tabular-nums">{created}</td>
        </tr>"""
        )

    return HTMLResponse(
        f"""
    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-xs text-slate-400 uppercase tracking-wide border-b">
          <th class="pb-2 pr-4 font-medium">Job</th>
          <th class="pb-2 pr-4 font-medium">Type</th>
          <th class="pb-2 pr-4 font-medium">Origin</th>
          <th class="pb-2 pr-4 font-medium">Subject</th>
          <th class="pb-2 pr-4 font-medium">Section</th>
          <th class="pb-2 pr-4 font-medium">Module</th>
          <th class="pb-2 pr-4 font-medium">Status</th>
          <th class="pb-2 pr-4 font-medium">Question</th>
          <th class="pb-2 font-medium">Created</th>
        </tr>
      </thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""
    )


@router.get("/review", response_class=HTMLResponse)
async def review_queue_page():
    return HTMLResponse(_REVIEW_PAGE)


@router.get("/review-items", response_class=HTMLResponse)
async def review_items_fragment(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    rows = await db.execute(text("""
        WITH latest_job AS (
            SELECT DISTINCT ON (question_id)
                id as job_id,
                question_id,
                status,
                validation_errors_jsonb,
                created_at
            FROM question_jobs
            ORDER BY question_id, created_at DESC
        )
        SELECT
            q.id, q.source_exam_code, q.source_question_number, q.stem_type_key,
            q.content_origin, q.current_question_text, q.current_passage_text,
            q.current_correct_option_label, q.practice_status,
            lj.validation_errors_jsonb, lj.job_id
        FROM questions q
        JOIN latest_job lj ON lj.question_id = q.id
        WHERE lj.status = 'needs_review'
        ORDER BY q.source_exam_code NULLS LAST,
                 q.source_question_number::int NULLS LAST
    """))
    items = rows.fetchall()

    if not items:
        return HTMLResponse(
            '<p class="text-sm text-slate-400 text-center py-10">'
            'No items in review queue. Everything is approved or pending.</p>'
        )

    qids = [str(row[0]) for row in items]
    opts_result = await db.execute(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_([row[0] for row in items]))
        .order_by(QuestionOption.question_id, QuestionOption.option_label)
    )
    opts_by_qid: dict[str, list] = {}
    for opt in opts_result.scalars().all():
        key = str(opt.question_id)
        opts_by_qid.setdefault(key, []).append(opt)

    cards = []
    for row in items:
        qid, exam, qnum, stem, origin, qtext, ptext, correct, pstatus, errors, job_id = row
        qid_str = str(qid)
        job_id_str = str(job_id)

        errors = errors or []
        blocking = [e for e in errors if e.get("severity") == "blocking"]
        warnings = [e for e in errors if e.get("severity") != "blocking"]

        err_html = ""
        for e in blocking:
            err_html += (
                f'<div class="flex items-start gap-2 text-red-700 text-xs">'
                f'<span class="font-bold mt-0.5">BLOCKING</span>'
                f'<span>{_esc(e.get("field",""))} — {_esc(e.get("message",""))}</span></div>'
            )
        for e in warnings:
            err_html += (
                f'<div class="flex items-start gap-2 text-amber-700 text-xs">'
                f'<span class="font-bold mt-0.5">WARN</span>'
                f'<span>{_esc(e.get("field",""))} — {_esc(e.get("message",""))}</span></div>'
            )

        opts = opts_by_qid.get(qid_str, [])
        opts_html = ""
        for o in opts:
            is_correct = o.option_label == correct
            bg = "bg-emerald-50 border-emerald-300 text-emerald-800" if is_correct else "bg-slate-50 border-slate-200 text-slate-700"
            opts_html += (
                f'<div class="flex items-start gap-2 rounded-lg border px-3 py-2 text-sm {bg}">'
                f'<span class="font-mono font-bold min-w-[1.2rem]">{_esc(o.option_label)}</span>'
                f'<span>{_esc(o.option_text or "")}</span>'
                f'</div>'
            )
        if not opts_html:
            opts_html = '<p class="text-xs text-slate-400 italic">No options stored.</p>'

        source_label = f'{_esc(exam or "?")} Q{qnum or "?"}'
        origin_cls = {
            "official": "bg-blue-100 text-blue-700",
            "unofficial": "bg-amber-100 text-amber-700",
            "generated": "bg-violet-100 text-violet-700",
        }.get(origin or "", "bg-slate-100 text-slate-600")

        passage_display = _esc(ptext[:500] + "…" if ptext and len(ptext) > 500 else (ptext or "")) or '<span class="italic text-slate-400">None</span>'

        cards.append(f"""
<div class="card p-5 space-y-4" id="rq-{qid_str[:8]}">
  <div class="flex flex-wrap items-center gap-3">
    <span class="font-semibold text-slate-800 text-base">{source_label}</span>
    <span class="chip {origin_cls}">{_esc(origin or "?")}</span>
    <span class="chip chip-soft">{_esc(stem or "?")}</span>
    <span class="text-xs text-slate-400 font-mono">{qid_str[:12]}…</span>
    <div class="ml-auto flex gap-2">
      <button onclick="rqReannotate('{qid_str}','{job_id_str}')"
              class="btn btn-sky text-xs px-3 py-1.5 w-auto">Reannotate</button>
      <button onclick="rqApprove('{qid_str}')"
              class="btn btn-emerald text-xs px-3 py-1.5 w-auto">Approve</button>
      <button onclick="rqReject('{qid_str}')"
              class="btn btn-red text-xs px-3 py-1.5 w-auto">Reject</button>
    </div>
  </div>

  <div class="space-y-1 rounded-lg border border-red-100 bg-red-50 p-3">
    {err_html or '<span class="text-xs text-slate-400">No validation errors recorded.</span>'}
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <div class="space-y-1">
      <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Question</p>
      <p class="text-sm text-slate-800 leading-snug">{_esc(qtext or "")}</p>
    </div>
    <div class="space-y-1">
      <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Passage</p>
      <p class="text-sm text-slate-800 leading-snug">{passage_display}</p>
    </div>
  </div>

  <div class="space-y-2">
    <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Options</p>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">{opts_html}</div>
  </div>

  <details class="group">
    <summary class="cursor-pointer text-xs font-semibold text-sky-600 hover:text-sky-800 select-none list-none flex items-center gap-1">
      <svg class="w-3 h-3 rotate-0 group-open:rotate-90 transition-transform" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd"/>
      </svg>
      Edit question content
    </summary>
    <form class="mt-3 space-y-3" onsubmit="return rqSave(event, '{qid_str}')">
      <div class="field">
        <label class="text-xs text-slate-500">Question text</label>
        <textarea name="question_text" rows="3" class="inp text-sm">{_esc(qtext or "")}</textarea>
      </div>
      <div class="field">
        <label class="text-xs text-slate-500">Passage text (Text 1 if dual-passage; include Text 2 below)</label>
        <textarea name="passage_text" rows="4" class="inp text-sm">{_esc(ptext or "")}</textarea>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="field">
          <label class="text-xs text-slate-500">Correct option (A–D)</label>
          <input name="correct_option_label" class="inp text-sm" value="{_esc(correct or "")}" maxlength="1" pattern="[A-Da-d]">
        </div>
        <div class="field">
          <label class="text-xs text-slate-500">Change notes</label>
          <input name="change_notes" class="inp text-sm" placeholder="e.g. added paired passage">
        </div>
      </div>
      <div class="field">
        <label class="text-xs text-slate-500">Explanation (short)</label>
        <textarea name="explanation_text" rows="2" class="inp text-sm"></textarea>
      </div>
      <div class="flex gap-3">
        <button type="submit" class="btn btn-slate text-xs px-4 py-2 w-auto">Save edits</button>
        <button type="button" onclick="rqSaveThenReannotate('{qid_str}', '{job_id_str}', this.closest('form'))"
                class="btn btn-sky text-xs px-4 py-2 w-auto">Save + Reannotate</button>
      </div>
      <div id="edit-result-{qid_str[:8]}" class="text-xs text-slate-500"></div>
    </form>
  </details>
</div>""")

    count = len(items)
    return HTMLResponse(
        f'<p class="text-sm text-slate-500 mb-4">{count} item{"s" if count != 1 else ""} need attention.</p>'
        + "\n".join(cards)
    )


def _esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


_REVIEW_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Review Queue — DSAT Backend</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .field label { display:block; font-size:.72rem; color:#64748b; margin-bottom:.28rem; }
    .inp {
      width:100%; border:1px solid #cbd5e1; border-radius:.6rem;
      padding:.55rem .7rem; font-size:.88rem; color:#0f172a; background:#fff;
      outline:none; transition:border-color .15s, box-shadow .15s;
    }
    .inp:focus { border-color:#0ea5e9; box-shadow:0 0 0 3px rgba(14,165,233,.16); }
    textarea.inp { resize:vertical; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.8rem; }
    .card { background:#fff; border:1px solid #e2e8f0; border-radius:1rem; box-shadow:0 10px 30px rgba(15,23,42,.05); }
    .btn {
      display:inline-flex; align-items:center; justify-content:center; gap:.45rem;
      padding:.55rem .9rem; border-radius:.7rem; color:#fff; font-size:.82rem;
      font-weight:600; cursor:pointer; transition:filter .12s, transform .12s;
    }
    .btn:hover { filter:brightness(.94); }
    .btn:active { transform:translateY(1px); }
    .btn-sky { background:#0284c7; }
    .btn-emerald { background:#059669; }
    .btn-slate { background:#334155; }
    .btn-red { background:#dc2626; }
    .chip { display:inline-flex; align-items:center; padding:.16rem .55rem; border-radius:999px; font-size:.7rem; font-weight:600; }
    .chip-soft { background:#e2e8f0; color:#334155; }
  </style>
</head>
<body class="min-h-screen bg-slate-100 text-slate-900">
  <header class="bg-slate-950 text-white">
    <div class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <a href="/dashboard" class="text-slate-400 hover:text-white text-sm transition-colors">← Dashboard</a>
        <span class="text-slate-600">|</span>
        <h1 class="text-lg font-semibold tracking-tight">Review Queue</h1>
      </div>
      <div class="flex items-center gap-3">
        <label for="api-key" class="text-xs text-slate-400">API Key</label>
        <input id="api-key" type="password" placeholder="admin key"
               class="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 w-36"
               oninput="localStorage.setItem('dsatKey', this.value)">
        <button onclick="reloadQueue()"
                class="btn btn-sky text-xs px-3 py-1.5">Refresh</button>
      </div>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-6 py-6">
    <div id="review-queue"
         hx-get="/dashboard/review-items"
         hx-trigger="load"
         hx-swap="innerHTML">
      <p class="text-sm text-slate-400 text-center py-10">Loading review queue…</p>
    </div>
    <div id="action-log" class="mt-6 space-y-2"></div>
  </main>

  <script>
    const storedKey = localStorage.getItem('dsatKey');
    if (storedKey) document.getElementById('api-key').value = storedKey;

    document.addEventListener('htmx:configRequest', function(evt) {
      const key = document.getElementById('api-key').value.trim();
      if (key) evt.detail.headers['X-API-Key'] = key;
    });

    function getKey() { return document.getElementById('api-key').value.trim(); }

    async function apiFetch(path, opts = {}) {
      const headers = new Headers(opts.headers || {});
      const key = getKey();
      if (key) headers.set('X-API-Key', key);
      const res = await fetch(path, { ...opts, headers });
      const txt = await res.text();
      let data;
      try { data = txt ? JSON.parse(txt) : {}; } catch(_) { data = txt; }
      if (!res.ok) throw { status: res.status, data };
      return data;
    }

    function log(msg, ok = true) {
      const el = document.createElement('div');
      el.className = 'text-xs px-3 py-2 rounded-lg ' + (ok ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200');
      el.textContent = new Date().toLocaleTimeString() + ' — ' + msg;
      const container = document.getElementById('action-log');
      container.prepend(el);
      if (container.children.length > 10) container.lastChild.remove();
    }

    function reloadQueue() {
      const el = document.getElementById('review-queue');
      el.innerHTML = '<p class="text-sm text-slate-400 text-center py-10">Refreshing…</p>';
      htmx.trigger(el, 'load');
    }

    async function rqSave(evt, qid) {
      evt.preventDefault();
      const form = evt.target;
      const fd = new FormData(form);
      const body = {};
      for (const [k, v] of fd.entries()) { if (v.trim()) body[k] = v.trim(); }
      try {
        const res = await apiFetch('/admin/questions/' + qid, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const el = form.querySelector('[id^="edit-result-"]');
        if (el) el.textContent = 'Saved v' + res.version + ' (' + (res.changes || []).join(', ') + ')';
        log('Saved edits for ' + qid.slice(0, 8) + '…');
      } catch(err) {
        const msg = JSON.stringify(err.data).slice(0, 120);
        const el = form.querySelector('[id^="edit-result-"]');
        if (el) el.textContent = 'Error: ' + msg;
        log('Save failed: ' + msg, false);
      }
      return false;
    }

    async function rqReannotate(qid, jobId) {
      try {
        const res = await apiFetch('/ingest/reannotate/' + qid, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider_name: 'openai', model_name: 'gpt-4o' }),
        });
        log('Reannotate queued for ' + qid.slice(0,8) + '… job=' + (res.id||'?').slice(0,8));
      } catch(err) {
        log('Reannotate failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    async function rqSaveThenReannotate(qid, jobId, form) {
      const fd = new FormData(form);
      const body = {};
      for (const [k, v] of fd.entries()) { if (v.trim()) body[k] = v.trim(); }
      try {
        await apiFetch('/admin/questions/' + qid, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        log('Saved edits for ' + qid.slice(0,8) + '…');
        await rqReannotate(qid, jobId);
      } catch(err) {
        log('Save failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    async function rqApprove(qid) {
      try {
        await apiFetch('/admin/questions/' + qid + '/approve', { method: 'POST' });
        log('Approved ' + qid.slice(0,8) + '… — removing from queue');
        const card = document.getElementById('rq-' + qid.slice(0,8));
        if (card) { card.style.opacity = '0.4'; card.style.pointerEvents = 'none'; }
      } catch(err) {
        log('Approve failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    async function rqReject(qid) {
      if (!confirm('Mark this question as rejected/archived?')) return;
      try {
        await apiFetch('/admin/questions/' + qid + '/reject', { method: 'POST' });
        log('Rejected ' + qid.slice(0,8) + '…');
        const card = document.getElementById('rq-' + qid.slice(0,8));
        if (card) { card.style.opacity = '0.4'; card.style.pointerEvents = 'none'; }
      } catch(err) {
        log('Reject failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }
  </script>
</body>
</html>"""


_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DSAT Backend Builder Dashboard</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .field label { display:block; font-size:.72rem; color:#64748b; margin-bottom:.28rem; }
    .inp {
      width:100%;
      border:1px solid #cbd5e1;
      border-radius:.6rem;
      padding:.55rem .7rem;
      font-size:.88rem;
      color:#0f172a;
      background:#fff;
      outline:none;
      transition:border-color .15s, box-shadow .15s;
    }
    .inp:focus { border-color:#0ea5e9; box-shadow:0 0 0 3px rgba(14,165,233,.16); }
    textarea.inp { resize:vertical; min-height:7rem; font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.8rem; }
    .card {
      background:#fff;
      border:1px solid #e2e8f0;
      border-radius:1rem;
      box-shadow:0 10px 30px rgba(15,23,42,.05);
    }
    .btn {
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap:.45rem;
      width:100%;
      padding:.68rem .9rem;
      border-radius:.7rem;
      color:#fff;
      font-size:.88rem;
      font-weight:600;
      transition:transform .12s, filter .12s;
    }
    .btn:hover { filter:brightness(.96); }
    .btn:active { transform:translateY(1px); }
    .btn-sky { background:#0284c7; }
    .btn-emerald { background:#059669; }
    .btn-slate { background:#334155; }
    .btn-amber { background:#d97706; }
    .chip {
      display:inline-flex;
      align-items:center;
      gap:.35rem;
      padding:.16rem .5rem;
      border-radius:999px;
      font-size:.72rem;
      font-weight:600;
    }
    .chip-soft { background:#e2e8f0; color:#334155; }
    .mono-box {
      background:#0f172a;
      color:#dbeafe;
      border-radius:1rem;
      padding:1rem;
      font-size:.78rem;
      line-height:1.45;
      overflow:auto;
      white-space:pre-wrap;
      word-break:break-word;
      min-height:18rem;
    }
    .mini-json {
      background:#f8fafc;
      border:1px solid #e2e8f0;
      border-radius:.75rem;
      padding:.75rem;
      font-size:.75rem;
      line-height:1.4;
      color:#0f172a;
      white-space:pre-wrap;
      word-break:break-word;
      max-height:14rem;
      overflow:auto;
    }
    .note {
      border:1px solid #cbd5e1;
      border-radius:.8rem;
      background:#f8fafc;
      color:#334155;
      padding:.8rem .9rem;
      font-size:.8rem;
    }
  </style>
</head>
<body class="min-h-screen bg-slate-100 text-slate-900">
  <header class="bg-slate-950 text-white">
    <div class="max-w-7xl mx-auto px-6 py-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div class="space-y-2">
        <div class="flex items-center gap-2">
          <span class="chip chip-soft">local</span>
          <span class="text-xs uppercase tracking-[0.2em] text-slate-400">builder dashboard</span>
        </div>
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-semibold tracking-tight">DSAT backend control surface</h1>
          <a href="/dashboard/review"
             class="chip bg-amber-500 text-white hover:bg-amber-600 transition-colors text-xs px-3 py-1 rounded-full font-semibold">
            Review Queue
          </a>
        </div>
        <p class="text-sm text-slate-400 max-w-3xl">
          Use this page while the backend is still evolving: ingest official or unofficial source material,
          generate questions, poll jobs, inspect stored question payloads, and verify what the database persisted.
        </p>
      </div>
      <div class="w-full lg:w-[22rem] space-y-2">
        <label for="api-key" class="block text-xs uppercase tracking-wide text-slate-400">Admin API Key</label>
        <input id="api-key" type="password" placeholder="enter key"
               class="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
               oninput="localStorage.setItem('dsatKey', this.value)">
        <p class="text-xs text-slate-500">Used for all admin-only API requests from this page.</p>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-6 py-6 space-y-6">
    <section class="grid grid-cols-1 xl:grid-cols-12 gap-6">
      <div class="xl:col-span-7 space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section class="card p-5 space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="font-semibold text-slate-800">Official PDF ingest</h2>
                <p class="text-sm text-slate-500">Posts to <code>/ingest/official/pdf</code>.</p>
              </div>
              <span class="chip bg-blue-100 text-blue-700">official</span>
            </div>
            <form id="official-pdf-form" class="space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div class="field">
                  <label>Exam</label>
                  <input name="source_exam_code" class="inp" placeholder="PT11">
                </div>
                <div class="field">
                  <label>Subject</label>
                  <select name="source_subject_code" class="inp">
                    <option value="verbal" selected>Verbal</option>
                    <option value="math">Math</option>
                  </select>
                </div>
                <div class="field">
                  <label>Section</label>
                  <select name="source_section_code" class="inp">
                    <option value="01" selected>01</option>
                    <option value="02">02</option>
                  </select>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div class="field">
                  <label>Module</label>
                  <select name="source_module_code" class="inp">
                    <option value="01" selected>01</option>
                    <option value="02">02</option>
                  </select>
                </div>
                <div></div>
                <div></div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Provider</label>
                  <select name="provider_name" class="inp" onchange="syncModel(this)">
                    <option value="anthropic">Anthropic</option>
                    <option value="openai">OpenAI</option>
                    <option value="ollama" selected>Ollama</option>
                  </select>
                </div>
                <div class="field">
                  <label>Model</label>
                  <input name="model_name" class="inp" value="kimi-k2.6:cloud">
                </div>
              </div>
              <div class="field">
                <label>PDF File</label>
                <input type="file" name="file" accept=".pdf,application/pdf" required
                       class="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-50 file:px-3 file:py-2 file:font-medium file:text-blue-700 hover:file:bg-blue-100">
              </div>
              <button type="submit" class="btn btn-sky">Upload and ingest official PDF</button>
            </form>
            <div id="official-pdf-result" class="mini-json">Awaiting submission.</div>
          </section>

          <section class="card p-5 space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="font-semibold text-slate-800">Unofficial PDF ingest</h2>
                <p class="text-sm text-slate-500">Posts to <code>/ingest/unofficial/file</code>.</p>
              </div>
              <span class="chip bg-amber-100 text-amber-700">unofficial</span>
            </div>
            <form id="unofficial-pdf-form" class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Provider</label>
                  <select name="provider_name" class="inp" onchange="syncModel(this)">
                    <option value="anthropic">Anthropic</option>
                    <option value="openai">OpenAI</option>
                    <option value="ollama" selected>Ollama</option>
                  </select>
                </div>
                <div class="field">
                  <label>Model</label>
                  <input name="model_name" class="inp" value="kimi-k2.6:cloud">
                </div>
              </div>
              <div class="field">
                <label>PDF File</label>
                <input type="file" name="file" accept=".pdf,application/pdf" required
                       class="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-amber-50 file:px-3 file:py-2 file:font-medium file:text-amber-700 hover:file:bg-amber-100">
              </div>
              <div class="note">
                Image OCR is still not implemented. Use PDF here, or use the text path below if you already have raw content.
              </div>
              <button type="submit" class="btn btn-amber">Upload and ingest unofficial PDF</button>
            </form>
            <div id="unofficial-pdf-result" class="mini-json">Awaiting submission.</div>
          </section>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section class="card p-5 space-y-4">
            <div>
              <h2 class="font-semibold text-slate-800">Text ingest</h2>
              <p class="text-sm text-slate-500">Posts to <code>/ingest/text</code>.</p>
            </div>
            <form id="text-ingest-form" class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Origin</label>
                  <select name="content_origin" class="inp">
                    <option value="unofficial">Unofficial</option>
                    <option value="official">Official</option>
                  </select>
                </div>
                <div class="field">
                  <label>Provider</label>
                  <select name="provider_name" class="inp" onchange="syncModel(this)">
                    <option value="anthropic">Anthropic</option>
                    <option value="openai">OpenAI</option>
                    <option value="ollama" selected>Ollama</option>
                  </select>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Model</label>
                  <input name="model_name" class="inp" value="kimi-k2.6:cloud">
                </div>
                <div class="field">
                  <label>Exam Code</label>
                  <input name="source_exam_code" class="inp" placeholder="PT11">
                </div>
              </div>
              <div class="grid grid-cols-4 gap-3">
                <div class="field">
                  <label>Subject</label>
                  <select name="source_subject_code" class="inp">
                    <option value="verbal" selected>Verbal</option>
                    <option value="math">Math</option>
                  </select>
                </div>
                <div class="field">
                  <label>Section</label>
                  <select name="source_section_code" class="inp">
                    <option value="01" selected>01</option>
                    <option value="02">02</option>
                  </select>
                </div>
                <div class="field">
                  <label>Module</label>
                  <select name="source_module_code" class="inp">
                    <option value="01" selected>01</option>
                    <option value="02">02</option>
                  </select>
                </div>
                <div></div>
              </div>
              <div class="field">
                <label>Question Text</label>
                <textarea name="text" class="inp" required
                          placeholder="Paste the passage, question stem, and A-D choices here."></textarea>
              </div>
              <button type="submit" class="btn btn-emerald">Submit text for ingestion</button>
            </form>
            <div id="text-ingest-result" class="mini-json">Awaiting submission.</div>
          </section>

          <section class="card p-5 space-y-4">
            <div>
              <h2 class="font-semibold text-slate-800">Generate question</h2>
              <p class="text-sm text-slate-500">Posts JSON to <code>/generate/questions</code>.</p>
            </div>
            <form id="generate-form" class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Grammar Role Key</label>
                  <input name="target_grammar_role_key" class="inp" placeholder="sentence_structure_boundaries" required>
                </div>
                <div class="field">
                  <label>Grammar Focus Key</label>
                  <input name="target_grammar_focus_key" class="inp" placeholder="comma_splice" required>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Syntactic Trap Key</label>
                  <input name="target_syntactic_trap_key" class="inp" value="none">
                </div>
                <div class="field">
                  <label>Difficulty</label>
                  <select name="difficulty_overall" class="inp">
                    <option value="easy">easy</option>
                    <option value="medium" selected>medium</option>
                    <option value="hard">hard</option>
                  </select>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Provider</label>
                  <select name="provider_name" class="inp" onchange="syncModel(this)">
                    <option value="anthropic">Anthropic</option>
                    <option value="openai">OpenAI</option>
                    <option value="ollama" selected>Ollama</option>
                  </select>
                </div>
                <div class="field">
                  <label>Model</label>
                  <input name="model_name" class="inp" value="kimi-k2.6:cloud">
                </div>
              </div>
              <div class="field">
                <label>Source Question IDs</label>
                <input name="source_question_ids" class="inp" placeholder="uuid1, uuid2">
              </div>
              <button type="submit" class="btn btn-slate">Generate and store question</button>
            </form>
            <div id="generate-result" class="mini-json">Awaiting submission.</div>
          </section>
        </div>

        <section class="card p-5 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="font-semibold text-slate-800">Recent jobs</h2>
              <p class="text-sm text-slate-500">Auto-refreshes every 5 seconds.</p>
            </div>
            <span class="text-xs text-slate-400 tabular-nums" id="last-refresh">not loaded yet</span>
          </div>
          <div id="jobs-table"
               hx-get="/dashboard/jobs"
               hx-trigger="load, every 5s"
               hx-swap="innerHTML">
            <p class="text-sm text-slate-400 py-6 text-center">Loading jobs…</p>
          </div>
        </section>
      </div>

      <div class="xl:col-span-5 space-y-6">
        <section class="card p-5 space-y-4">
          <div>
            <h2 class="font-semibold text-slate-800">Inspect backend state</h2>
            <p class="text-sm text-slate-500">
              Pull live API responses to verify the database is storing what you expect.
            </p>
          </div>

          <div class="grid grid-cols-1 gap-4">
            <form id="job-lookup-form" class="space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-slate-700">Job or generation run</h3>
                <span class="chip chip-soft">read</span>
              </div>
              <div class="grid grid-cols-[1fr_auto] gap-3">
                <input name="lookup_id" class="inp" placeholder="job UUID or run UUID" required>
                <select name="lookup_kind" class="inp w-36">
                  <option value="job">ingest job</option>
                  <option value="run">generate run</option>
                </select>
              </div>
              <button type="submit" class="btn btn-slate">Fetch job state</button>
            </form>

            <form id="question-lookup-form" class="space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-slate-700">Question detail</h3>
                <span class="chip chip-soft">read</span>
              </div>
              <input name="question_id" class="inp" placeholder="question UUID" required>
              <div class="grid grid-cols-2 gap-3">
                <button type="submit" class="btn btn-emerald">Fetch question detail</button>
                <button type="button" class="btn btn-slate" onclick="loadQuestionVersionsFromForm()">Fetch versions</button>
              </div>
            </form>

            <form id="recall-form" class="space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-slate-700">Recall query</h3>
                <span class="chip chip-soft">read</span>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Origin</label>
                  <select name="origin" class="inp">
                    <option value="">any</option>
                    <option value="official">official</option>
                    <option value="unofficial">unofficial</option>
                    <option value="generated">generated</option>
                  </select>
                </div>
                <div class="field">
                  <label>Difficulty</label>
                  <select name="difficulty" class="inp">
                    <option value="">any</option>
                    <option value="easy">easy</option>
                    <option value="medium">medium</option>
                    <option value="hard">hard</option>
                  </select>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Grammar Focus</label>
                  <input name="grammar_focus" class="inp" placeholder="comma_splice">
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div class="field">
                    <label>Limit</label>
                    <input name="limit" type="number" min="1" max="100" value="10" class="inp">
                  </div>
                  <div class="field">
                    <label>Offset</label>
                    <input name="offset" type="number" min="0" value="0" class="inp">
                  </div>
                </div>
              </div>
              <button type="submit" class="btn btn-sky">Run recall query</button>
            </form>
          </div>

          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-700">Latest response</h3>
              <button type="button" class="text-xs text-slate-500 hover:text-slate-700" onclick="clearConsole()">Clear</button>
            </div>
            <pre id="console" class="mono-box">No API call yet.</pre>
          </div>
        </section>

        <section class="card p-5 space-y-3">
          <h2 class="font-semibold text-slate-800">What this page covers</h2>
          <ul class="space-y-2 text-sm text-slate-600">
            <li>Official PDF ingest with explicit exam, section, and module metadata.</li>
            <li>Unofficial PDF ingest and text ingest using the current backend routes.</li>
            <li>Generated-question creation using the live generation endpoint.</li>
            <li>Job polling, question detail lookup, version lookup, and recall queries.</li>
            <li>Raw JSON inspection so you can confirm metadata and storage shape without opening SQL first.</li>
          </ul>
        </section>
      </div>
    </section>
  </main>

  <script>
    const MODEL_DEFAULTS = {
      anthropic: 'claude-sonnet-4-6',
      openai: 'gpt-4o',
      ollama: 'kimi-k2.6:cloud',
    };

    const storedKey = localStorage.getItem('dsatKey');
    if (storedKey) {
      document.getElementById('api-key').value = storedKey;
    }

    document.addEventListener('htmx:configRequest', function (evt) {
      const key = getApiKey();
      if (key) {
        evt.detail.headers['X-API-Key'] = key;
      }
    });

    document.addEventListener('htmx:afterSettle', function (evt) {
      if (evt.detail.target.id === 'jobs-table') {
        document.getElementById('last-refresh').textContent =
          'last updated ' + new Date().toLocaleTimeString();
      }
    });

    function getApiKey() {
      return document.getElementById('api-key').value.trim();
    }

    function syncModel(sel) {
      const form = sel.closest('form');
      const modelInput = form.querySelector('[name="model_name"]');
      if (modelInput) {
        modelInput.value = MODEL_DEFAULTS[sel.value] || '';
      }
    }

    function showConsole(label, payload) {
      const target = document.getElementById('console');
      const body = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
      target.textContent = label + '\\n\\n' + body;
    }

    function clearConsole() {
      document.getElementById('console').textContent = 'No API call yet.';
    }

    function setMiniResult(targetId, label, payload) {
      const el = document.getElementById(targetId);
      if (!el) return;
      const body = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
      el.textContent = label + '\\n\\n' + body;
    }

    async function apiFetch(path, options = {}) {
      const headers = new Headers(options.headers || {});
      const key = getApiKey();
      if (key) {
        headers.set('X-API-Key', key);
      }
      const response = await fetch(path, { ...options, headers });
      const text = await response.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch (_) {
        data = text;
      }
      if (!response.ok) {
        throw { status: response.status, data };
      }
      return data;
    }

    function compactSummary(data) {
      if (!data || typeof data !== 'object') return '';
      if (data.id && data.status) {
        return 'id=' + data.id + ' status=' + data.status + (data.question_id ? ' question_id=' + data.question_id : '');
      }
      if (Array.isArray(data)) {
        return 'items=' + data.length;
      }
      return '';
    }

    async function submitFormData(formId, path, resultId) {
      const form = document.getElementById(formId);
      const data = new FormData(form);
      try {
        const payload = await apiFetch(path, {
          method: 'POST',
          body: data,
        });
        const summary = compactSummary(payload) || 'request succeeded';
        setMiniResult(resultId, summary, payload);
        showConsole(path, payload);
        form.reset();
      } catch (err) {
        setMiniResult(resultId, 'error ' + err.status, err.data);
        showConsole(path + ' failed', err.data);
      }
    }

    function parseCsvIds(raw) {
      return raw
        .split(',')
        .map((part) => part.trim())
        .filter(Boolean);
    }

    async function submitGenerateForm(evt) {
      evt.preventDefault();
      const form = document.getElementById('generate-form');
      const formData = new FormData(form);
      const body = {
        target_grammar_role_key: formData.get('target_grammar_role_key'),
        target_grammar_focus_key: formData.get('target_grammar_focus_key'),
        target_syntactic_trap_key: formData.get('target_syntactic_trap_key') || 'none',
        difficulty_overall: formData.get('difficulty_overall') || 'medium',
        provider_name: formData.get('provider_name') || null,
        model_name: formData.get('model_name') || null,
      };
      const sourceIds = parseCsvIds(String(formData.get('source_question_ids') || ''));
      if (sourceIds.length) {
        body.source_question_ids = sourceIds;
      }
      try {
        const payload = await apiFetch('/generate/questions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const summary = compactSummary(payload) || 'generation queued';
        setMiniResult('generate-result', summary, payload);
        showConsole('/generate/questions', payload);
      } catch (err) {
        setMiniResult('generate-result', 'error ' + err.status, err.data);
        showConsole('/generate/questions failed', err.data);
      }
    }

    async function loadJob(jobId) {
      const trimmed = String(jobId || '').trim();
      if (!trimmed) return;
      try {
        const payload = await apiFetch('/ingest/jobs/' + trimmed);
        showConsole('/ingest/jobs/' + trimmed, payload);
      } catch (err) {
        showConsole('/ingest/jobs/' + trimmed + ' failed', err.data);
      }
    }

    async function loadRun(runId) {
      const trimmed = String(runId || '').trim();
      if (!trimmed) return;
      try {
        const payload = await apiFetch('/generate/runs/' + trimmed);
        showConsole('/generate/runs/' + trimmed, payload);
      } catch (err) {
        showConsole('/generate/runs/' + trimmed + ' failed', err.data);
      }
    }

    async function loadQuestion(questionId) {
      const trimmed = String(questionId || '').trim();
      if (!trimmed) return;
      const formField = document.querySelector('#question-lookup-form [name="question_id"]');
      if (formField) formField.value = trimmed;
      try {
        const payload = await apiFetch('/questions/' + trimmed);
        showConsole('/questions/' + trimmed, payload);
      } catch (err) {
        showConsole('/questions/' + trimmed + ' failed', err.data);
      }
    }

    async function loadQuestionVersions(questionId) {
      const trimmed = String(questionId || '').trim();
      if (!trimmed) return;
      try {
        const payload = await apiFetch('/questions/' + trimmed + '/versions');
        showConsole('/questions/' + trimmed + '/versions', payload);
      } catch (err) {
        showConsole('/questions/' + trimmed + '/versions failed', err.data);
      }
    }

    function loadQuestionVersionsFromForm() {
      const questionId = document.querySelector('#question-lookup-form [name="question_id"]').value;
      loadQuestionVersions(questionId);
    }

    function buildRecallQuery(formData) {
      const params = new URLSearchParams();
      const fields = ['origin', 'difficulty', 'grammar_focus', 'limit', 'offset'];
      fields.forEach((field) => {
        const value = String(formData.get(field) || '').trim();
        if (value) params.set(field, value);
      });
      return '/questions/recall' + (params.toString() ? '?' + params.toString() : '');
    }

    document.getElementById('official-pdf-form').addEventListener('submit', function (evt) {
      evt.preventDefault();
      submitFormData('official-pdf-form', '/ingest/official/pdf', 'official-pdf-result');
    });

    document.getElementById('unofficial-pdf-form').addEventListener('submit', function (evt) {
      evt.preventDefault();
      submitFormData('unofficial-pdf-form', '/ingest/unofficial/file', 'unofficial-pdf-result');
    });

    document.getElementById('text-ingest-form').addEventListener('submit', function (evt) {
      evt.preventDefault();
      submitFormData('text-ingest-form', '/ingest/text', 'text-ingest-result');
    });

    document.getElementById('generate-form').addEventListener('submit', submitGenerateForm);

    document.getElementById('job-lookup-form').addEventListener('submit', function (evt) {
      evt.preventDefault();
      const formData = new FormData(evt.target);
      const lookupId = formData.get('lookup_id');
      const kind = formData.get('lookup_kind');
      if (kind === 'run') {
        loadRun(lookupId);
      } else {
        loadJob(lookupId);
      }
    });

    document.getElementById('question-lookup-form').addEventListener('submit', function (evt) {
      evt.preventDefault();
      const formData = new FormData(evt.target);
      loadQuestion(formData.get('question_id'));
    });

    document.getElementById('recall-form').addEventListener('submit', async function (evt) {
      evt.preventDefault();
      const path = buildRecallQuery(new FormData(evt.target));
      try {
        const payload = await apiFetch(path);
        showConsole(path, payload);
      } catch (err) {
        showConsole(path + ' failed', err.data);
      }
    });
  </script>
</body>
</html>"""
