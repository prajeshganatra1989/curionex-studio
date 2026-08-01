# Version and Approval Orchestration

## Version creation from workspace

`POST /scripts/{script_id}/workflow/create-version`

1. Verify workflow and project access
2. Verify required ScriptDocuments exist (`discovery_brief`, `story_spine`, `master_script`)
3. Build deterministic plain-text snapshot
4. Create draft `ContentVersion` (M2G)
5. Set workflow `active_content_version_id`
6. Set stage `versioning`, status `active`
7. Audit `workflow.version_created` (+ `workflow.stage_changed` when stage moves)
8. Commit atomically

### Snapshot format

```
DISCOVERY BRIEF

<content>

STORY SPINE

<content>

MASTER SCRIPT

<content>
```

Order is fixed; it does not depend on database insertion order.

## Review submission

`POST /scripts/{script_id}/workflow/submit-review`

1. Stage must be `versioning`
2. Active ContentVersion must exist and belong to the same project
3. Version must be draft (or otherwise eligible)
4. Create Approval via M2G (`request_approval`)
5. Version status → `in_review`
6. Workflow stage → `review`
7. Audit `workflow.review_submitted`
8. Commit atomically

Duplicate pending approvals are rejected (`409`), same as M2G.

## Approval

`POST /approvals/{approval_id}/approve`

- ContentVersion → `approved`
- Approval → `approved`
- Linked workflow (if `active_content_version_id` matches) → stage `completed`, status `completed`
- Audit includes `workflow.completed`

If no workflow references the version, M2G behavior is unchanged.

## Rejection

`POST /approvals/{approval_id}/reject`

- ContentVersion remains immutable with status `rejected`
- Approval remains history-preserving with status `rejected`
- Linked workflow → stage `workspace`, status `active`
- Audit includes `workflow.returned_to_workspace`

Rejected versions are never modified. Rework happens in ScriptDocuments, then a **new** ContentVersion is created.

## Rework loop

```
review (rejected)
  → workspace (edit ScriptDocuments)
    → create-version (new ContentVersion)
      → versioning
        → submit-review
          → review
```
