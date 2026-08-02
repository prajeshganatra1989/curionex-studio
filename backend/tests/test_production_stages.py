"""Unit tests for Production Mode stage classification and next-action engine."""

from __future__ import annotations

from uuid import uuid4

from app.production.stages import (
    PRODUCTION_STAGES,
    STAGE_PRIORITY,
    AiJobSnapshot,
    ApprovalSnapshot,
    ClassificationInput,
    DocumentPresence,
    QualitySnapshot,
    VersionFingerprintSnapshot,
    WorkflowSnapshot,
    classify_production_stage,
    empty_stage_counts,
    resolve_next_action,
    serialize_next_action,
)


def _base(**overrides) -> ClassificationInput:
    data = ClassificationInput(
        script_id=uuid4(),
        project_id=uuid4(),
        project_status="active",
        script_status="draft",
        has_knowledge_pack=True,
        knowledge_pack_complete=True,
    )
    for key, value in overrides.items():
        setattr(data, key, value)
    return data


def test_stage_priority_covers_all_stages() -> None:
    assert set(STAGE_PRIORITY) == set(PRODUCTION_STAGES)
    # Lower number = higher queue priority.
    assert STAGE_PRIORITY["blocked"] < STAGE_PRIORITY["pending_human_review"]
    assert STAGE_PRIORITY["pending_human_review"] < STAGE_PRIORITY["needs_revision"]
    assert STAGE_PRIORITY["idea"] < STAGE_PRIORITY["approved"]
    assert STAGE_PRIORITY["approved"] < STAGE_PRIORITY["archived"]


def test_empty_stage_counts() -> None:
    counts = empty_stage_counts()
    assert set(counts) == set(PRODUCTION_STAGES)
    assert all(value == 0 for value in counts.values())


# --- Classification: idea → archived ---


def test_classify_idea_project_without_script_or_pack() -> None:
    stage = classify_production_stage(
        ClassificationInput(
            script_id=None,
            project_id=uuid4(),
            project_status="active",
            has_knowledge_pack=False,
        )
    )
    assert stage == "idea"


def test_classify_research_project_with_pack() -> None:
    incomplete = classify_production_stage(
        ClassificationInput(
            script_id=None,
            project_id=uuid4(),
            has_knowledge_pack=True,
            knowledge_pack_complete=False,
        )
    )
    complete = classify_production_stage(
        ClassificationInput(
            script_id=None,
            project_id=uuid4(),
            has_knowledge_pack=True,
            knowledge_pack_complete=True,
        )
    )
    assert incomplete == "research"
    assert complete == "research"


def test_classify_discovery_brief() -> None:
    assert (
        classify_production_stage(
            _base(
                documents=DocumentPresence(),
                has_knowledge_pack=True,
            )
        )
        == "discovery_brief"
    )
    assert (
        classify_production_stage(
            _base(
                documents=DocumentPresence(),
                has_knowledge_pack=False,
            )
        )
        == "discovery_brief"
    )


def test_classify_story_spine() -> None:
    assert (
        classify_production_stage(
            _base(documents=DocumentPresence(discovery_brief=True))
        )
        == "story_spine"
    )


def test_classify_master_script() -> None:
    assert (
        classify_production_stage(
            _base(
                documents=DocumentPresence(
                    discovery_brief=True,
                    story_spine=True,
                )
            )
        )
        == "master_script"
    )


def test_classify_quality_review_when_master_present_no_generation() -> None:
    assert (
        classify_production_stage(
            _base(
                documents=DocumentPresence(
                    discovery_brief=True,
                    story_spine=True,
                    master_script=True,
                ),
                quality=QualitySnapshot(),
            )
        )
        == "quality_review"
    )


def test_classify_needs_revision_paths() -> None:
    docs = DocumentPresence(
        discovery_brief=True,
        story_spine=True,
        master_script=True,
    )
    gen_id = uuid4()

    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(generation_id=gen_id, stale=True, score=90),
            )
        )
        == "needs_revision"
    )
    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(
                    generation_id=gen_id,
                    recommendation="revise",
                    score=85,
                ),
            )
        )
        == "needs_revision"
    )
    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(
                    generation_id=gen_id,
                    score=70,
                    recommendation="human_review",
                ),
            )
        )
        == "needs_revision"
    )
    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(
                    generation_id=gen_id,
                    score=88,
                    high_risk_facts=1,
                    recommendation="human_review",
                ),
            )
        )
        == "needs_revision"
    )
    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(
                    generation_id=gen_id,
                    score=88,
                    has_critical_issue=True,
                    recommendation="human_review",
                ),
            )
        )
        == "needs_revision"
    )


def test_classify_ready_for_version() -> None:
    docs = DocumentPresence(
        discovery_brief=True,
        story_spine=True,
        master_script=True,
    )
    gen_id = uuid4()
    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(
                    generation_id=gen_id,
                    score=92,
                    recommendation="ready_for_version",
                ),
                version=VersionFingerprintSnapshot(version_id=None),
            )
        )
        == "ready_for_version"
    )
    assert (
        classify_production_stage(
            _base(
                documents=docs,
                quality=QualitySnapshot(
                    generation_id=gen_id,
                    score=92,
                    recommendation="ready_for_version",
                ),
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="approved",
                    workspace_matches_version=False,
                ),
            )
        )
        == "ready_for_version"
    )


def test_classify_version_created() -> None:
    assert (
        classify_production_stage(
            _base(
                documents=DocumentPresence(master_script=True),
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="draft",
                ),
                quality=QualitySnapshot(generation_id=uuid4(), score=95),
            )
        )
        == "version_created"
    )


def test_classify_pending_human_review() -> None:
    assert (
        classify_production_stage(
            _base(
                approval=ApprovalSnapshot(status="pending", approval_id=uuid4()),
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="in_review",
                ),
            )
        )
        == "pending_human_review"
    )
    # in_review without pending approval still routes to pending_human_review.
    assert (
        classify_production_stage(
            _base(
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="in_review",
                ),
            )
        )
        == "pending_human_review"
    )


def test_classify_approved() -> None:
    assert (
        classify_production_stage(
            _base(
                workflow=WorkflowSnapshot(stage="completed", status="completed"),
            )
        )
        == "approved"
    )
    assert (
        classify_production_stage(
            _base(
                script_status="approved",
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="approved",
                ),
            )
        )
        == "approved"
    )


def test_classify_blocked() -> None:
    assert classify_production_stage(_base(provider_config_blocker=True)) == "blocked"
    assert (
        classify_production_stage(
            _base(ai_job=AiJobSnapshot(status="failed", job_id=uuid4()))
        )
        == "blocked"
    )
    assert (
        classify_production_stage(
            _base(workflow=WorkflowSnapshot(status="blocked", stage="workspace"))
        )
        == "blocked"
    )


def test_classify_archived() -> None:
    assert (
        classify_production_stage(_base(script_status="archived")) == "archived"
    )
    assert (
        classify_production_stage(_base(project_status="archived")) == "archived"
    )


def test_classify_rejected_version_is_needs_revision() -> None:
    assert (
        classify_production_stage(
            _base(
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="rejected",
                ),
            )
        )
        == "needs_revision"
    )


# --- Precedence: first match wins ---


def test_precedence_archived_beats_approved() -> None:
    assert (
        classify_production_stage(
            _base(
                script_status="archived",
                workflow=WorkflowSnapshot(stage="completed", status="completed"),
            )
        )
        == "archived"
    )


def test_precedence_approved_beats_blocked() -> None:
    assert (
        classify_production_stage(
            _base(
                workflow=WorkflowSnapshot(stage="completed", status="completed"),
                provider_config_blocker=True,
            )
        )
        == "approved"
    )


def test_precedence_blocked_beats_pending_review() -> None:
    assert (
        classify_production_stage(
            _base(
                provider_config_blocker=True,
                approval=ApprovalSnapshot(status="pending", approval_id=uuid4()),
            )
        )
        == "blocked"
    )


def test_precedence_pending_beats_version_created() -> None:
    assert (
        classify_production_stage(
            _base(
                approval=ApprovalSnapshot(status="pending", approval_id=uuid4()),
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="draft",
                ),
            )
        )
        == "pending_human_review"
    )


def test_precedence_version_created_beats_quality_gates() -> None:
    assert (
        classify_production_stage(
            _base(
                documents=DocumentPresence(master_script=True),
                version=VersionFingerprintSnapshot(
                    version_id=uuid4(),
                    version_status="draft",
                ),
                quality=QualitySnapshot(),  # would be quality_review without version
            )
        )
        == "version_created"
    )


# --- Next action ---


def test_resolve_next_action_key_stages() -> None:
    project_id = uuid4()
    script_id = uuid4()
    pack_id = uuid4()
    gen_id = uuid4()
    approval_id = uuid4()
    version_id = uuid4()
    job_id = uuid4()

    cases = [
        (
            "idea",
            resolve_next_action("idea", project_id=project_id, script_id=None),
            "create_knowledge_pack",
        ),
        (
            "research",
            resolve_next_action(
                "research",
                project_id=project_id,
                script_id=None,
                knowledge_pack_id=pack_id,
            ),
            "open_knowledge_pack",
        ),
        (
            "discovery_brief",
            resolve_next_action(
                "discovery_brief",
                project_id=project_id,
                script_id=script_id,
            ),
            "generate_discovery_brief",
        ),
        (
            "story_spine",
            resolve_next_action(
                "story_spine",
                project_id=project_id,
                script_id=script_id,
            ),
            "generate_story_spine",
        ),
        (
            "master_script",
            resolve_next_action(
                "master_script",
                project_id=project_id,
                script_id=script_id,
            ),
            "generate_master_script",
        ),
        (
            "quality_review",
            resolve_next_action(
                "quality_review",
                project_id=project_id,
                script_id=script_id,
            ),
            "run_quality_review",
        ),
        (
            "needs_revision",
            resolve_next_action(
                "needs_revision",
                project_id=project_id,
                script_id=script_id,
                quality_generation_id=gen_id,
            ),
            "fix_quality_issues",
        ),
        (
            "ready_for_version",
            resolve_next_action(
                "ready_for_version",
                project_id=project_id,
                script_id=script_id,
            ),
            "create_version",
        ),
        (
            "version_created",
            resolve_next_action(
                "version_created",
                project_id=project_id,
                script_id=script_id,
            ),
            "submit_human_review",
        ),
        (
            "pending_human_review",
            resolve_next_action(
                "pending_human_review",
                project_id=project_id,
                script_id=script_id,
                approval_id=approval_id,
            ),
            "review_approval",
        ),
        (
            "approved",
            resolve_next_action(
                "approved",
                project_id=project_id,
                script_id=script_id,
                version_id=version_id,
            ),
            "view_approved_version",
        ),
        (
            "blocked_retry",
            resolve_next_action(
                "blocked",
                project_id=project_id,
                script_id=script_id,
                failed_job_id=job_id,
            ),
            "retry_ai_job",
        ),
        (
            "blocked_provider",
            resolve_next_action(
                "blocked",
                project_id=project_id,
                script_id=script_id,
                provider_config_blocker=True,
            ),
            "configure_ai_provider",
        ),
        (
            "archived",
            resolve_next_action(
                "archived",
                project_id=project_id,
                script_id=script_id,
            ),
            "view_approved_version",
        ),
    ]

    for _label, action, expected_code in cases:
        assert action.code == expected_code
        assert action.label
        assert action.reason
        serialized = serialize_next_action(action)
        assert serialized["code"] == expected_code
        assert "blocked" in serialized


def test_resolve_next_action_discovery_without_script() -> None:
    project_id = uuid4()
    action = resolve_next_action(
        "discovery_brief",
        project_id=project_id,
        script_id=None,
    )
    assert action.code == "create_script"
    assert f"/projects/{project_id}/scripts" in (action.href or "")


def test_resolve_next_action_research_without_pack() -> None:
    project_id = uuid4()
    action = resolve_next_action(
        "research",
        project_id=project_id,
        script_id=None,
        knowledge_pack_id=None,
    )
    assert action.code == "create_knowledge_pack"
