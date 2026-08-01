"""RBAC domain services — permission-code authorization."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_PERMISSION_ASSIGNED,
    ACTION_ROLE_ASSIGNED,
    ACTION_ROLE_CREATED,
    ACTION_ROLE_REMOVED,
    ENTITY_PERMISSION,
    ENTITY_ROLE,
    ENTITY_USER,
)
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.rbac.catalog import (
    OWNER_ROLE_NAME,
    PERMISSION_CATALOG,
    ROLE_CATALOG,
)
from app.services.audit_service import record_audit_event


class DuplicateAssignmentError(Exception):
    """Raised when a duplicate user-role or role-permission link is created."""


class DuplicateRoleError(Exception):
    """Raised when creating a role with a name that already exists."""


class NotFoundError(Exception):
    """Raised when a referenced RBAC entity does not exist."""


def normalize_role_name(name: str) -> str:
    """Normalize role display names for storage and lookup."""
    return " ".join(name.strip().split())


def get_permission_codes_for_user(db: Session, user: User) -> set[str]:
    """Return active permission codes granted via the user's active roles."""
    if not user.is_active:
        return set()

    statement = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user.id,
            Role.is_active.is_(True),
            Permission.is_active.is_(True),
        )
    )
    return set(db.scalars(statement).all())


def has_permission(db: Session, user: User, permission_code: str) -> bool:
    """Return True if the active user has the permission via any active role."""
    if not user.is_active:
        return False
    return permission_code in get_permission_codes_for_user(db, user)


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name)).all())


def list_permissions(db: Session) -> list[Permission]:
    return list(db.scalars(select(Permission).order_by(Permission.code)).all())


def get_role_by_id(db: Session, role_id: UUID) -> Role | None:
    return db.get(Role, role_id)


def get_role_by_name(db: Session, name: str) -> Role | None:
    normalized = normalize_role_name(name)
    statement = select(Role).where(func.lower(Role.name) == normalized.lower())
    return db.scalar(statement)


def get_permission_by_id(db: Session, permission_id: UUID) -> Permission | None:
    return db.get(Permission, permission_id)


def get_permission_by_code(db: Session, code: str) -> Permission | None:
    return db.scalar(select(Permission).where(Permission.code == code))


def create_role(
    db: Session,
    *,
    name: str,
    description: str | None = None,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Role:
    role = Role(name=normalize_role_name(name), description=description, is_active=True)
    db.add(role)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_ROLE_CREATED,
            entity_type=ENTITY_ROLE,
            entity_id=role.id,
            metadata={"name": role.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateRoleError("A role with this name already exists.") from exc
    db.refresh(role)
    return role


def create_permission(
    db: Session,
    *,
    code: str,
    name: str,
    description: str | None = None,
) -> Permission:
    permission = Permission(
        code=code.strip(),
        name=name.strip(),
        description=description,
        is_active=True,
    )
    db.add(permission)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAssignmentError("Permission code already exists.") from exc
    db.refresh(permission)
    return permission


def assign_permission_to_role(
    db: Session,
    *,
    role_id: UUID,
    permission_id: UUID,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> RolePermission:
    role = get_role_by_id(db, role_id)
    permission = get_permission_by_id(db, permission_id)
    if role is None or permission is None:
        raise NotFoundError("Role or permission not found.")

    link = RolePermission(role_id=role_id, permission_id=permission_id)
    db.add(link)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_PERMISSION_ASSIGNED,
            entity_type=ENTITY_PERMISSION,
            entity_id=permission.id,
            metadata={"role_id": str(role.id), "permission_code": permission.code},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAssignmentError(
            "Permission is already assigned to this role."
        ) from exc
    db.refresh(link)
    return link


def assign_role_to_user(
    db: Session,
    *,
    user_id: UUID,
    role_id: UUID,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> UserRole:
    user = db.get(User, user_id)
    role = get_role_by_id(db, role_id)
    if user is None or role is None:
        raise NotFoundError("User or role not found.")

    link = UserRole(user_id=user_id, role_id=role_id)
    db.add(link)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_ROLE_ASSIGNED,
            entity_type=ENTITY_USER,
            entity_id=user.id,
            metadata={"role_id": str(role.id), "role": role.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAssignmentError("Role is already assigned to this user.") from exc
    db.refresh(link)
    return link


def remove_role_from_user(
    db: Session,
    *,
    user_id: UUID,
    role_id: UUID,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    link = db.get(UserRole, (user_id, role_id))
    if link is None:
        raise NotFoundError("User role assignment not found.")
    role = get_role_by_id(db, role_id)
    db.delete(link)
    record_audit_event(
        db,
        actor_user_id=actor_user_id,
        action=ACTION_ROLE_REMOVED,
        entity_type=ENTITY_USER,
        entity_id=user_id,
        metadata={
            "role_id": str(role_id),
            "role": role.name if role is not None else None,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()


def seed_rbac_catalog(db: Session) -> dict[str, int]:
    """Idempotently seed permissions, roles, and role-permission grants."""
    created_permissions = 0
    created_roles = 0
    created_grants = 0

    permission_by_code: dict[str, Permission] = {
        p.code: p for p in db.scalars(select(Permission)).all()
    }
    for item in PERMISSION_CATALOG:
        existing = permission_by_code.get(item["code"])
        if existing is None:
            permission = Permission(
                code=item["code"],
                name=item["name"],
                description=item.get("description"),
                is_active=True,
            )
            db.add(permission)
            db.flush()
            permission_by_code[item["code"]] = permission
            created_permissions += 1

    role_by_name: dict[str, Role] = {
        r.name.lower(): r for r in db.scalars(select(Role)).all()
    }
    for role_name, config in ROLE_CATALOG.items():
        key = role_name.lower()
        role = role_by_name.get(key)
        if role is None:
            role = Role(
                name=role_name,
                description=config.get("description"),
                is_active=True,
            )
            db.add(role)
            db.flush()
            role_by_name[key] = role
            created_roles += 1

        existing_perm_ids = {
            rp.permission_id
            for rp in db.scalars(
                select(RolePermission).where(RolePermission.role_id == role.id)
            ).all()
        }
        for code in config["permissions"]:
            permission = permission_by_code[code]
            if permission.id in existing_perm_ids:
                continue
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))
            created_grants += 1

    db.commit()
    return {
        "permissions_created": created_permissions,
        "roles_created": created_roles,
        "grants_created": created_grants,
    }


def assign_owner_role(db: Session, user: User) -> UserRole:
    """Assign the Owner role to a user (bootstrap helper)."""
    seed_rbac_catalog(db)
    role = get_role_by_name(db, OWNER_ROLE_NAME)
    if role is None:
        raise NotFoundError("Owner role is not available.")
    return assign_role_to_user(db, user_id=user.id, role_id=role.id)


def get_user_role_names(db: Session, user: User) -> list[str]:
    statement = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id, Role.is_active.is_(True))
        .order_by(Role.name)
    )
    return list(db.scalars(statement).all())
