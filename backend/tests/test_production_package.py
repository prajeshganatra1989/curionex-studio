"""Production package generator tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.production.storyboard import (
    build_storyboard_scenes,
    build_subtitle_segments,
    wrap_caption_lines,
)
from app.schemas.auth import UserCreate
from app.services.rbac_service import assign_owner_role, seed_rbac_catalog
from app.services.user_service import create_user


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-prod-pkg@example.com"):
    seed_rbac_catalog(db)
    user = create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Prod",
            last_name="Pack",
        ),
    )
    assign_owner_role(db, user)
    return user


def _project_and_script(client: TestClient, headers: dict) -> tuple[dict, dict]:
    project = client.post(
        "/projects", headers=headers, json={"name": "Prod Pack Project"}
    ).json()
    script = client.post(
        f"/projects/{project['id']}/scripts",
        headers=headers,
        json={"title": "Why Do Magnets Attract?"},
    ).json()
    return project, script


MASTER = """Hold a magnet near a paperclip—
and the clip drifts closer across empty air.

That pull is a magnetic field.
It isn't gravity.
And magnets don't attract everything—
only materials that can respond, like iron.

Inside a magnet, tiny magnetic regions called domains
line up in the same direction.
That shared alignment builds one organized field
with a north pole and a south pole.

Here's the surprise.
A magnet isn't magical.
It's billions of tiny magnetic regions working together.

Follow for more fascinating facts about how the universe works."""


def test_storyboard_scene_duration_bounds() -> None:
    scenes = build_storyboard_scenes(MASTER, wpm=150)
    assert 4 <= len(scenes) <= 20
    for scene in scenes:
        span = scene["end_seconds"] - scene["start_seconds"]
        assert span >= 2.5
        assert scene["purpose"] in {
            "hook",
            "question",
            "explanation",
            "twist",
            "perspective_shift",
            "cta",
        }
    assert scenes[0]["purpose"] == "hook"
    assert scenes[-1]["purpose"] == "cta"


def test_subtitle_line_limits() -> None:
    lines = wrap_caption_lines(
        "This is a moderately long sentence that should wrap carefully."
    )
    assert 1 <= len(lines) <= 2
    assert all(len(line) <= 42 for line in lines)
    scenes = build_storyboard_scenes(MASTER)
    subs = build_subtitle_segments(scenes)
    assert subs
    assert all(len(s["lines"]) <= 2 for s in subs)


def test_production_package_requires_gold(
    client: TestClient, db_session: Session
) -> None:
    user = _owner(db_session)
    headers = _auth_header(user)
    _project, script = _project_and_script(client, headers)
    client.patch(
        f"/scripts/{script['id']}/documents/master_script",
        headers=headers,
        json={"content": MASTER},
    )
    blocked = client.post(
        f"/scripts/{script['id']}/production-package", headers=headers
    )
    assert blocked.status_code == 422
    assert blocked.json()["detail"]["code"] == "not_gold_approved"

    eligibility = client.get(
        f"/scripts/{script['id']}/production-package/eligibility", headers=headers
    )
    assert eligibility.status_code == 200
    assert eligibility.json()["eligible"] is False


def test_production_package_when_script_approved(
    client: TestClient, db_session: Session
) -> None:
    from app.models.script import Script
    from app.scripts.constants import SCRIPT_STATUS_APPROVED

    user = _owner(db_session)
    headers = _auth_header(user)
    project, script = _project_and_script(client, headers)
    client.patch(
        f"/scripts/{script['id']}/documents/master_script",
        headers=headers,
        json={"content": MASTER},
    )
    client.patch(
        f"/scripts/{script['id']}/documents/discovery_brief",
        headers=headers,
        json={"content": "CORE QUESTION\nWhy do magnets attract?"},
    )
    client.patch(
        f"/scripts/{script['id']}/documents/story_spine",
        headers=headers,
        json={"content": "HOOK\nPaperclip drifts."},
    )
    row = db_session.get(Script, script["id"])
    assert row is not None
    row.status = SCRIPT_STATUS_APPROVED
    db_session.commit()

    eligibility = client.get(
        f"/scripts/{script['id']}/production-package/eligibility", headers=headers
    )
    assert eligibility.json()["eligible"] is True

    response = client.post(
        f"/scripts/{script['id']}/production-package", headers=headers
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["project"]["id"] == project["id"]
    assert payload["script"]["script_code"] == script["script_code"]
    assert payload["master_script"]
    assert payload["storyboard"]
    assert payload["shot_list"]
    assert payload["asset_checklist"]
    assert payload["voice_package"]["word_count"] > 0
    assert payload["subtitle_package"]
    assert payload["youtube_package"]["category"] == "Education"
    assert payload["qa_package"]
    assert payload["production_metadata"]["gold_gate"] == "script_status_approved"


def test_production_package_forbidden_without_permission(
    client: TestClient, db_session: Session
) -> None:
    seed_rbac_catalog(db_session)
    user = create_user(
        db_session,
        UserCreate(
            email="noperm-prod-pkg@example.com",
            password="securepass123",
            first_name="No",
            last_name="Perm",
        ),
    )
    # no role → no scripts.view
    headers = _auth_header(user)
    response = client.post(
        "/scripts/00000000-0000-0000-0000-000000000001/production-package",
        headers=headers,
    )
    assert response.status_code in {401, 403}
