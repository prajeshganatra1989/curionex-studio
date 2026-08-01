"""RBAC authorization tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.schemas.auth import UserCreate
from app.services import rbac_service
from app.services.rbac_service import (
    DuplicateAssignmentError,
    DuplicateRoleError,
    assign_permission_to_role,
    assign_role_to_user,
    create_permission,
    create_role,
    has_permission,
    remove_role_from_user,
    seed_rbac_catalog,
)
from app.services.user_service import create_user


def _user(db: Session, email: str = "rbac@example.com"):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Rbac",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_role_and_permission_creation(db_session: Session) -> None:
    role = create_role(db_session, name="Custom Role", description="test")
    permission = create_permission(
        db_session,
        code="custom.action",
        name="Custom action",
    )
    assert role.id is not None
    assert permission.code == "custom.action"


def test_duplicate_role_rejected(db_session: Session) -> None:
    create_role(db_session, name="Unique Role")
    with pytest.raises(DuplicateRoleError):
        create_role(db_session, name="Unique Role")


def test_user_role_and_role_permission_assignment(db_session: Session) -> None:
    user = _user(db_session, "assign@example.com")
    role = create_role(db_session, name="Temp Role")
    permission = create_permission(
        db_session,
        code="temp.view",
        name="Temp view",
    )
    assign_permission_to_role(
        db_session,
        role_id=role.id,
        permission_id=permission.id,
    )
    assign_role_to_user(db_session, user_id=user.id, role_id=role.id)
    assert has_permission(db_session, user, "temp.view") is True


def test_duplicate_assignments_rejected(db_session: Session) -> None:
    user = _user(db_session, "dup-assign@example.com")
    role = create_role(db_session, name="Dup Role")
    permission = create_permission(
        db_session,
        code="dup.perm",
        name="Dup perm",
    )
    assign_permission_to_role(
        db_session,
        role_id=role.id,
        permission_id=permission.id,
    )
    with pytest.raises(DuplicateAssignmentError):
        assign_permission_to_role(
            db_session,
            role_id=role.id,
            permission_id=permission.id,
        )
    assign_role_to_user(db_session, user_id=user.id, role_id=role.id)
    with pytest.raises(DuplicateAssignmentError):
        assign_role_to_user(db_session, user_id=user.id, role_id=role.id)


def test_user_with_permission_authorized(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "owner-api@example.com")
    rbac_service.assign_owner_role(db_session, user)

    response = client.get("/roles", headers=_auth_header(user))
    assert response.status_code == 200
    assert any(item["name"] == "Owner" for item in response.json())


def test_user_without_permission_receives_403(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "writer@example.com")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    assert writer is not None
    assign_role_to_user(db_session, user_id=user.id, role_id=writer.id)

    response = client.get("/roles", headers=_auth_header(user))
    assert response.status_code == 403


def test_unauthenticated_request_receives_401(client: TestClient) -> None:
    response = client.get("/roles")
    assert response.status_code == 401


def test_inactive_user_denied(db_session: Session) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "inactive-rbac@example.com")
    rbac_service.assign_owner_role(db_session, user)
    user.is_active = False
    db_session.commit()
    assert has_permission(db_session, user, "roles.view") is False


def test_inactive_role_denied(db_session: Session) -> None:
    user = _user(db_session, "inactive-role@example.com")
    role = create_role(db_session, name="Inactive Role")
    permission = create_permission(
        db_session,
        code="inactive.role.perm",
        name="Inactive role perm",
    )
    assign_permission_to_role(
        db_session,
        role_id=role.id,
        permission_id=permission.id,
    )
    assign_role_to_user(db_session, user_id=user.id, role_id=role.id)
    role.is_active = False
    db_session.commit()
    assert has_permission(db_session, user, "inactive.role.perm") is False


def test_inactive_permission_denied(db_session: Session) -> None:
    user = _user(db_session, "inactive-perm@example.com")
    role = create_role(db_session, name="Perm Role")
    permission = create_permission(
        db_session,
        code="inactive.perm.code",
        name="Inactive perm",
    )
    assign_permission_to_role(
        db_session,
        role_id=role.id,
        permission_id=permission.id,
    )
    assign_role_to_user(db_session, user_id=user.id, role_id=role.id)
    permission.is_active = False
    db_session.commit()
    assert has_permission(db_session, user, "inactive.perm.code") is False


def test_multiple_roles_combine_permissions(db_session: Session) -> None:
    user = _user(db_session, "multi@example.com")
    role_a = create_role(db_session, name="Role A")
    role_b = create_role(db_session, name="Role B")
    perm_a = create_permission(db_session, code="combo.a", name="A")
    perm_b = create_permission(db_session, code="combo.b", name="B")
    assign_permission_to_role(db_session, role_id=role_a.id, permission_id=perm_a.id)
    assign_permission_to_role(db_session, role_id=role_b.id, permission_id=perm_b.id)
    assign_role_to_user(db_session, user_id=user.id, role_id=role_a.id)
    assign_role_to_user(db_session, user_id=user.id, role_id=role_b.id)
    assert has_permission(db_session, user, "combo.a")
    assert has_permission(db_session, user, "combo.b")


def test_owner_gets_expected_permissions(db_session: Session) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "owner-perms@example.com")
    rbac_service.assign_owner_role(db_session, user)
    for code in (
        "users.view",
        "roles.assign",
        "projects.create",
        "approvals.approve",
        "audit.view",
        "settings.update",
    ):
        assert has_permission(db_session, user, code)


def test_script_writer_cannot_manage_users(db_session: Session) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "sw@example.com")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    assert writer is not None
    assign_role_to_user(db_session, user_id=user.id, role_id=writer.id)
    assert has_permission(db_session, user, "users.create") is False
    assert has_permission(db_session, user, "scripts.update") is True


def test_reviewer_can_approve_writer_cannot(db_session: Session) -> None:
    seed_rbac_catalog(db_session)
    reviewer_user = _user(db_session, "reviewer@example.com")
    writer_user = _user(db_session, "writer2@example.com")
    reviewer = rbac_service.get_role_by_name(db_session, "Reviewer")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    assert reviewer and writer
    assign_role_to_user(db_session, user_id=reviewer_user.id, role_id=reviewer.id)
    assign_role_to_user(db_session, user_id=writer_user.id, role_id=writer.id)
    assert has_permission(db_session, reviewer_user, "approvals.approve") is True
    assert has_permission(db_session, writer_user, "approvals.approve") is False


def test_user_cannot_self_assign_owner_without_roles_assign(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "no-assign@example.com")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    owner = rbac_service.get_role_by_name(db_session, "Owner")
    assert writer and owner
    assign_role_to_user(db_session, user_id=user.id, role_id=writer.id)

    response = client.post(
        f"/users/{user.id}/roles/{owner.id}",
        headers=_auth_header(user),
    )
    assert response.status_code == 403


def test_roles_assign_can_assign_role(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    admin_user = _user(db_session, "admin-assign@example.com")
    target = _user(db_session, "target@example.com")
    admin = rbac_service.get_role_by_name(db_session, "Admin")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    assert admin and writer
    assign_role_to_user(db_session, user_id=admin_user.id, role_id=admin.id)

    response = client.post(
        f"/users/{target.id}/roles/{writer.id}",
        headers=_auth_header(admin_user),
    )
    assert response.status_code == 201


def test_remove_role_from_user(db_session: Session) -> None:
    user = _user(db_session, "remove-role@example.com")
    role = create_role(db_session, name="Removable")
    assign_role_to_user(db_session, user_id=user.id, role_id=role.id)
    remove_role_from_user(db_session, user_id=user.id, role_id=role.id)
    # second removal fails
    with pytest.raises(rbac_service.NotFoundError):
        remove_role_from_user(db_session, user_id=user.id, role_id=role.id)


def test_create_role_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    user = _user(db_session, "create-role@example.com")
    rbac_service.assign_owner_role(db_session, user)
    response = client.post(
        "/roles",
        headers=_auth_header(user),
        json={"name": "Ops", "description": "Operations"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Ops"


def test_authentication_still_works(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(
        db_session,
        UserCreate(
            email="still-auth@example.com",
            password="securepass123",
            first_name="Still",
            last_name="Auth",
        ),
    )
    login = client.post(
        "/auth/login",
        json={"email": "still-auth@example.com", "password": "securepass123"},
    )
    assert login.status_code == 200
    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert "password_hash" not in me.json()
