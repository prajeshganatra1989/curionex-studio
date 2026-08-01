# Audit Event Catalog (initial)

Stable action codes currently emitted by Curionex Studio. This catalog will grow with new modules.

| Action | Entity type | When |
|--------|-------------|------|
| `authentication.login` | `user` | Successful login |
| `authentication.login_failed` | `authentication` | Failed login (safe metadata only) |
| `user.created` | `user` | User account created |
| `user.updated` | `user` | Profile fields updated |
| `user.deactivated` | `user` | User deactivated |
| `role.created` | `role` | Role created |
| `role.assigned` | `user` | Role assigned to user |
| `role.removed` | `user` | Role removed from user |
| `permission.assigned` | `permission` | Permission granted to a role |

Reserved for future use (defined in constants / docs, not all emitted yet):

- `role.updated`

Constants live in `app/audit/actions.py`.
