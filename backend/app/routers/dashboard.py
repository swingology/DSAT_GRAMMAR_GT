"""Local admin dashboard for ingestion, generation, and inspection."""
import json
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import admin_required
from app.database import get_db
from app.models.db import QuestionJob, Question, QuestionOption
from app.routers.admin import list_generated_questions

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
async def dashboard(_auth: str = Depends(admin_required)):
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
async def review_queue_page(_auth: str = Depends(admin_required)):
    return HTMLResponse(_REVIEW_PAGE)


@router.get("/review-items", response_class=HTMLResponse)
async def review_items_fragment(
    generation_batch_id: str | None = None,
    requested_by: str | None = None,
    student_id: int | None = None,
    domain: str | None = None,
    grammar_role_key: str | None = None,
    grammar_focus_key: str | None = None,
    reading_skill_family_key: str | None = None,
    reading_focus_key: str | None = None,
    difficulty: str | None = None,
    generator_provider: str | None = None,
    generator_model: str | None = None,
    reviewer_provider: str | None = None,
    reviewer_model: str | None = None,
    min_average_realism: float | None = None,
    consensus_verdict: str | None = None,
    min_reviewer_disagreement: float | None = None,
    overlap_status: str | None = None,
    practice_status: str | None = Query("draft"),
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    data = await list_generated_questions(
        generation_batch_id=generation_batch_id or None,
        requested_by=requested_by or None,
        student_id=student_id,
        domain=domain or None,
        grammar_role_key=grammar_role_key or None,
        grammar_focus_key=grammar_focus_key or None,
        reading_skill_family_key=reading_skill_family_key or None,
        reading_focus_key=reading_focus_key or None,
        difficulty=difficulty or None,
        generator_provider=generator_provider or None,
        generator_model=generator_model or None,
        reviewer_provider=reviewer_provider or None,
        reviewer_model=reviewer_model or None,
        min_average_realism=min_average_realism,
        consensus_verdict=consensus_verdict or None,
        min_reviewer_disagreement=min_reviewer_disagreement,
        overlap_status=overlap_status or None,
        practice_status=practice_status or None,
        created_from=created_from or None,
        created_to=created_to or None,
        limit=limit,
        offset=offset,
        db=db,
        _auth=_auth,
    )
    items = data["items"]

    if not items:
        return HTMLResponse(
            '<p class="text-sm text-slate-400 text-center py-10">'
            'No generated candidates match the current filters.</p>'
        )

    cards = []
    for item in items:
        qid_str = item["id"]
        q_short = qid_str[:8]
        job = item.get("job") or {}
        job_id_str = job.get("id") or ""
        batch = item.get("batch") or {}
        consensus = item.get("consensus") or {}
        review_results = item.get("review_results") or []
        annotation = item.get("annotation") or {}
        request = job.get("generation_request_jsonb") or {}
        source_examples = item.get("source_examples") or []
        errors = job.get("validation_errors_jsonb") or []
        correct = item.get("correct_option_label")

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
            # validate_question warnings use field/message; qnum and OCR
            # cross-check warnings use step/issue/detail — fall back across both.
            w_field = e.get("field") or e.get("step") or ""
            w_msg = e.get("message") or e.get("detail") or e.get("issue") or ""
            err_html += (
                f'<div class="flex items-start gap-2 text-amber-700 text-xs">'
                f'<span class="font-bold mt-0.5">WARN</span>'
                f'<span>{_esc(w_field)} — {_esc(w_msg)}</span></div>'
            )

        opts_html = ""
        for opt in item.get("options", []):
            is_correct = opt.get("label") == correct
            bg = "bg-emerald-50 border-emerald-300 text-emerald-800" if is_correct else "bg-slate-50 border-slate-200 text-slate-700"
            opts_html += (
                f'<div class="flex items-start gap-2 rounded-lg border px-3 py-2 text-sm {bg}">'
                f'<span class="font-mono font-bold min-w-[1.2rem]">{_esc(opt.get("label") or "")}</span>'
                f'<span>{_esc(opt.get("text") or "")}</span>'
                f'</div>'
            )
        if not opts_html:
            opts_html = '<p class="text-xs text-slate-400 italic">No options stored.</p>'

        def _truncate(t):
            if not t:
                return '<span class="italic text-slate-400">None</span>'
            escaped = _esc(t[:500] + "…" if len(t) > 500 else t)
            return f'<p class="text-sm text-slate-800 leading-snug whitespace-pre-wrap">{escaped}</p>'

        review_rows = ""
        for review in review_results:
            scores = review.get("scores_jsonb") or {}
            review_rows += f"""
        <tr class="border-b border-slate-100">
          <td class="py-1.5 pr-2 text-xs">{_esc(review.get("provider_name") or "")}</td>
          <td class="py-1.5 pr-2 text-xs">{_esc(review.get("model_name") or "")}</td>
          <td class="py-1.5 pr-2 text-xs">{_esc(review.get("verdict") or "")}</td>
          <td class="py-1.5 pr-2 text-xs tabular-nums">{scores.get("realism_score", "—")}</td>
          <td class="py-1.5 pr-2 text-xs tabular-nums">{scores.get("sat_fidelity_score", "—")}</td>
          <td class="py-1.5 pr-2 text-xs tabular-nums">{scores.get("copy_risk_score", "—")}</td>
          <td class="py-1.5 text-xs text-slate-500">{_esc(review.get("review_notes") or review.get("error_message") or "")}</td>
        </tr>"""
        if not review_rows:
            review_rows = '<tr><td colspan="7" class="py-2 text-xs text-slate-400">No review results yet.</td></tr>'

        source_rows = ""
        for source in source_examples:
            source_rows += f"""
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-1">
          <div class="flex gap-2 text-xs text-slate-500">
            <span class="font-mono">{_esc(source.get("id", "")[:8])}…</span>
            <span>{_esc(source.get("source_exam_code") or "")} {_esc(source.get("source_module_code") or "")} Q{_esc(source.get("source_question_number") or "")}</span>
            <span>correct {_esc(source.get("correct_option_label") or "")}</span>
          </div>
          <p class="text-sm text-slate-800">{_esc(source.get("question_text") or "")}</p>
        </div>"""
        if not source_rows:
            source_rows = '<p class="text-xs text-slate-400">No source examples recorded.</p>'

        request_keys = [
            "target_grammar_role_key", "target_grammar_focus_key",
            "target_reading_skill_family_key", "target_skill_family_key",
            "target_reading_focus_key", "difficulty_overall",
            "stimulus_mode_key", "stem_type_key",
        ]
        request_summary = {key: request.get(key) for key in request_keys if request.get(key)}
        annotation_keys = [
            "grammar_role_key", "grammar_focus_key",
            "reading_skill_family_key", "reading_focus_key",
            "difficulty_overall", "stimulus_mode_key", "stem_type_key",
        ]
        annotation_summary = {key: annotation.get(key) for key in annotation_keys if annotation.get(key)}

        passage_block = _truncate(item.get("passage_text"))
        underlined_block = (
            f'<div class="mt-2 rounded border border-amber-200 bg-amber-50 px-3 py-2">'
            f'<p class="text-xs font-semibold text-amber-700 mb-1">Underlined portion</p>'
            f'<p class="text-sm text-slate-800">{_esc(item.get("underlined_text"))}</p></div>'
        ) if item.get("underlined_text") else ""
        consensus_chip = consensus.get("consensus_verdict") or "not_reviewed"
        overlap_chip = item.get("official_overlap_status") or "none"
        rejection_html = (
            f'<div class="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">'
            f'<span class="font-semibold">Reject reason:</span> {_esc(item.get("rejection_reason"))}</div>'
            if item.get("rejection_reason")
            else ""
        )
        generator_label = " ".join(
            part for part in [job.get("provider_name"), job.get("model_name")] if part
        ) or "unknown generator"
        reviewer_disagreement = consensus.get("reviewer_disagreement")
        average_realism = consensus.get("average_realism")
        batch_label = batch.get("id", "")[:8] + "…" if batch.get("id") else "no batch"
        requested_by = batch.get("requested_by") or "unknown"
        student_origin = batch.get("student_id")
        student_label = f"student {student_origin}" if student_origin is not None else "admin/profile none"

        cards.append(f"""
<div class="card p-5 space-y-4" id="rq-{q_short}">
  <div class="flex flex-wrap items-center gap-3">
    <span class="font-semibold text-slate-800 text-base">{_esc(item.get("domain") or "generated")}</span>
    <span class="chip chip-soft">{_esc(item.get("practice_status") or "")}</span>
    <span class="chip chip-soft">{_esc(consensus_chip)}</span>
    <span class="chip chip-soft">overlap {_esc(overlap_chip)}</span>
    <span class="chip chip-soft">realism {_esc(average_realism if average_realism is not None else "—")}</span>
    <span class="chip chip-soft">disagreement {_esc(reviewer_disagreement if reviewer_disagreement is not None else "—")}</span>
    <span class="text-xs text-slate-400 font-mono">{qid_str[:12]}…</span>
    <div class="ml-auto flex gap-2">
      <button onclick="rqReviewSwarm('{qid_str}')"
              class="btn btn-sky text-xs px-3 py-1.5 w-auto">Re-review</button>
      <button onclick="rqRegenerate('{qid_str}')"
              class="btn btn-slate text-xs px-3 py-1.5 w-auto">Regenerate</button>
      <button onclick="rqApprove('{qid_str}')"
              class="btn btn-emerald text-xs px-3 py-1.5 w-auto">Approve</button>
      <button onclick="rqReject('{qid_str}')"
              class="btn btn-red text-xs px-3 py-1.5 w-auto">Reject</button>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600">Batch</p>
      <p class="font-mono text-slate-700">{_esc(batch_label)}</p>
      <p class="text-slate-500">requested by {_esc(requested_by)}</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600">Origin</p>
      <p class="text-slate-700">{_esc(student_label)}</p>
      <p class="text-slate-500">{_esc(batch.get("release_policy") or "")}</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600">Generator</p>
      <p class="text-slate-700">{_esc(generator_label)}</p>
      <p class="font-mono text-slate-500">{_esc(job_id_str[:8] + "…" if job_id_str else "no job")}</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600">Created</p>
      <p class="text-slate-700">{_esc(item.get("created_at") or "—")}</p>
      <p class="text-slate-500">updated {_esc(item.get("updated_at") or "—")}</p>
    </div>
  </div>

  <div class="space-y-1 rounded-lg border border-red-100 bg-red-50 p-3">
    {err_html or '<span class="text-xs text-slate-400">No validation errors recorded.</span>'}
  </div>
  {rejection_html}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <div class="space-y-1">
      <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Question</p>
      <p class="text-sm text-slate-800 leading-snug">{_esc(item.get("question_text") or "")}</p>
    </div>
    <div class="space-y-1">
      <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">{'Text 1 / Passage' if item.get("paired_passage_text") else 'Passage'}</p>
      {passage_block}
      {underlined_block}
      {'<p class="text-xs font-medium text-slate-500 uppercase tracking-wide mt-2">Text 2 (paired)</p>' + _truncate(item.get("paired_passage_text")) if item.get("paired_passage_text") else ""}
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 text-xs">
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600 mb-1">Requested target</p>
      <pre class="whitespace-pre-wrap text-slate-700">{_esc(json.dumps(request_summary, indent=2))}</pre>
    </div>
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600 mb-1">Actual annotation</p>
      <pre class="whitespace-pre-wrap text-slate-700">{_esc(json.dumps(annotation_summary, indent=2))}</pre>
    </div>
    <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p class="font-semibold text-slate-600 mb-1">Consensus reasons</p>
      <pre class="whitespace-pre-wrap text-slate-700">{_esc(json.dumps(consensus.get("reasons_jsonb") or [], indent=2))}</pre>
    </div>
  </div>

  <div class="space-y-2">
    <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Options</p>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">{opts_html}</div>
    <p class="text-xs text-slate-600">Correct answer: <span class="font-mono font-semibold">{_esc(correct or "—")}</span></p>
  </div>

  <div class="space-y-1 rounded-lg border border-slate-200 bg-white p-3">
    <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Explanation</p>
    {_truncate(item.get("explanation_text"))}
  </div>

  <div class="space-y-2">
    <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Review swarm scores and notes</p>
    <div class="overflow-x-auto">
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-slate-200 text-xs text-slate-400">
            <th class="py-1.5 pr-2 font-medium">Provider</th>
            <th class="py-1.5 pr-2 font-medium">Model</th>
            <th class="py-1.5 pr-2 font-medium">Verdict</th>
            <th class="py-1.5 pr-2 font-medium">Realism</th>
            <th class="py-1.5 pr-2 font-medium">SAT</th>
            <th class="py-1.5 pr-2 font-medium">Copy</th>
            <th class="py-1.5 font-medium">Notes</th>
          </tr>
        </thead>
        <tbody>{review_rows}</tbody>
      </table>
    </div>
  </div>

  <details class="group" id="sources-{q_short}">
    <summary class="cursor-pointer text-xs font-semibold text-sky-600 hover:text-sky-800 select-none">Compare with official source examples</summary>
    <div class="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-3">{source_rows}</div>
  </details>

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
        <textarea name="question_text" rows="3" class="inp text-sm">{_esc(item.get("question_text") or "")}</textarea>
      </div>
      <div class="field">
        <label class="text-xs text-slate-500">Passage text (Text 1)</label>
        <textarea name="passage_text" rows="4" class="inp text-sm">{_esc(item.get("passage_text") or "")}</textarea>
      </div>
      <div class="field">
        <label class="text-xs text-slate-500">Text 2 / Paired passage (compare questions — leave blank if single passage)</label>
        <textarea name="paired_passage_text" rows="4" class="inp text-sm">{_esc(item.get("paired_passage_text") or "")}</textarea>
      </div>
      <div class="field">
        <label class="text-xs text-slate-500">Underlined portion (exact text that is underlined in the passage — leave blank if none)</label>
        <textarea name="underlined_text" rows="2" class="inp text-sm">{_esc(item.get("underlined_text") or "")}</textarea>
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
      <div id="edit-result-{q_short}" class="text-xs text-slate-500"></div>
    </form>
  </details>
</div>""")

    count = len(items)
    next_offset = data.get("next_offset")
    current_offset = data.get("offset") or 0
    next_button_offset = next_offset if next_offset is not None else current_offset
    pager_html = f"""
    <div class="flex items-center justify-between mb-4">
      <p class="text-sm text-slate-500">{count} item{"s" if count != 1 else ""} need attention.</p>
      <div class="flex items-center gap-2">
        <button type="button" onclick="setReviewOffset({max(current_offset - limit, 0)})"
                class="btn btn-slate text-xs px-3 py-1.5 w-auto"
                {"disabled" if current_offset <= 0 else ""}>Previous</button>
        <span class="text-xs text-slate-400">offset {current_offset}</span>
        <button type="button" onclick="setReviewOffset({next_button_offset})"
                class="btn btn-slate text-xs px-3 py-1.5 w-auto"
                {"disabled" if next_offset is None else ""}>Next</button>
      </div>
    </div>"""
    return HTMLResponse(
        pager_html + "\n".join(cards)
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

  <main class="max-w-6xl mx-auto px-6 py-6 space-y-5">
    <form id="review-filter-form" class="card p-4 space-y-4" onsubmit="reloadQueue(); return false;">
      <div class="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-6 gap-3">
        <div class="field">
          <label>Batch ID</label>
          <input name="generation_batch_id" class="inp" placeholder="uuid">
        </div>
        <div class="field">
          <label>Requested by</label>
          <select name="requested_by" class="inp">
            <option value="">any</option>
            <option value="admin">admin</option>
            <option value="self_study_agent">self-study agent</option>
          </select>
        </div>
        <div class="field">
          <label>Student ID</label>
          <input name="student_id" type="number" min="1" class="inp" placeholder="any">
        </div>
        <div class="field">
          <label>Status</label>
          <select name="practice_status" class="inp">
            <option value="draft" selected>draft</option>
            <option value="rejected">rejected</option>
            <option value="active">active</option>
            <option value="">any</option>
          </select>
        </div>
        <div class="field">
          <label>Domain</label>
          <select name="domain" class="inp">
            <option value="">any</option>
            <option value="grammar">grammar</option>
            <option value="reading">reading</option>
          </select>
        </div>
        <div class="field">
          <label>Overlap</label>
          <select name="overlap_status" class="inp">
            <option value="">any</option>
            <option value="none">none</option>
            <option value="possible">possible</option>
            <option value="confirmed">confirmed</option>
          </select>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-6 gap-3">
        <div class="field">
          <label>Grammar role</label>
          <input name="grammar_role_key" class="inp" placeholder="role key">
        </div>
        <div class="field">
          <label>Grammar focus</label>
          <input name="grammar_focus_key" class="inp" placeholder="focus key">
        </div>
        <div class="field">
          <label>Reading family</label>
          <input name="reading_skill_family_key" class="inp" placeholder="family key">
        </div>
        <div class="field">
          <label>Reading focus</label>
          <input name="reading_focus_key" class="inp" placeholder="focus key">
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
        <div class="field">
          <label>Consensus</label>
          <select name="consensus_verdict" class="inp">
            <option value="">any</option>
            <option value="blocked_overlap">blocked_overlap</option>
            <option value="reject_recommended">reject_recommended</option>
            <option value="regenerate_recommended">regenerate_recommended</option>
            <option value="insufficient_reviews">insufficient_reviews</option>
            <option value="admin_review_ready">admin_review_ready</option>
          </select>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-7 gap-3">
        <div class="field">
          <label>Generator provider</label>
          <input name="generator_provider" class="inp" placeholder="openai">
        </div>
        <div class="field">
          <label>Generator model</label>
          <input name="generator_model" class="inp" placeholder="model">
        </div>
        <div class="field">
          <label>Reviewer provider</label>
          <input name="reviewer_provider" class="inp" placeholder="anthropic">
        </div>
        <div class="field">
          <label>Reviewer model</label>
          <input name="reviewer_model" class="inp" placeholder="model">
        </div>
        <div class="field">
          <label>Min realism</label>
          <input name="min_average_realism" type="number" min="0" max="10" step="0.1" class="inp" placeholder="0-10">
        </div>
        <div class="field">
          <label>Min disagreement</label>
          <input name="min_reviewer_disagreement" type="number" min="0" step="0.1" class="inp" placeholder="0.0">
        </div>
        <div class="field">
          <label>Limit</label>
          <input name="limit" type="number" min="1" max="100" value="25" class="inp">
        </div>
        <div class="field">
          <label>Offset</label>
          <input name="offset" type="number" min="0" value="0" class="inp">
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto_auto] gap-3 items-end">
        <div class="field">
          <label>Created from</label>
          <input name="created_from" type="datetime-local" class="inp">
        </div>
        <div class="field">
          <label>Created to</label>
          <input name="created_to" type="datetime-local" class="inp">
        </div>
        <button type="submit" class="btn btn-sky text-xs px-4 py-2">Apply filters</button>
        <button type="button" onclick="resetFilters()" class="btn btn-slate text-xs px-4 py-2">Reset</button>
      </div>
    </form>

    <div id="review-queue">
      <p class="text-sm text-slate-400 text-center py-10">Loading review queue...</p>
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

    function reviewQueryString() {
      const form = document.getElementById('review-filter-form');
      const params = new URLSearchParams();
      for (const [key, value] of new FormData(form).entries()) {
        const trimmed = String(value).trim();
        if (trimmed) params.set(key, trimmed);
      }
      return params.toString();
    }

    async function reloadQueue() {
      const el = document.getElementById('review-queue');
      el.innerHTML = '<p class="text-sm text-slate-400 text-center py-10">Refreshing…</p>';
      const query = reviewQueryString();
      const path = '/dashboard/review-items' + (query ? '?' + query : '');
      try {
        const headers = {};
        const key = getKey();
        if (key) headers['X-API-Key'] = key;
        const res = await fetch(path, { headers });
        const html = await res.text();
        if (!res.ok) throw { status: res.status, data: html };
        el.innerHTML = html;
      } catch(err) {
        el.innerHTML = '<p class="text-sm text-red-700 text-center py-10">Review queue load failed: ' +
          String(err.data || err.status || err).slice(0, 180) + '</p>';
      }
    }

    function resetFilters() {
      document.getElementById('review-filter-form').reset();
      reloadQueue();
    }

    function setReviewOffset(offset) {
      const input = document.querySelector('#review-filter-form [name="offset"]');
      if (input) input.value = String(Math.max(0, Number(offset) || 0));
      reloadQueue();
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
        const res = await apiFetch('/admin/generated-questions/' + qid + '/approve', { method: 'POST' });
        log('Approved ' + qid.slice(0,8) + '… — removing from queue');
        if (res.reviewer_admin_override_count !== undefined) {
          log('Captured ' + res.reviewer_admin_override_count + ' reviewer/admin override rows');
        }
        const card = document.getElementById('rq-' + qid.slice(0,8));
        if (card) { card.style.opacity = '0.4'; card.style.pointerEvents = 'none'; }
      } catch(err) {
        log('Approve failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    async function rqReject(qid) {
      const reason = prompt('Reject reason for audit trail:', 'admin rejected from review queue');
      if (reason === null) return;
      try {
        const res = await apiFetch('/admin/generated-questions/' + qid + '/reject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason }),
        });
        log('Rejected ' + qid.slice(0,8) + '…');
        if (res.reviewer_admin_override_count !== undefined) {
          log('Captured ' + res.reviewer_admin_override_count + ' reviewer/admin override rows');
        }
        const card = document.getElementById('rq-' + qid.slice(0,8));
        if (card) { card.style.opacity = '0.4'; card.style.pointerEvents = 'none'; }
      } catch(err) {
        log('Reject failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    async function rqReviewSwarm(qid) {
      try {
        const res = await apiFetch('/admin/questions/' + qid + '/review-swarm', { method: 'POST' });
        log('Review swarm completed for ' + qid.slice(0,8) + '… status=' + (res.status || '?'));
        await reloadQueue();
      } catch(err) {
        log('Review swarm failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    async function rqRegenerate(qid) {
      if (!confirm('Create a new single-question batch from this candidate spec?')) return;
      try {
        const res = await apiFetch('/admin/generated-questions/' + qid + '/regenerate', { method: 'POST' });
        log('Regeneration batch queued: ' + (res.batch_id || '').slice(0,8) + '…');
      } catch(err) {
        log('Regenerate failed: ' + JSON.stringify(err.data).slice(0, 100), false);
      }
    }

    reloadQueue();
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
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Release Year</label>
                  <input name="source_release_year" class="inp" placeholder="2025">
                </div>
                <div class="field">
                  <label>Test Name</label>
                  <input name="source_test_name" class="inp" placeholder="Bluebook Practice Test 1">
                </div>
              </div>
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
                  <input name="model_name" class="inp" value="deepseek-v4-pro:cloud">
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
                  <input name="model_name" class="inp" value="deepseek-v4-pro:cloud">
                </div>
              </div>
              <div class="field">
                <label>PDF File</label>
                <input type="file" name="file" accept=".pdf,application/pdf" required
                       class="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-amber-50 file:px-3 file:py-2 file:font-medium file:text-amber-700 hover:file:bg-amber-100">
              </div>
              <div class="note">
                Scanned PDFs use GLM OCR through Ollama, then DeepSeek V4 Pro through Ollama for text extraction.
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
                  <input name="model_name" class="inp" value="deepseek-v4-pro:cloud">
                </div>
                <div class="field">
                  <label>Exam Code</label>
                  <input name="source_exam_code" class="inp" placeholder="PT11">
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Release Year</label>
                  <input name="source_release_year" class="inp" placeholder="2025">
                </div>
                <div class="field">
                  <label>Test Name</label>
                  <input name="source_test_name" class="inp" placeholder="Bluebook Practice Test 1">
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
                  <input name="target_grammar_role_key" class="inp" placeholder="sentence_structure_boundaries">
                </div>
                <div class="field">
                  <label>Grammar Focus Key</label>
                  <input name="target_grammar_focus_key" class="inp" placeholder="comma_splice">
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label>Reading Skill Family Key</label>
                  <input name="target_reading_skill_family_key" class="inp" placeholder="words_in_context">
                </div>
                <div class="field">
                  <label>Reading Focus Key</label>
                  <input name="target_reading_focus_key" class="inp" placeholder="figurative_language_meaning">
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
              <div class="field">
                <label>Test Construct Key</label>
                <input name="target_test_construct_key" class="inp" placeholder="figurative_interpretation_precision">
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
                  <input name="model_name" class="inp" value="deepseek-v4-pro:cloud">
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
      ollama: 'deepseek-v4-pro:cloud',
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
        difficulty_overall: formData.get('difficulty_overall') || 'medium',
        provider_name: formData.get('provider_name') || null,
        model_name: formData.get('model_name') || null,
      };
      [
        'target_grammar_role_key',
        'target_grammar_focus_key',
        'target_syntactic_trap_key',
        'target_reading_skill_family_key',
        'target_reading_focus_key',
        'target_test_construct_key',
      ].forEach((key) => {
        const value = String(formData.get(key) || '').trim();
        if (value) {
          body[key] = value;
        }
      });
      if (!body.target_syntactic_trap_key && body.target_grammar_role_key) {
        body.target_syntactic_trap_key = 'none';
      }
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
