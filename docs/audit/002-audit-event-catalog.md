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
| `content_version.created` | `content_version` | Immutable content version created |
| `approval.requested` | `approval` | Approval requested for a version |
| `approval.approved` | `approval` | Approval approved |
| `approval.rejected` | `approval` | Approval rejected |
| `approval.cancelled` | `approval` | Pending approval cancelled |
| `script.created` | `script` | Script workspace created (with document shells) |
| `script.updated` | `script` | Script metadata updated |
| `script.archived` | `script` | Script archived |
| `script.document_updated` | `script` | Workspace document title/content updated |
| `ai.prompt_created` | `ai_prompt` | AI prompt created |
| `ai.prompt_updated` | `ai_prompt` | AI prompt metadata updated |
| `ai.prompt_version_created` | `ai_prompt_version` | Immutable prompt version created |
| `ai.prompt_version_activated` | `ai_prompt_version` | Prompt version activated |
| `ai.job_queued` | `ai_job` | AI job queued |
| `ai.job_started` | `ai_job` | AI job started executing |
| `ai.job_completed` | `ai_job` | AI job completed |
| `ai.job_failed` | `ai_job` | AI job failed |
| `ai.job_cancelled` | `ai_job` | AI job cancelled |
| `ai.settings_changed` | `ai_settings` | AI defaults updated |
| `ai.provider_updated` | `ai_provider` | Provider settings updated |
| `ai.provider_credentials_set` | `ai_provider` | Provider credentials stored (encrypted) |
| `ai.provider_credentials_cleared` | `ai_provider` | Provider credentials cleared |
| `ai.model_updated` | `ai_model` | Model flags updated |
| `knowledge_pack.ai_draft_applied` | `knowledge_pack` | Selected AI draft sections applied |

Reserved for future use (defined in constants / docs, not all emitted yet):

- `role.updated`

Constants live in `app/audit/actions.py`.

Note: audit metadata for content versions must **not** include full content snapshots.
Note: audit metadata for script documents must **not** include full document content.
Note: audit metadata for AI credentials must **never** include API keys or ciphertext.
