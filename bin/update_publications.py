#!/usr/bin/env python3
"""
update_publications.py — Auto-sync publications from OpenAlex.

Usage:
    # Monthly sync (interactive — prompts before writing):
    python bin/update_publications.py

    # Preview only (no files written):
    python bin/update_publications.py --dry-run

    # Search for your OpenAlex author ID if you ever need to update it:
    python bin/update_publications.py --find-author "Eslam Abdelaleem"

What it does:
  1. Fetches all papers for the author from OpenAlex (free, no API key needed)
  2. Compares against _bibliography/papers.bib
  3. Reports new papers not in the bib (with a suggested BibTeX entry)
  4. Detects preprints that have since been published (arXiv → journal)
  5. Optionally writes updated bib entries and _news/ announcement drafts

Requirements:
    pip install requests bibtexparser

OpenAlex author ID:
    Already set below as DEFAULT_AUTHOR_ID. If you ever need to find it again:
    https://openalex.org/authors?search=Eslam+Abdelaleem
    or run: python bin/update_publications.py --find-author "Eslam Abdelaleem"
"""

import argparse
import re
import sys
import time
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

try:
    import bibtexparser
    from bibtexparser.bwriter import BibTexWriter
    from bibtexparser.bibdatabase import BibDatabase
except ImportError:
    sys.exit("Missing dependency: pip install bibtexparser")

# ── Configuration ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
BIB_FILE  = REPO_ROOT / "_bibliography" / "papers.bib"
NEWS_DIR  = REPO_ROOT / "_news"

# OpenAlex author ID — verified for Eslam Abdelaleem
# Profile: https://openalex.org/A5093023319
DEFAULT_AUTHOR_ID = "A5093023319"

# Polite pool: OpenAlex gives higher rate limits when you include your email
OPENALEX_EMAIL = "eslam.abdelaleem@gatech.edu"

OPENALEX_API = "https://api.openalex.org"

# Work types that are preprints
PREPRINT_TYPES = {"preprint"}
PREPRINT_SOURCE_TYPES = {"repository"}

# ── API helpers ────────────────────────────────────────────────────────────────

def oa_get(path, params=None):
    """GET from OpenAlex API. Includes mailto for polite pool (higher rate limits)."""
    params = params or {}
    params["mailto"] = OPENALEX_EMAIL
    url = f"{OPENALEX_API}{path}"
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def oa_get_all(path, params=None, max_results=200):
    """Paginate through all results from an OpenAlex endpoint."""
    params = params or {}
    params["per-page"] = 50
    params["cursor"] = "*"
    results = []
    while len(results) < max_results:
        data = oa_get(path, params.copy())
        batch = data.get("results", [])
        results.extend(batch)
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not batch:
            break
        params["cursor"] = cursor
    return results


# ── BibTeX helpers ─────────────────────────────────────────────────────────────

def load_bib(bib_file):
    with open(bib_file, "r", encoding="utf-8") as f:
        return bibtexparser.load(f)


def title_key(title):
    """Normalised title for fuzzy matching — lowercase, alphanumeric only."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def existing_titles(db):
    return {title_key(e.get("title", "")): e for e in db.entries}


def bib_key_from(work):
    """Generate a BibTeX key like abdelaleem2025deep from an OpenAlex work."""
    authors = work.get("authorships", [])
    last = "unknown"
    for a in authors:
        name = a.get("author", {}).get("display_name", "")
        parts = name.split()
        if parts:
            last = parts[-1].lower()
            break
    year = work.get("publication_year") or "0000"
    words = re.findall(r"[a-z]+", (work.get("title") or "").lower())
    stopwords = {"a", "an", "the", "of", "in", "on", "for", "and", "or",
                 "to", "with", "from", "is", "are", "that", "this", "how",
                 "its", "using", "via", "new"}
    word = next((w for w in words if w not in stopwords and len(w) > 3),
                words[0] if words else "paper")
    return f"{last}{year}{word}"


def work_doi(work):
    doi = work.get("doi") or ""
    # OpenAlex returns full URL like https://doi.org/10.xxxx/...
    return doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()


def work_arxiv(work):
    for loc in (work.get("locations") or []):
        src = loc.get("source") or {}
        if "arxiv" in (src.get("id") or "").lower():
            landing = loc.get("landing_page_url") or ""
            m = re.search(r"arxiv\.org/abs/([\w.]+)", landing)
            if m:
                return m.group(1)
    ids = work.get("ids") or {}
    openalex_id = ids.get("openalex") or ""
    # Try ids dict
    for k, v in ids.items():
        if "arxiv" in k.lower() and v:
            return str(v).split("/")[-1]
    return ""


def work_venue(work):
    """Return a clean venue name. Normalise arXiv DOIs to 'arXiv'."""
    doi = work_doi(work)
    if doi and "arxiv" in doi.lower():
        return "arXiv"
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name") or ""


def work_is_preprint(work):
    wtype = (work.get("type") or "").lower()
    src = ((work.get("primary_location") or {}).get("source") or {})
    src_type = (src.get("type") or "").lower()
    return wtype in PREPRINT_TYPES or src_type in PREPRINT_SOURCE_TYPES


def build_bib_entry(work):
    """Build a BibTeX entry dict from an OpenAlex work object."""
    key   = bib_key_from(work)
    title = work.get("title") or ""
    year  = str(work.get("publication_year") or "")
    venue = work_venue(work)
    doi   = work_doi(work)
    arxiv = work_arxiv(work)

    authors_list = []
    for a in (work.get("authorships") or []):
        name = a.get("author", {}).get("display_name", "")
        if name:
            authors_list.append(name)
    authors = " and ".join(authors_list)

    entry = {
        "ENTRYTYPE": "article",
        "ID": key,
        "title": title,
        "author": authors,
        "year": year,
        "journal": venue,
        "abbr": venue.split()[0][:8] if venue else "Unknown",
        "selected": "{false}",
    }
    if doi:
        entry["url"]  = f"https://doi.org/{doi}"
        entry["html"] = f"https://doi.org/{doi}"
    elif arxiv:
        entry["url"]  = f"https://arxiv.org/abs/{arxiv}"
        entry["html"] = f"https://arxiv.org/abs/{arxiv}"
    return entry


def entry_to_bib_string(entry):
    db = BibDatabase()
    db.entries = [entry]
    writer = BibTexWriter()
    writer.indent = "  "
    return bibtexparser.dumps(db, writer).strip()


def news_slug(work, prefix="new_paper"):
    year  = work.get("publication_year") or date.today().year
    words = re.findall(r"[a-z]+", (work.get("title") or "").lower())
    slug  = "_".join(words[:3])
    return f"{prefix}_{year}_{slug}.md"


def build_news_entry(work, note=""):
    title = work.get("title") or "New paper"
    venue = work_venue(work) or "journal"
    doi   = work_doi(work)
    arxiv = work_arxiv(work)
    link  = (f"https://doi.org/{doi}" if doi
             else (f"https://arxiv.org/abs/{arxiv}" if arxiv else "#"))
    today = date.today().isoformat()
    lines = [
        "---", "layout: post", f"date: {today}",
        "inline: true", "related_posts: false", "---", "",
        f'New paper published in _{venue}_: **"[{title}]({link})"**.',
    ]
    if note:
        lines.append(note)
    return "\n".join(lines) + "\n"


def check_arxiv_published(arxiv_id):
    """Check arXiv API: returns (doi, journal_ref) if the preprint was published."""
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        text = resp.text
        doi_m     = re.search(r"<arxiv:doi[^>]*>(.*?)</arxiv:doi>", text)
        journal_m = re.search(r"<arxiv:journal_ref[^>]*>(.*?)</arxiv:journal_ref>", text)
        return (doi_m.group(1).strip() if doi_m else None,
                journal_m.group(1).strip() if journal_m else None)
    except Exception:
        return None, None


# ── Author search ──────────────────────────────────────────────────────────────

def find_author(name):
    print(f"\nSearching OpenAlex for: {name}\n")
    data = oa_get("/authors", {"search": name, "select": "id,display_name,works_count,affiliations"})
    authors = data.get("results", [])
    if not authors:
        print("No results found.")
        return
    print(f"{'OpenAlex ID':<25} {'Works':>6}  {'Name':<30}  Latest affiliation")
    print("-" * 85)
    for a in authors[:10]:
        oa_id  = (a.get("id") or "").replace("https://openalex.org/", "")
        affs   = a.get("affiliations") or []
        aff    = affs[0].get("institution", {}).get("display_name", "") if affs else ""
        print(f"{oa_id:<25} {a.get('works_count',0):>6}  {a.get('display_name',''):<30}  {aff}")
    print("\nCopy your ID (e.g. A5093023319) and set DEFAULT_AUTHOR_ID in this script.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing files")
    parser.add_argument("--author-id", default=DEFAULT_AUTHOR_ID,
                        help="OpenAlex author ID (default: %(default)s)")
    parser.add_argument("--find-author", metavar="NAME",
                        help="Search OpenAlex for an author and print their IDs")
    args = parser.parse_args()

    if args.find_author:
        find_author(args.find_author)
        return

    print(f"\n{'='*60}")
    print(f"  update_publications.py  (via OpenAlex)")
    print(f"  Author:    {args.author_id}")
    print(f"  Mode:      {'DRY RUN' if args.dry_run else 'LIVE (will prompt before writing)'}")
    print(f"{'='*60}\n")

    # ── 1. Load bib ──
    print(f"Loading {BIB_FILE.relative_to(REPO_ROOT)}...")
    db = load_bib(BIB_FILE)
    existing = existing_titles(db)
    print(f"  {len(db.entries)} existing entries.\n")

    # ── 2. Fetch works from OpenAlex ──
    print("Fetching works from OpenAlex...")
    works = oa_get_all(
        "/works",
        params={
            "filter": f"author.id:{args.author_id}",
            "select": "id,title,publication_year,type,doi,ids,authorships,primary_location,locations",
            "sort": "publication_year:desc",
        },
    )
    print(f"  {len(works)} works fetched.\n")

    # ── 3. Compare ──
    new_works        = []
    preprint_updates = []
    seen_title_keys  = set()  # deduplicate OpenAlex returning same paper twice

    for work in works:
        title = work.get("title") or ""
        if not title:
            continue
        key = title_key(title)

        # Skip if we already flagged this title in this run (OpenAlex duplicate)
        if key in seen_title_keys:
            continue
        seen_title_keys.add(key)

        if key not in existing:
            new_works.append(work)
        else:
            # Check if a preprint entry in our bib has been published
            bib_entry   = existing[key]
            bib_journal = bib_entry.get("journal", "").lower()
            if any(p in bib_journal for p in ("arxiv", "biorxiv", "medrxiv", "preprint")):
                arxiv = work_arxiv(work)
                if arxiv:
                    doi, journal_ref = check_arxiv_published(arxiv)
                    if doi or journal_ref:
                        preprint_updates.append({
                            "bib_entry":   bib_entry,
                            "work":        work,
                            "doi":         doi,
                            "journal_ref": journal_ref,
                        })

    # ── 4. Report new works ──
    if not new_works:
        print("✓ No new papers found — bib is up to date.\n")
    else:
        print(f"{'─'*60}")
        print(f"  NEW PAPERS ({len(new_works)} not in bib):")
        print(f"{'─'*60}")
        print("  NOTE: preprint versions of already-published papers may appear here")
        print("  if the preprint title differs from the published title. Press N for those.\n")
        for i, w in enumerate(new_works, 1):
            title = w.get("title", "?")
            venue = work_venue(w) or "?"
            year  = w.get("publication_year") or "?"
            doi   = work_doi(w)
            arxiv = work_arxiv(w)
            print(f"\n  [{i}] {title}")
            print(f"      Venue: {venue}  |  Year: {year}  |  Type: {w.get('type','?')}")
            if doi:   print(f"      DOI:   {doi}")
            if arxiv: print(f"      arXiv: {arxiv}")

            bib_str = entry_to_bib_string(build_bib_entry(w))
            print(f"\n  Suggested BibTeX:")
            for line in bib_str.splitlines():
                print(f"    {line}")

            if not args.dry_run:
                ans = input("\n  Add to papers.bib? [y/N/s(kip all)] ").strip().lower()
                if ans == "s":
                    print("  Skipping remaining.")
                    break
                if ans == "y":
                    entry = build_bib_entry(w)
                    db.entries.append(entry)
                    print(f"  ✓ Added {entry['ID']}.")
                    news_ans = input("  Create _news/ announcement? [y/N] ").strip().lower()
                    if news_ans == "y":
                        fname = news_slug(w, "new_paper")
                        path  = NEWS_DIR / fname
                        if not path.exists():
                            path.write_text(build_news_entry(w))
                            print(f"  ✓ Created {path.relative_to(REPO_ROOT)}")
                        else:
                            print(f"  ⚠ {fname} already exists — skipped.")

    # ── 5. Preprint → published ──
    if not preprint_updates:
        print("✓ No preprint → published transitions detected.\n")
    else:
        print(f"\n{'─'*60}")
        print(f"  PREPRINT UPDATES ({len(preprint_updates)}):")
        print(f"{'─'*60}")
        for upd in preprint_updates:
            bib = upd["bib_entry"]
            w   = upd["work"]
            doi = upd["doi"]
            jr  = upd["journal_ref"]
            print(f"\n  Entry:   {bib.get('ID')}")
            print(f"  Title:   {bib.get('title')}")
            print(f"  Current: {bib.get('journal')}")
            if doi: print(f"  DOI:     {doi}")
            if jr:  print(f"  Ref:     {jr}")

            if not args.dry_run:
                ans = input("\n  Update entry? [y/N] ").strip().lower()
                if ans == "y":
                    for e in db.entries:
                        if title_key(e.get("title", "")) == title_key(bib.get("title", "")):
                            if jr:  e["journal"] = jr
                            if doi:
                                e["url"]  = f"https://doi.org/{doi}"
                                e["html"] = f"https://doi.org/{doi}"
                            for k in ("note", "eprint"):
                                e.pop(k, None)
                            print(f"  ✓ Updated {e['ID']}.")
                    news_ans = input("  Create _news/ announcement? [y/N] ").strip().lower()
                    if news_ans == "y":
                        fname = news_slug(w, "published")
                        path  = NEWS_DIR / fname
                        if not path.exists():
                            path.write_text(build_news_entry(w, "(Previously an arXiv preprint.)"))
                            print(f"  ✓ Created {path.relative_to(REPO_ROOT)}")

    # ── 6. Save bib ──
    if not args.dry_run:
        writer = BibTexWriter()
        writer.indent = "  "
        with open(BIB_FILE, "w", encoding="utf-8") as f:
            f.write(bibtexparser.dumps(db, writer))
        print(f"\n✓ Saved {BIB_FILE.relative_to(REPO_ROOT)}")

    print(f"\n{'='*60}")
    print("  Done.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
