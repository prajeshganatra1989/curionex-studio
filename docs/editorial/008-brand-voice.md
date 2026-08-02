# Brand Voice — Curionex Content Standard

Canonical brand voice lives on the active Content Standard (`brand_voice`, `tone_guidelines`, `language_rules`). Do not maintain a separate copy inside prompt templates.

## Voice attributes

- **Friendly** — approachable without talking down
- **Confident** — clear claims, never bluffing
- **Conversational** — natural spoken English
- **Curious** — shared wonder with the viewer
- **Trustworthy** — evidence-conscious, no hype

## Tone guidelines

- Short sentences for the ear
- No robotic or academic jargon
- Concrete verbs, everyday vocabulary
- One idea per sentence when possible

## Forbidden voice patterns

- Overhype and fear bait
- Conspiracy framing
- False certainty
- Clickbait promises

## CTA voice

Approved patterns (Content Standard):

- Follow for more fascinating facts.
- Comment your favourite fact.

## Prompt usage

Templates should inject `{{content_standard}}` (or at minimum `{{content_standard_label}}`) rather than hard-coding brand adjectives. Derived `{{brand_voice}}` remains available for older templates and is sourced from the active standard at render time.
