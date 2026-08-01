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
| `project.created` | `project` | Project created |
| `project.updated` | `project` | Project fields updated |
| `project.archived` | `project` | Project archived (DELETE lifecycle) |
| `project.member_added` | `project` | User added to project members |
| `project.member_removed` | `project` | User removed from project members |
| `category.created` | `category` | Category created |
| `category.updated` | `category` | Category updated |
| `tag.created` | `tag` | Tag created |
| `tag.updated` | `tag` | Tag updated |
| `knowledge_pack.created` | `knowledge_pack` | Knowledge Pack created (with section shells) |
| `knowledge_pack.updated` | `knowledge_pack` | Knowledge Pack fields updated |
| `knowledge_pack.archived` | `knowledge_pack` | Knowledge Pack archived |
| `knowledge_pack.section_updated` | `knowledge_pack` | Section title/content updated |
| `knowledge_pack.sections_reordered` | `knowledge_pack` | Section positions updated |

Reserved for future use (defined in constants / docs, not all emitted yet):

- `role.updated`

Constants live in `app/audit/actions.py`.
