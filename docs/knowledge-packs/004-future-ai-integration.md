# Future AI Integration (concept only — not implemented in M2F)

Knowledge Packs are designed to feed later automation:

```
Knowledge Pack
    ↓
Discovery Brief
    ↓
Story Spine
    ↓
Master Script
    ↓
Voiceover
    ↓
Video / repurposed content
```

Future systems may populate or suggest section content via:

- research automation
- AI processing
- source extraction
- structured fact extraction

## M2F constraints

- No OpenAI / Claude / Gemini / ElevenLabs (or other provider) code
- No embeddings or vector storage
- Section content remains plain text, manually editable
- Structure stays predictable through the controlled section catalog

Provider integrations belong in later milestones and must remain loosely coupled to this
schema so packs stay portable across automation backends.
