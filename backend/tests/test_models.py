from sqlalchemy import inspect


def test_all_ten_tables_exist():
    from app.models.db import Base
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "question_jobs", "questions", "question_versions",
        "question_annotations", "question_options", "question_assets",
        "question_relations", "llm_evaluations", "users", "user_progress",
    }
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"


def test_question_jobs_columns():
    from app.models.db import QuestionJob
    mapper = inspect(QuestionJob).mapper
    col_names = {c.key for c in mapper.columns}
    required = {"id", "job_type", "content_origin", "input_format", "status",
                "provider_name", "model_name", "prompt_version", "rules_version",
                "pass1_json", "pass2_json", "validation_errors_jsonb",
                "comparison_group_id", "created_at", "updated_at"}
    assert required.issubset(col_names), f"Missing cols: {required - col_names}"


def test_questions_columns():
    from app.models.db import Question
    mapper = inspect(Question).mapper
    col_names = {c.key for c in mapper.columns}
    required = {"id", "content_origin", "source_exam_code", "source_subject_code", "source_section_code", "source_module_code",
                "stimulus_mode_key", "stem_type_key",
                "current_question_text", "current_passage_text",
                "current_correct_option_label", "current_explanation_text",
                "practice_status", "official_overlap_status",
                "is_admin_edited", "metadata_managed_by_llm",
                "created_at", "updated_at"}
    assert required.issubset(col_names), f"Missing cols: {required - col_names}"


def test_question_options_columns():
    from app.models.db import QuestionOption
    mapper = inspect(QuestionOption).mapper
    col_names = {c.key for c in mapper.columns}
    required = {"id", "question_id", "option_label", "option_text",
                "is_correct", "option_role", "distractor_type_key",
                "precision_score", "created_at"}
    assert required.issubset(col_names), f"Missing cols: {required - col_names}"


def test_foreign_keys():
    from app.models.db import UserProgress
    mapper = inspect(UserProgress).mapper
    fk_cols = {c.key for c in mapper.columns if c.foreign_keys}
    assert "user_id" in fk_cols
    assert "question_id" in fk_cols
