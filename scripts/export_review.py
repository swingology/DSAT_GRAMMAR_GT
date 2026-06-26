"""Export ingested questions to a markdown review file with tables and passages."""
import asyncio
import json
import os
import asyncpg


async def main():
    conn = await asyncpg.connect("postgresql://dsat:dsat_dev@localhost:5437/dsat_dev")

    job = await conn.fetchrow(
        "SELECT id, status FROM question_jobs ORDER BY created_at DESC LIMIT 1"
    )
    job_id = job["id"]
    job_status = job["status"]

    rows = await conn.fetch(
        """
        SELECT q.id, q.source_question_number, q.current_question_text,
               q.current_correct_option_label, q.current_explanation_text,
               q.source_exam_code, q.source_module_code, q.source_section_code,
               q.current_passage_text, q.current_paired_passage_text,
               q.stimulus_mode_key, q.stem_type_key
        FROM questions q
        JOIN question_job_questions qjq ON qjq.question_id = q.id
        WHERE qjq.job_id = $1
        ORDER BY q.source_question_number
        """,
        job_id,
    )

    md_lines = ["# Test 5 Section 1 Module 1 - Ingested Data Review\n"]
    md_lines.append(f"Job ID: ``{job_id}``  ")
    md_lines.append(f"Status: ``{job_status}``  ")
    md_lines.append(f"Questions: {len(rows)}\n")
    md_lines.append("---\n")

    for row in rows:
        qnum = row["source_question_number"]
        qtext = row["current_question_text"] or ""
        answer = row["current_correct_option_label"] or ""
        explanation = row["current_explanation_text"] or ""
        exam = row["source_exam_code"] or ""
        module = row["source_module_code"] or ""
        section = row["source_section_code"] or ""
        passage = row["current_passage_text"] or ""
        paired_passage = row["current_paired_passage_text"] or ""
        stim_mode = row["stimulus_mode_key"] or ""
        stem_type = row["stem_type_key"] or ""
        qid = row["id"]

        md_lines.append(f"## Q{qnum}\n")
        md_lines.append(f"**Source:** {exam} | **Module:** {module} | **Section:** {section}  ")
        md_lines.append(f"**Stimulus:** {stim_mode} | **Stem:** {stem_type}\n")

        # Passage
        if passage:
            md_lines.append("### Passage\n")
            md_lines.append(f"{passage}\n")
        if paired_passage:
            md_lines.append("### Paired Passage\n")
            md_lines.append(f"{paired_passage}\n")

        # Stimulus assets (tables, charts, etc.)
        sassets = await conn.fetch(
            "SELECT stimulus_type, title, structured_data_jsonb, render_hints_jsonb FROM question_stimulus_assets WHERE question_id = $1",
            qid,
        )
        for sa in sassets:
            stype = sa["stimulus_type"] or ""
            stitle = sa["title"] or ""
            sdata = sa["structured_data_jsonb"]
            md_lines.append(f"### {stype.capitalize()}: {stitle}\n")
            if sdata:
                try:
                    data = json.loads(sdata) if isinstance(sdata, str) else sdata
                    headers = data.get("headers", [])
                    rows_data = data.get("rows", [])
                    if headers and rows_data:
                        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
                        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
                        md_lines.append(header_line)
                        md_lines.append(sep_line)
                        for r in rows_data:
                            row_line = "| " + " | ".join(str(c) for c in r) + " |"
                            md_lines.append(row_line)
                        md_lines.append("")
                    else:
                        md_lines.append(
                            "```json\n" + json.dumps(data, indent=2) + "\n```\n"
                        )
                except Exception:
                    md_lines.append(f"```json\n{sdata}\n```\n")

        # Question
        md_lines.append("### Question\n")
        md_lines.append(f"{qtext}\n")

        # Options
        opts = await conn.fetch(
            "SELECT option_label, option_text, is_correct FROM question_options WHERE question_id = $1 ORDER BY option_label",
            qid,
        )
        for opt in opts:
            marker = " **(correct)**" if opt["is_correct"] else ""
            otext = opt["option_text"] or ""
            md_lines.append(f"- **{opt['option_label']}.** {otext}{marker}")

        md_lines.append(f"\n**Correct Answer:** {answer}\n")
        if explanation:
            md_lines.append(f"**Explanation:** {explanation}\n")
        md_lines.append("---\n")

    outpath = "/home/jb/DSAT_REDUX_MD/analysis/test5_sec01_mod01_review.md"
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        f.write("\n".join(md_lines))
    print(f"Written to {outpath} ({len(rows)} questions)")

    await conn.close()


asyncio.run(main())