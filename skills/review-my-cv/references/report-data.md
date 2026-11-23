# Data for the builder

Write two JSON files (UTF-8), then run `scripts/build_document.py`. Fully worked fictional examples are in `assets/sample-cv.json` and `assets/sample-report.json`. Copy their structure, never their facts.

Plain strings only: no Markdown, HTML or bracketed placeholders. The builder rejects text such as "[add number]", "TBD" or "XX". Write for a busy reader: short sentences, and one idea per table cell.

## cv.json

```json
{
  "name": "Candidate's supplied name, or a professional heading",
  "name_is_heading": false,
  "headline": "Optional one-line identity, source-supported",
  "contact": ["City", "phone", "email", "linkedin.com/in/..."],
  "profile": "3 to 5 sentences, or a list of 2 short paragraphs",
  "key_skills": ["up to 6, each evidenced"],
  "experience": [
    {"title": "Official title", "employer": "", "location": "", "dates": "2019 to present",
     "scope": "One line: remit, team, budget, markets, reporting line", "bullets": ["3 to 5 outcome bullets"]}
  ],
  "earlier_career": [
    {"title": "", "employer": "", "dates": "", "bullets": []}
  ],
  "education": ["Degree, institution"],
  "certifications": ["Qualification, awarding body"],
  "other_sections": [{"heading": "Board roles", "items": ["..."]}]
}
```

An earlier-career role with no `bullets` prints as one compact line. Give it a `scope` and bullets when relevance to the target justifies it (see cv-rules.md). Leave out any field you have no source for.

## report.json

```json
{
  "candidate": "Supplied name, or omit",
  "subtitle": "Current identity, targeting <target> (or 'General best-practice review')",
  "date": "YYYY-MM-DD, today's date from the host",
  "source": "Original file name",
  "target": "Target role and whether a full JD or a short paragraph was supplied; omit if none",
  "summary": {"strong": "1 to 2 sentences", "changed": "1 to 2 sentences", "needs_evidence": "up to 3 decisive items"},
  "hiring_manager_read": {
    "first_impression": "One sentence: what they conclude in 30 seconds",
    "hesitations": ["2 to 4 specific doubts, each tied to something in the CV"],
    "shortlist_case": "2 to 3 sentences: the case for shortlisting, from evidence",
    "interview_probe": "What an interviewer will press on"
  },
  "ratings": [{"area": "<one of the 7 areas>", "rating": 1, "evidence": "Short quote or location", "fix": "Practical fix"}],
  "requirements": [{"requirement": "", "priority": "Essential|Desirable|Stated", "core": true, "status": "<one of the 4 statuses>",
                    "evidence": "Where in the CV", "action": "Next action or 'None'"}],
  "level_check": {"brief": "Level the JD asks for", "cv": "Level the CV shows", "result": "match|over|under|unclear", "note": "What it means and what to do"},
  "keywords": [{"term": "", "original": false, "suggested": true, "note": "Why added, or 'Not added: no evidence in your CV'"}],
  "changes": [{"label": "Applied in suggested CV|Additional evidence needed", "text": ""}],
  "before_after": [{"before": "Exact original wording", "after": "Exact suggested wording", "why": "", "quote": true}],
  "not_inflated": ["What you deliberately did not claim, and why"],
  "layout_notes": "Only if the file was scanned, tabular or multi-column and something was uncertain",
  "hygiene": [{"check": "", "result": "ok|fix|flag", "note": ""}],
  "skills_teaser": [{"skill": "Market-standard label", "evidence": "One-line pointer to the CV evidence"}],
  "carly_next": {"module": "Skills|Adjacencies|Target Map|Headhunter Call-list|Daily Alert|Diagnose", "why": "One sentence tied to the biggest gap"}
}
```

Rules the builder enforces (v1.0): exactly the seven areas; at most 8 `requirements`, with at least one marked `core` or Essential; `level_check` whenever there are requirements; a Weak role fit needs the fit-warning opening; `carly_next` with a valid module; 1 to 5 `changes`, at most 3 of them "Additional evidence needed", ranked by importance (misleading claims, essential gaps and buried decisive evidence come before presentation); at most 3 `before_after`; 3 or 4 `skills_teaser` items. Use `requirements`, `level_check` and `keywords` only when a target was supplied. Without them, the report leaves out the role-fit section and says on the cover and in the changes section that no job description was supplied.

Save the original CV as plain text and pass it with `--source`: every `before` with `"quote": true` (the default) must appear in it word for word. A "..." may join two exact fragments. Each rating's `evidence` and `fix` print in one column ("... Fix: ..."), so keep each to about 25 words.

`not_inflated` is the visible proof of the method. Include one to three honest items whenever the CV or the job description tempted an upgrade. If nothing did, omit it rather than inventing restraint.

The rating for "Skills language" also appears in the skills section of the report, so make its `evidence` short.
