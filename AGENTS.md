# AGENTS.md — Website Maintenance Guide

This file is the authoritative reference for any agent (human or AI) making changes to
this Jekyll/al-folio academic website. Read it fully before touching any file.

**Live site:** https://eslam-abdelaleem.github.io
**Owner:** Eslam Abdelaleem — Postdoctoral Fellow, Georgia Institute of Technology
**Theme:** [al-folio](https://github.com/alshedivat/al-folio) (Jekyll)
**Deployed:** GitHub Pages (push to `main` branch → auto-deploy)

---

## 1. Repo Structure — What Controls What

```
_bibliography/papers.bib     ← ALL publications (BibTeX). The single source of truth.
_data/cv.yml                 ← CV sections rendered at /cv/
_data/socials.yml            ← Social/contact icons in header & footer
_data/repositories.yml       ← GitHub repos shown at /repositories/
_news/                       ← Short announcements shown on home page
_pages/                      ← All site pages (Markdown + YAML front matter)
_projects/                   ← Research direction cards shown at /projects/
assets/pdf/                  ← PDF files (CV, primers, etc.)
assets/img/                  ← Images (profile pic, photography)
bin/update_publications.py   ← Automation script — see Section 7
```

**Do not edit:**
- `_layouts/`, `_includes/`, `_sass/` — theme files; changes here affect rendering globally
- `_config.yml` — site-wide config; only change if you know what you're doing
- `Gemfile`, `package.json` — dependency files

---

## 2. Navigation Order

Current nav bar order (left to right):

| Page | File | nav_order |
|---|---|---|
| Publications | `_pages/publications.md` | 2 |
| CV | `_pages/cv.md` | 3 |
| Projects | `_pages/projects.md` | 4 |
| Tutorials | `_pages/tutorials.md` | 5 |
| Teaching | `_pages/teaching.md` | 6 |
| Talks | `_pages/misc.md` | 7 |
| Repositories | `_pages/repositories.md` | 8 |
| Photography | `_pages/gallery.md` | 9 |

To add a new nav page, pick an unused integer. To hide a page from nav, set `nav: false`.
**Never assign the same nav_order to two pages.**

---

## 3. Adding a New Publication

### 3a. Add to `_bibliography/papers.bib`

Every paper needs these fields:

```bibtex
@article{citekey,
  abbr      = {VENUE},          % short venue label shown as badge (e.g., JMLR, PNAS, arXiv)
  author    = {Last, First and Last2, First2 and ...},
  title     = {Full paper title},
  journal   = {Full journal/conference name},
  year      = {2026},
  url       = {https://doi.org/...},
  html      = {https://doi.org/...},
  selected  = {true},           % true = appears in "Selected Publications" on home page
                                % false or omitted = appears only in full Publications list
}
```

**Optional fields:**
```bibtex
  award     = {Prize name}      % shown as a badge on the paper card
  volume    = {26},
  number    = {3},
  pages     = {1--50},
  publisher = {Publisher Name},
```

**Cite key convention:** `lastnameyearfirstword` — e.g., `abdelaleem2025deep`

**Author name format:** `Abdelaleem, Eslam` (Last, First) — this is required for author
highlighting to work correctly. The config highlights `Abdelaleem, Eslam` automatically.

**arXiv preprints:** use `abbr = {arXiv}` and link to `https://arxiv.org/abs/XXXX.XXXXX`

### 3b. Optionally create a news item

See Section 5.

---

## 4. Updating the CV Page (`_data/cv.yml`)

The CV page at `/cv/` is fully driven by this YAML file. Structure:

```yaml
- title: Section Title
  type: time_table        # or: map, list, nested_list
  contents:
    - title: Role/Degree
      institution: Organization, City, Country
      year: 2024 -- Present   # or a single year
      description:
        - "Plain text item"
        - "Another item"
```

**Existing sections:** General Information, Education, Appointments, Awards.

**To add an award:**
```yaml
- title: Awards
  type: time_table
  contents:
    - year: 2026
      items:
        - Award Name, Granting Body — for "Paper Title"
```

---

## 5. Adding a News Item (`_news/`)

News items appear on the home page (max 5 shown, newest first).

**File naming:** `_news/YYYY-MM-DD_short_description.md` or any descriptive name.

**Front matter + content:**
```markdown
---
layout: post
date: 2026-05-03       ← determines sort order
inline: true           ← true = one-line announcement style; false = full post
related_posts: false
---

Short announcement text. Use **bold** for emphasis, _italics_ for journal names,
and [link text](URL) for links.
```

**Guidelines:**
- Keep `inline: true` for all announcements (matches site style)
- One sentence to three sentences maximum
- Typical uses: new paper published, award received, media coverage, new position

---

## 6. Updating Talks (`_pages/misc.md`)

The talks page lives at `/talks/` (file: `_pages/misc.md`). It uses definition-list
Markdown syntax:

```markdown
**Year or Month Year**
:   **Conference/Venue Name**, City, Country
    _Talk Title_ — **Award if any**
```

**Sections:** Invited Talks → Selected & Contributed Talks (within each section,
newest entries first).

---

## 7. Updating Teaching (`_pages/teaching.md`)

Format:
```markdown
**Season Year**
:   **Role** — _Course Name_ (Course Number)
```

Roles: Guest Lecturer, Co-Instructor, Instructor, Teaching Assistant.
Group by institution with `### Institution Name` headers.

---

## 8. Adding/Updating Research Projects (`_projects/`)

Each file is a project card shown at `/projects/`. Front matter:

```yaml
---
layout: page
title: Project Title
description: One-sentence description shown on the card.
importance: 1          ← lower number = shown first
category: research     ← use "research" for academic projects, "software" for code
---
```

Body: 2–4 paragraphs. End with a **Key results:** line citing specific papers with
venue and year in parentheses.

**Current projects (do not duplicate):**
- `information_bottleneck.md` (importance: 1)
- `neural_circuits.md` (importance: 2)
- `physics_ml.md` (importance: 3)

---

## 9. Adding Repositories (`_data/repositories.yml`)

```yaml
github_repos:
  - owner/repo-name
```

Descriptions are pulled live from the GitHub API — update the repo description on
GitHub itself if you want different text shown on the site.

**Current repos:** `eslam-abdelaleem/NeuralMI`, `paarthgulati/dim_est`,
`paarthgulati/DYSIB_Pendulum`

---

## 10. Updating Social Links (`_data/socials.yml`)

Most socials use a single field:
```yaml
github_username: eslam-abdelaleem
linkedin_username: eslamabdelaleem
scholar_userid: 8vetn38AAAAJ
orcid_id: 0009-0006-9429-3589
arxiv_id: eslam.abdelaleem        # links to arxiv.org/a/eslam.abdelaleem.html
```

For links with no native template support, use custom social entries at the bottom:
```yaml
my_link_name:
  logo: https://example.com/favicon.ico   # or path to local SVG/PNG
  title: Display Name
  url: https://example.com/profile
```

---

## 11. Automation Script (`bin/update_publications.py`)

Checks OpenAlex (author ID: `A5093023319`) for new papers not yet in `papers.bib`.

```bash
# Normal run — interactive, prompts before writing anything
python bin/update_publications.py

# Dry run — shows what would be added, writes nothing
python bin/update_publications.py --dry-run

# Find your author ID if it ever changes
python bin/update_publications.py --find-author "Abdelaleem, Eslam"
```

**What it does:**
1. Fetches all works from OpenAlex for this author
2. Compares titles against existing `papers.bib` entries
3. For arXiv preprints, checks the arXiv API for a published version
4. Prompts you to confirm each new entry before writing
5. Optionally creates a `_news/` item for each new paper

**When to run:** After submitting or publishing a paper, or monthly as a check.

**False positives:** arXiv preprints of already-published papers may appear as "new"
if their titles differ slightly from the published version. Press `N` to skip these.

---

## 12. Common Tasks — Quick Reference

| Task | File(s) to edit |
|---|---|
| New paper published | `_bibliography/papers.bib` + optional `_news/*.md` |
| Paper won an award | Add `award = {Prize Name}` in `.bib`; add to `_data/cv.yml`; add `_news/*.md` |
| New talk or seminar | `_pages/misc.md` |
| New teaching role | `_pages/teaching.md` + `_data/cv.yml` |
| New appointment | `_data/cv.yml` |
| New research direction | New file in `_projects/` |
| Add a GitHub repo | `_data/repositories.yml` |
| Upload CV PDF | Replace `assets/pdf/Eslam_Abdelaleem_CV.pdf` |
| Add photos to gallery | Drop images into `assets/img/photography/` |
| Update bio text | `_pages/about.md` |
