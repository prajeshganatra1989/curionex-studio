# Role Catalog (initial defaults)

Initial roles are **seed data**. They can be changed in the database / admin APIs.
Authorization always uses permission codes, not these names.

## Owner

Full access to all currently defined permissions.

Bootstrap:

```bash
python -m app.cli.create_user \
  --email you@example.com \
  --first-name Your \
  --last-name Name \
  --assign-owner
```

## Admin

Same initial permission set as Owner for v0.4.0 (administrative access).
Future milestones may differentiate ownership-only actions.

## Content Manager

Manages projects, knowledge packs, and scripts; can view approvals.

Includes: `projects.*` (view/create/update), knowledge pack view/create/update,
script view/create/update, versions view/create, approvals.view.

## Script Writer

Creates and edits scripts within accessible projects.

Includes: projects.view, knowledge_packs.view, scripts view/create/update,
versions view/create.

Does **not** include user management or approval decisions.

## Reviewer

Reviews content and can approve or reject.

Includes: projects.view, knowledge_packs.view, scripts.view, versions.view,
approvals.view / approve / reject.

## Notes

- Assign multiple roles to combine permissions
- Deactivate a role (`is_active=false`) to revoke its grants without deleting history links
- Prefer adding permissions to roles over hard-coding role checks in code
