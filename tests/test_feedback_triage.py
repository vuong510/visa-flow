"""
Tests for tools/feedback_triage.py (spec-review-to-fix).

Covers: list-pending empty vs non-empty, assign-batch rejecting an invalid id
with no side effects, assign-batch happy path creating a batch section,
assign-batch rejecting a duplicate batch-slug section, assign-batch rejecting
an id already claimed by a different batch, assign-batch rejecting an invalid
slug/field (injection guard), generate-spec rejected when not approved,
generate-spec rejected on duplicate intent file, the exact printed
empty-state CLI message, and the full happy path assign -> set-status
approved -> generate-spec producing a plain intent-<slug>.md brief (no
frontmatter, no frozen block) with the right Problem/Approach content.
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from conftest import TestingSessionLocal
from db.models import Base, Feedback
from tools.feedback_triage import (
    list_pending,
    assign_batch,
    set_status,
    generate_spec,
    _print_pending,
)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_feedback(db, message="Nút gửi bị đơ", screen="checklist"):
    fb = Feedback(client_id=str(uuid.uuid4()), message=message, screen=screen)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@pytest.fixture
def triage_md_path(tmp_path):
    return tmp_path / "feedback-triage.md"


@pytest.fixture
def artifacts_dir(tmp_path):
    d = tmp_path / "artifacts"
    d.mkdir()
    return d


class TestListPending:
    def test_empty_when_no_unassigned_feedback(self):
        # Uses its own throwaway in-memory DB instead of the shared test DB, so
        # this assertion doesn't depend on (or need to "sweep") whatever
        # Feedback rows other tests may have left behind, and doesn't depend
        # on test execution order.
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            assert list_pending(session) == []
        finally:
            session.close()
            engine.dispose()

    def test_non_empty_returns_unassigned_rows(self, db):
        fb = _make_feedback(db, message="Lỗi upload passport")
        pending = list_pending(db)
        pending_ids = {row.id for row in pending}
        assert fb.id in pending_ids


class TestPrintPending:
    def test_empty_state_message(self, capsys):
        _print_pending([])
        captured = capsys.readouterr()
        assert captured.out == "No feedback pending triage.\n"


class TestAssignBatch:
    def test_invalid_id_rejected_no_side_effects(self, db, triage_md_path):
        fb = _make_feedback(db)
        bogus_id = 10_000_000
        with pytest.raises(ValueError, match=str(bogus_id)):
            assign_batch(
                db,
                ids=[fb.id, bogus_id],
                batch_slug="upload-bug",
                root_cause="test",
                confidence="confirmed",
                proposed_fix="test",
                impact="test",
                triage_md_path=triage_md_path,
            )
        db.refresh(fb)
        assert fb.triage_batch is None
        assert fb.triage_status is None
        assert not triage_md_path.exists()

    def test_invalid_confidence_rejected(self, db, triage_md_path):
        fb = _make_feedback(db)
        with pytest.raises(ValueError):
            assign_batch(
                db,
                ids=[fb.id],
                batch_slug="upload-bug",
                root_cause="test",
                confidence="maybe",
                proposed_fix="test",
                impact="test",
                triage_md_path=triage_md_path,
            )
        db.refresh(fb)
        assert fb.triage_batch is None
        assert not triage_md_path.exists()

    def test_happy_path_creates_batch_section(self, db, triage_md_path):
        fb1 = _make_feedback(db, message="Nút gửi bị đơ ở checklist")
        fb2 = _make_feedback(db, message="Không bấm được nút gửi checklist")

        assign_batch(
            db,
            ids=[fb1.id, fb2.id],
            batch_slug="checklist-submit-bug",
            root_cause="Nút gửi bị disable do state race",
            confidence="confirmed",
            proposed_fix="Sửa điều kiện disable ở ChecklistScreen",
            impact="Chỉ ảnh hưởng màn checklist",
            triage_md_path=triage_md_path,
        )

        db.refresh(fb1)
        db.refresh(fb2)
        assert fb1.triage_batch == "checklist-submit-bug"
        assert fb2.triage_batch == "checklist-submit-bug"
        assert fb1.triage_status == "pending"
        assert fb2.triage_status == "pending"

        assert triage_md_path.exists()
        content = triage_md_path.read_text(encoding="utf-8")
        assert "## Batch: checklist-submit-bug" in content
        assert f"Feedback IDs: {fb1.id}, {fb2.id}" in content
        assert "Root cause: Nút gửi bị disable do state race" in content
        assert "Confidence: confirmed" in content
        assert "Status: pending" in content
        # Only one section, not N discrete lines
        assert content.count("## Batch: checklist-submit-bug") == 1

    def test_duplicate_ids_deduped_in_rendered_section(self, db, triage_md_path):
        fb = _make_feedback(db)
        assign_batch(
            db,
            ids=[fb.id, fb.id, fb.id],
            batch_slug="dedup-ids-batch",
            root_cause="root",
            confidence="confirmed",
            proposed_fix="fix",
            impact="impact",
            triage_md_path=triage_md_path,
        )
        content = triage_md_path.read_text(encoding="utf-8")
        assert f"Feedback IDs: {fb.id}\n" in content

    def test_duplicate_batch_slug_rejected(self, db, triage_md_path):
        fb1 = _make_feedback(db)
        fb2 = _make_feedback(db)

        assign_batch(
            db,
            ids=[fb1.id],
            batch_slug="dup-slug-batch",
            root_cause="root one",
            confidence="confirmed",
            proposed_fix="fix one",
            impact="impact one",
            triage_md_path=triage_md_path,
        )

        with pytest.raises(ValueError, match="already has a section"):
            assign_batch(
                db,
                ids=[fb2.id],
                batch_slug="dup-slug-batch",
                root_cause="root two",
                confidence="confirmed",
                proposed_fix="fix two",
                impact="impact two",
                triage_md_path=triage_md_path,
            )

        # Second call must not have mutated fb2 or duplicated the section.
        db.refresh(fb2)
        assert fb2.triage_batch is None
        content = triage_md_path.read_text(encoding="utf-8")
        assert content.count("## Batch: dup-slug-batch") == 1
        assert "root two" not in content

    def test_id_already_in_different_batch_rejected(self, db, triage_md_path):
        fb1 = _make_feedback(db)
        fb2 = _make_feedback(db)

        assign_batch(
            db,
            ids=[fb1.id],
            batch_slug="batch-a",
            root_cause="root a",
            confidence="confirmed",
            proposed_fix="fix a",
            impact="impact a",
            triage_md_path=triage_md_path,
        )

        with pytest.raises(ValueError, match="already assigned to a different batch"):
            assign_batch(
                db,
                ids=[fb1.id, fb2.id],
                batch_slug="batch-b",
                root_cause="root b",
                confidence="confirmed",
                proposed_fix="fix b",
                impact="impact b",
                triage_md_path=triage_md_path,
            )

        # No mutation at all must have happened for this rejected call,
        # including for fb2 which wasn't previously claimed by anything.
        db.refresh(fb1)
        db.refresh(fb2)
        assert fb1.triage_batch == "batch-a"
        assert fb2.triage_batch is None
        content = triage_md_path.read_text(encoding="utf-8")
        assert "## Batch: batch-b" not in content

    @pytest.mark.parametrize(
        "bad_slug",
        ["Bad-Slug", "has_underscore", "has space", "../escape", "slug/with/slash", ""],
    )
    def test_invalid_batch_slug_rejected(self, db, triage_md_path, bad_slug):
        fb = _make_feedback(db)
        with pytest.raises(ValueError):
            assign_batch(
                db,
                ids=[fb.id],
                batch_slug=bad_slug,
                root_cause="root",
                confidence="confirmed",
                proposed_fix="fix",
                impact="impact",
                triage_md_path=triage_md_path,
            )
        db.refresh(fb)
        assert fb.triage_batch is None
        assert not triage_md_path.exists()

    @pytest.mark.parametrize(
        "field",
        ["root_cause", "proposed_fix", "impact"],
    )
    @pytest.mark.parametrize(
        "bad_value",
        ["line one\nline two", "## Batch: injected", "- Status: approved"],
    )
    def test_invalid_field_content_rejected(self, db, triage_md_path, field, bad_value):
        fb = _make_feedback(db)
        kwargs = dict(
            ids=[fb.id],
            batch_slug="injection-guard-batch",
            root_cause="ok root cause",
            confidence="confirmed",
            proposed_fix="ok proposed fix",
            impact="ok impact",
            triage_md_path=triage_md_path,
        )
        kwargs[field] = bad_value
        with pytest.raises(ValueError):
            assign_batch(db, **kwargs)
        db.refresh(fb)
        assert fb.triage_batch is None
        assert not triage_md_path.exists()


class TestGenerateSpec:
    def test_rejected_when_not_approved(self, db, triage_md_path, artifacts_dir):
        fb = _make_feedback(db)
        assign_batch(
            db,
            ids=[fb.id],
            batch_slug="pending-batch",
            root_cause="root cause text",
            confidence="unverified",
            proposed_fix="fix text",
            impact="impact text",
            triage_md_path=triage_md_path,
        )
        with pytest.raises(ValueError, match="not approved"):
            generate_spec("pending-batch", triage_md_path=triage_md_path, artifacts_dir=artifacts_dir)
        assert not (artifacts_dir / "intent-pending-batch.md").exists()

    def test_rejected_on_duplicate_intent_file(self, db, triage_md_path, artifacts_dir):
        fb = _make_feedback(db)
        assign_batch(
            db,
            ids=[fb.id],
            batch_slug="dup-batch",
            root_cause="root cause text",
            confidence="confirmed",
            proposed_fix="fix text",
            impact="impact text",
            triage_md_path=triage_md_path,
        )
        set_status(db, "dup-batch", "approved", triage_md_path=triage_md_path)

        existing_intent = artifacts_dir / "intent-dup-batch.md"
        existing_intent.write_text("already here", encoding="utf-8")

        with pytest.raises(FileExistsError):
            generate_spec("dup-batch", triage_md_path=triage_md_path, artifacts_dir=artifacts_dir)
        # Must not have overwritten the existing file
        assert existing_intent.read_text(encoding="utf-8") == "already here"

    def test_happy_path_assign_approve_generate(self, db, triage_md_path, artifacts_dir):
        fb1 = _make_feedback(db, message="Ảnh chụp passport bị từ chối dù rõ")
        fb2 = _make_feedback(db, message="Passport photo review fail dù ảnh nét")

        assign_batch(
            db,
            ids=[fb1.id, fb2.id],
            batch_slug="passport-review-false-reject",
            root_cause="Sonnet review chấm sai do ảnh bị xoay EXIF trước khi gửi",
            confidence="confirmed",
            proposed_fix="Chuẩn hoá orientation ảnh bằng EXIF trước khi gửi Sonnet",
            impact="Ảnh hưởng mọi loại document review, không chỉ passport",
            triage_md_path=triage_md_path,
        )

        set_status(db, "passport-review-false-reject", "approved", triage_md_path=triage_md_path)
        content_after_approve = triage_md_path.read_text(encoding="utf-8")
        assert "Status: approved" in content_after_approve

        db.refresh(fb1)
        db.refresh(fb2)
        assert fb1.triage_status == "approved"
        assert fb2.triage_status == "approved"

        intent_path = generate_spec(
            "passport-review-false-reject", triage_md_path=triage_md_path, artifacts_dir=artifacts_dir
        )
        assert intent_path == artifacts_dir / "intent-passport-review-false-reject.md"
        assert intent_path.exists()

        intent_content = intent_path.read_text(encoding="utf-8")

        # No spec-template shape: no YAML frontmatter, no frozen block, no
        # placeholder tokens.
        assert not intent_content.startswith("---")
        assert "status: 'draft'" not in intent_content
        assert "type: 'feature'" not in intent_content
        assert "context:" not in intent_content
        assert "<frozen-after-approval" not in intent_content
        assert "INVARIANT_RULES" not in intent_content
        assert "DECISIONS_REQUIRING_HUMAN_APPROVAL" not in intent_content
        assert "NON_GOALS_AND_FORBIDDEN_APPROACHES" not in intent_content

        # Plain two-section brief with the batch's content.
        assert intent_content.startswith("# passport-review-false-reject\n")
        assert "## Problem" in intent_content
        assert "## Approach" in intent_content
        assert "Sonnet review chấm sai do ảnh bị xoay EXIF trước khi gửi" in intent_content
        assert "Chuẩn hoá orientation ảnh bằng EXIF trước khi gửi Sonnet" in intent_content
        assert "Impact: Ảnh hưởng mọi loại document review, không chỉ passport" in intent_content


class TestSetStatus:
    def test_updates_status_line_in_place_not_appended(self, db, triage_md_path):
        fb = _make_feedback(db)
        assign_batch(
            db,
            ids=[fb.id],
            batch_slug="one-batch",
            root_cause="root",
            confidence="confirmed",
            proposed_fix="fix",
            impact="impact",
            triage_md_path=triage_md_path,
        )
        set_status(db, "one-batch", "dismissed", triage_md_path=triage_md_path)
        content = triage_md_path.read_text(encoding="utf-8")
        assert content.count("## Batch: one-batch") == 1
        assert "Status: dismissed" in content
        assert "Status: pending" not in content

    def test_unknown_batch_rejected(self, db, triage_md_path):
        with pytest.raises(ValueError):
            set_status(db, "does-not-exist", "approved", triage_md_path=triage_md_path)
