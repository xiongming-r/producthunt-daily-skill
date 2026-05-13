# Core And Skill Iteration Roadmap

## Principle

The skill is the primary product surface. The CLI core is the stable execution engine.

## Core Track

- Owns `src/ph_daily`.
- Provides deterministic Product Hunt fetching, filtering, enrichment, output, and tests.
- Adds stable CLI capabilities only when they benefit both direct script users and skill users.

## Skill Track

- Owns `skills/producthunt-daily`.
- Provides Agent instructions, setup workflow, templates, Agent Mode guidance, and distribution.
- Evolves faster than the core as agent workflows change.

## Versioning

Use release notes to record both dimensions:

```text
Core: 0.3.0
Skill: 0.1.0
```

## Near-Term Priorities

1. Agent Mode with `--no-enrichment`.
2. Exportable self-contained skill package.
3. Skill validation and hygiene checks.
4. Agent-side enrichment templates and examples.
