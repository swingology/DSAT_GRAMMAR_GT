#!/usr/bin/env python3
"""Local development CLI for approval-gated rule amendments."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.pipeline import amendment_review  # noqa: E402


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _result_to_exit(result: amendment_review.AmendmentOperationResult) -> int:
    if result.ok and result.amendment is not None:
        _print_json(result.amendment.to_file_dict())
        return 0
    if result.ok:
        _print_json({"ok": True})
        return 0
    print(result.error, file=sys.stderr)
    if result.details:
        print(json.dumps(result.details, indent=2, ensure_ascii=False), file=sys.stderr)
    return 1


def cmd_list(args) -> int:
    _print_json(amendment_review.list_amendments(repo_root=args.repo_root))
    return 0


def cmd_show(args) -> int:
    return _result_to_exit(amendment_review.load_amendment_by_id(args.amendment_id, repo_root=args.repo_root))


def cmd_approve(args) -> int:
    return _result_to_exit(
        amendment_review.approve_amendment(
            args.amendment_id,
            reviewer=args.reviewer,
            notes=args.notes,
            repo_root=args.repo_root,
        )
    )


def cmd_reject(args) -> int:
    return _result_to_exit(
        amendment_review.reject_amendment(
            args.amendment_id,
            reviewer=args.reviewer,
            notes=args.notes,
            repo_root=args.repo_root,
        )
    )


def cmd_request_more_evidence(args) -> int:
    return _result_to_exit(
        amendment_review.request_more_evidence(
            args.amendment_id,
            reviewer=args.reviewer,
            notes=args.notes,
            repo_root=args.repo_root,
        )
    )


def cmd_promote(args) -> int:
    return _result_to_exit(
        amendment_review.promote_amendment(
            args.amendment_id,
            reviewer=args.reviewer,
            notes=args.notes,
            repo_root=args.repo_root,
        )
    )


def _add_decision_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("amendment_id")
    parser.add_argument("--reviewer", default="cli")
    parser.add_argument("--notes", default="")


def _resolve_repo_root(value: str) -> Path:
    """Resolve a --repo-root argument to an existing repository directory."""
    root = Path(value).expanduser().resolve()
    if not (root / "vocabulary").is_dir():
        raise argparse.ArgumentTypeError(
            f"--repo-root {root} does not look like the repository root "
            "(missing vocabulary/ directory)"
        )
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=_resolve_repo_root,
        default=REPO_ROOT,
        help="repository root (defaults to the directory containing this script)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="list reviewable amendments")
    list_parser.set_defaults(func=cmd_list)

    show_parser = sub.add_parser("show", help="show one amendment")
    show_parser.add_argument("amendment_id")
    show_parser.set_defaults(func=cmd_show)

    approve_parser = sub.add_parser("approve", help="approve one pending amendment")
    _add_decision_args(approve_parser)
    approve_parser.set_defaults(func=cmd_approve)

    reject_parser = sub.add_parser("reject", help="reject one amendment")
    _add_decision_args(reject_parser)
    reject_parser.set_defaults(func=cmd_reject)

    evidence_parser = sub.add_parser("request-more-evidence", help="request more evidence")
    _add_decision_args(evidence_parser)
    evidence_parser.set_defaults(func=cmd_request_more_evidence)

    promote_parser = sub.add_parser("promote", help="promote an approved amendment")
    _add_decision_args(promote_parser)
    promote_parser.set_defaults(func=cmd_promote)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
