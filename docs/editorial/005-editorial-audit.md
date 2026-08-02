# Editorial Audit — v0.21.1

**Scope:** Full review of the `curionex-evergreen-v1` seed library (100 topics).  
**Method:** Editorial quality audit for YouTube Shorts (45–60s). No database, seed, API, or UI changes in this release.  
**Companion export:** [editorial_audit.csv](./editorial_audit.csv)

## Executive summary

The Editorial Library is **production-ready as a planning corpus**, with a strong concentration of curiosity-forward, mythbust, and scale-wow titles across ten categories. Most topics already use Why/How/What hooks and can fit a compelling Short with disciplined scripting.

Primary gaps are not “empty categories” but **title precision**, **scientific overclaim risk**, and a **small cluster of near-duplicate animal/physics beats**. Four topics are recommended for removal and replacement; one near-duplicate should be merged or sharply differentiated before production.

| Metric | Count |
|--------|------:|
| Topics reviewed | **100** |
| KEEP | **79** |
| IMPROVE TITLE | **16** |
| MERGE | **1** |
| REMOVE | **4** |
| Tier A (produce first) | **51** |
| Tier B (queue next) | **39** |
| Tier C (deprioritize / fix) | **10** |

**Verdict:** Keep 79 topics as-is; apply title improvements before filming the IMPROVE set; do not auto-replace seeds in this sprint — apply decisions in a later editorial curation pass.

## Scoring criteria applied

1. **Evergreen value** — lasting interest beyond news cycles  
2. **Curiosity / hook potential** — scroll-stopping first line  
3. **45–60s explainability** — one idea, one reveal, one payoff  
4. **Broad audience appeal** — ages ~16–40 science-curious default  
5. **Scientific / historical reliability** — defendable without heavy caveats  
6. **Title clarity** — Why/How/What preferred; avoid vague nouns  
7. **Uniqueness** — distinct beat vs rest of library  
8. **Duplicate risk** — exact / near / concept overlap  
9. **Production priority** — A / B / C queueing

Scores in the CSV are **audit scores** (Editorial Director). Seed scores remain unchanged in the database.

## Decision totals

- **KEEP (79):** Fit for Shorts production with current title (minor script hedges OK).  
- **IMPROVE TITLE (16):** Concept is strong; rename before Create Project / filming.  
- **MERGE (1):** Near-duplicate of another topic — differentiate hard or combine into one series plan.  
- **REMOVE (4):** Weak fit for Curionex educational Shorts brand; replace (recommendations below).

## Priority tiers

### Tier A — 51 topics (produce first)

High evergreen + curiosity, clear Short structure, reliable core claim. Examples: dream forgetting, Dunning–Kruger, neutron-star teaspoon, Cleopatra timeline, octopus anatomy, GPS/relativity, taste-map mythbust.

### Tier B — 39 topics (standard queue)

Solid library depth; may need tighter scripting, softer claims, or slightly longer runtime.

### Tier C — 10 topics (fix, hedge, or replace)

Contested science framing, weak brand fit, vague hooks, or recommended removals.

## Duplicate report

### Exact duplicates

**None.** No two titles or slugs are identical.

### Near duplicates / concept overlap

| Group | Topics | Recommendation |
|-------|--------|----------------|
| Crustacean strike / cavitation | *Mantis shrimp punch* + *Pistol shrimp bubble* | **MERGE or differentiate:** keep mantis as punch-speed Short; pistol only if framed as *sound/heat bubble weapon*, not a second “super punch.” Prefer one filmed first, second only after 90 days. |
| Neutron-star wow | *Teaspoon weight* + *Gold from collisions* | **KEEP both** as a mini-series (density → origin of heavy elements). Not duplicates. |
| Bias family | *Confirmation bias* + *Cognitive dissonance* | **KEEP both**; related but distinct mechanisms. Avoid back-to-back publish. |
| Sleep / brain maintenance | *Glymphatic wash* + *Brain calorie burn* | **KEEP both**; different hooks. |
| Bioluminescence cluster | *Ocean glow* + *Fireflies* + *Human glow* | **KEEP all**; different organisms/mechanisms. Space publishes ≥2 weeks apart. |

### Title collision risk

Vague *“This [animal]…”* patterns (tardigrade, mantis/pistol shrimp, axolotl, jellyfish) increase thumbnail/title sameness — addressed under IMPROVE TITLE.

## Shorts suitability (45–60s)

### Fit well (majority)

Most Easy/Medium A/B topics with a single reveal (mythbust, scale fact, body paradox).

### Borderline — keep, but script tightly

| Topic | Risk |
|-------|------|
| Why is the night sky dark… | Olbers’ paradox needs careful pacing |
| Double-slit intro | Easy to mystify; one demo, one takeaway |
| Absolute zero unreachable | Abstract; one analogy only |
| Cognitive dissonance | Needs a single concrete example |
| Plants / quantum photosynthesis | Contested; must hedge |
| Earth’s inner core may spin faster… | Evolving research; provisional language |

### Poor fit → REMOVE + replace

See Remove list and Replacement recommendations.

## IMPROVE TITLE list (16)

| Current title | Recommended title |
|---------------|-------------------|
| You Don't Use Only 10% of Your Brain — Here's the Real Number | Why the 'You Only Use 10% of Your Brain' Myth Is Totally Wrong |
| The Brain Cells That Make You Feel What Others Feel | Why Watching Someone Else Yawn Makes You Yawn Too |
| Believing You Can Improve Actually Makes You Smarter | Why Believing You Can Improve Changes How You Learn |
| Jupiter Acts Like a Cosmic Shield for Earth | Does Jupiter Really Protect Earth From Asteroids? |
| The Pressure at the Bottom of the Ocean Can Crush a Submarine | Why the Deepest Ocean Could Crush a Submarine Instantly |
| Some Ocean Waves Glow Blue at Night — Here's the Science | Why Some Ocean Waves Glow Blue at Night |
| Nothing Can Go Faster Than Light — Not Even Thought Experiments | Why Nothing in the Universe Can Outrun Light |
| Your Hard Drive Doesn't Have a Little Arm Reading a Spiral | How a Hard Drive Reads Data Without Touching the Disk |
| This Tiny Animal Survives the Vacuum of Space | How Tardigrades Survive the Vacuum of Space |
| This Shrimp Punches as Fast as a .22 Bullet | Why the Mantis Shrimp Punches Faster Than a Bullet |
| This Salamander Can Regrow Its Brain and Heart | How Axolotls Regrow Their Brain and Heart |
| Your Bones Are Stronger Than Steel — Pound for Pound | Why Your Bones Are Stronger Than Concrete — Pound for Pound |
| Microbes in Your Gut Outnumber Your Own Cells | Why Your Gut Microbes Shape Digestion, Immunity, and Mood |
| Your Immune System Kills Thousands of Threats While You Read This | What Your Immune System Does in the Next 60 Seconds |
| Trees Talk to Each Other Through an Underground Fungal Internet | How Trees Share Nutrients Through Underground Fungal Networks |
| This Jellyfish Can Reverse Its Aging and Start Over | How This Immortal Jellyfish Reverses Its Aging |

## MERGE list (1)

| Topic | Recommended title if kept distinct | Notes |
|-------|------------------------------------|-------|
| This Shrimp Creates a Bubble Hotter Than the Sun's Surface | How the Pistol Shrimp Makes a Bubble Hotter Than the Sun | Near-duplicate of mantis shrimp punch/cavitation; keep only if sharply differentiated OR merge into crustacean-weapons series. |

## REMOVE list (4)

| Topic | Category | Why remove |
|-------|----------|------------|
| Planes Fly Because of Pressure — Not Just Engine Thrust | Science | Oversimplified aerodynamics risk; replace with clearer flight physics topic. |
| Your Password Alone Isn't Enough Anymore | Technology | Security advice more than curiosity science; replace with deeper tech physics. |
| The Cloud Is Just Someone Else's Computer in a Warehouse | Technology | Dated meme; low educational depth for Curionex brand. |
| Abraham Lincoln Was a Licensed Bartender | History | Trivia vs educational mission; weak Shorts fit for Curionex. |

## Replacement recommendations

Replace REMOVEd topics with high-curiosity, Shorts-native ideas (do **not** seed in this release):

| Replace | Suggested replacement title | Category |
|---------|----------------------------|----------|
| Bernoulli / pressure-only flight | Why Airplane Wings Don't Work the Way Your Textbook Said | Science |
| Password / 2FA advice | How Your Phone's Fingerprint Sensor Actually Sees You | Technology |
| Cloud is someone else's computer | Why Undersea Cables Carry Almost All Internet Traffic | Technology |
| Lincoln bartender trivia | Why We Still Don't Know Who Invented Zero | History |

Optional backlog (growth toward 1,000 evergreen topics):

- Why Can't You Remember Being a Baby?
- What Happens to Your Body in Free Fall for 60 Seconds?
- How Black Holes Can Bend Time
- Why Blood Is Red but Veins Look Blue
- What Happens When You Freeze Helium
- How Vaccines Teach Your Immune System Without Making You Sick
- Why Cats Always Land on Their Feet
- How Glass Is Actually a Liquid (Or Is It?) — careful mythbust
- Why Time Zones Exist
- How Coral Reefs Are Built by Tiny Animals

## Category health snapshot

| Category | KEEP | IMPROVE | MERGE | REMOVE | Notes |
|----------|-----:|--------:|------:|-------:|-------|
| Animals | 6 | 3 | 1 | 0 | — |
| Biology | 8 | 2 | 0 | 0 | — |
| Earth | 8 | 2 | 0 | 0 | — |
| History | 9 | 0 | 0 | 1 | — |
| Human Body | 7 | 3 | 0 | 0 | — |
| Human Brain | 8 | 2 | 0 | 0 | — |
| Psychology | 9 | 1 | 0 | 0 | — |
| Science | 8 | 1 | 0 | 1 | — |
| Space | 9 | 1 | 0 | 0 | — |
| Technology | 7 | 1 | 0 | 2 | — |

## Production guidance (no workflow changes)

1. Prefer **Tier A** when choosing Create Project from `/topics`.  
2. Apply **Recommended Title** before filming IMPROVE items.  
3. Do not film pistol-shrimp until mantis-shrimp differentiation is locked.  
4. Soft-archive REMOVE candidates in a future curation sprint (not this audit).  
5. Keep seed catalog frozen until an explicit curation release.

## Out of scope (confirmed)

- No AI generation  
- No database / seed / migration edits  
- No backend API or frontend changes  
- No Production Mode workflow changes  

## Related docs

- [001-editorial-library.md](./001-editorial-library.md)
- [002-topic-lifecycle.md](./002-topic-lifecycle.md)
- [003-topic-seeding.md](./003-topic-seeding.md)
- [004-create-project-from-topic.md](./004-create-project-from-topic.md)
