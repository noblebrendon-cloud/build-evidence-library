# Build Evidence Library

A local-first template for preserving completed build evidence, reusable lessons,
possible documentation derivatives, and publication history. The core principle is
simple: completed work should leave behind durable evidence, not only a commit and
fading memory.

Build Evidence Library turns a completed change into a structured event record:

```text
completed work
-> event record
-> evidence
-> teaching atoms
-> possible derivatives
-> published history
```

It is evidence-first. Public content, case studies, tutorials, release notes, and
teaching material are downstream outputs of the evidence, not automatic outputs.

## Quick Start

Create a new build event:

```bash
python tools/new_build_event.py EVT-2026-01-20-cache-timeout-fix 2026 "Cache timeout fix"
```

Re-running the same command reopens the existing event and makes no changes.

For isolated verification, write to a blank temporary output root:

```bash
python tools/new_build_event.py EVT-2026-01-20-cache-timeout-fix 2026 "Cache timeout fix" --root tmp/manual-check
```

The tool reads templates from this repository and writes event output only under the
selected output root.

## Repository

Canonical source repository:

```text
https://github.com/noblebrendon-cloud/build-evidence-library
```

## Directory Map

```text
build-evidence-library/
  BUILD_EVENT_INDEX.md
  docs/
  templates/
  examples/
  events/
  tools/
  tests/
  .github/
```

## Non-Goals

- Not a content generator.
- Not a project manager.
- Not a telemetry collector.
- Not a replacement for tests, source control, or review.
- Not a place to store secrets, customer data, credentials, or private evidence.

## Privacy And Sanitization

Before copying evidence into an event record, remove private paths, secret values,
customer data, personal data, unreleased plans, screenshots with sensitive details,
and organization-specific implementation names. The example event is fictional so the
template can be reused safely.

## Release And Archive

The v0.1.0 public license is MIT. Citation metadata lives in `CITATION.cff` for the
GitHub citation surface and `.zenodo.json` for Zenodo archive metadata. The canonical
source repository URL is recorded now that the GitHub repository exists.

- GitHub release `v0.1.0`: https://github.com/noblebrendon-cloud/build-evidence-library/releases/tag/v0.1.0
- Zenodo archive: https://zenodo.org/records/21045115
- Version DOI: `10.5281/zenodo.21045115`
- Concept DOI: `10.5281/zenodo.21045114`

The version DOI cites this exact archived `v0.1.0` release. The concept DOI resolves
to the latest archived version across the project release series.

## Public Release Checklist

- Create the public GitHub repository.
- Mark the repository as a template.
- Create GitHub Release `v0.1.0`.
- Enable Zenodo archiving for the repository.
- Verify Zenodo metadata and DOI after the archive is created.
- Add final GitHub and Zenodo links to release material.
