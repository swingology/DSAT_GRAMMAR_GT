"""Run with python3; no database or third-party dependencies required."""
import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("fetch", Path(__file__).with_name("fetch_question.py"))
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)
qid = "063675a5-e319-5c9c-a8fd-b7846009bc5e"

def run(arg, result):
    out = io.StringIO()
    with patch.object(fetch.sys, "argv", ["fetch", arg]), patch.object(
        fetch.subprocess, "run", return_value=result
    ) as call, contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = fetch.main()
    return code, out.getvalue(), call

code, _, call = run("bad'; DROP TABLE questions", None)
assert code == 2 and not call.called
code, out, call = run(qid, SimpleNamespace(returncode=0, stdout='{"question": {}}'))
assert code == 0 and '"question"' in out
assert "default_transaction_read_only=on" in call.call_args.kwargs["env"]["PGOPTIONS"]
assert "question_versions" in call.call_args.args[0][-1]
for result in [SimpleNamespace(returncode=1), SimpleNamespace(returncode=0, stdout=""),
               SimpleNamespace(returncode=0, stdout="invalid")]:
    assert run(qid, result)[0] == 1
print("fetch checks passed")
