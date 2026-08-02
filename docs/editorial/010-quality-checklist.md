# Quality Checklist — Curionex Content Standard

Editors and AI quality review share the same checklist from the active Content Standard (`quality_checklist`).

## Checklist

| Criterion | Question |
|-----------|----------|
| **Curiosity** | Does the opening make the viewer want the answer? |
| **Clarity** | Can a general audience follow without jargon? |
| **Accuracy** | Are claims evidence-based, with uncertainty stated? |
| **Retention** | Does each beat advance the story without filler? |
| **Natural narration** | Does it sound spoken, not written for the page? |
| **Viewer payoff** | Is there a satisfying reveal or takeaway? |

## Defaults

- Duration: **60** seconds
- Target words: **160**

## Integration

- Prompt variable `quality_requirements` is derived from the active standard’s checklist at render time.
- Quality review prompts use `{{content_standard}}` so scoring criteria stay aligned with editorial policy.
- Changing the active Content Standard version updates quality guidance for new jobs automatically.

## Related

- [020-editorial-bible-v1.md](./020-editorial-bible-v1.md) — Gold / Platinum thresholds + full review criteria
- [007-curionex-content-standard.md](./007-curionex-content-standard.md)
- [008-brand-voice.md](./008-brand-voice.md)
- [009-editorial-principles.md](./009-editorial-principles.md)
