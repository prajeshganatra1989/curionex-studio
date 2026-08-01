# Permission Catalog (initial)

Stable permission codes used by Curionex Studio authorization.

> Roles are configurable. Application logic must authorize on **codes**, not role names.

| Code | Name |
|------|------|
| `users.view` | View users |
| `users.create` | Create users |
| `users.update` | Update users |
| `users.deactivate` | Deactivate users |
| `roles.view` | View roles |
| `roles.create` | Create roles |
| `roles.update` | Update roles |
| `roles.assign` | Assign roles |
| `projects.view` | View projects |
| `projects.create` | Create projects |
| `projects.update` | Update projects |
| `projects.delete` | Delete projects |
| `knowledge_packs.view` | View knowledge packs |
| `knowledge_packs.create` | Create knowledge packs |
| `knowledge_packs.update` | Update knowledge packs |
| `knowledge_packs.delete` | Delete knowledge packs |
| `scripts.view` | View scripts |
| `scripts.create` | Create scripts |
| `scripts.update` | Update scripts |
| `scripts.delete` | Delete scripts |
| `versions.view` | View versions |
| `versions.create` | Create versions |
| `approvals.view` | View approvals |
| `approvals.create` | Create approvals |
| `approvals.approve` | Approve |
| `approvals.reject` | Reject |
| `audit.view` | View audit logs |
| `settings.view` | View settings |
| `settings.update` | Update settings |

Not every code has an implemented feature endpoint yet. Codes are reserved so future milestones can authorize consistently.

Seed with:

```bash
python -m app.cli.seed_rbac
```
