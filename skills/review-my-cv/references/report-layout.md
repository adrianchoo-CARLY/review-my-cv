# Building the two Word files

There is no bundled builder. Create both files as editable Word (.docx) documents with the host's own document tools (for example a docx skill, or python-docx if the host provides it). Follow this guide exactly so every report looks the same. Plan the content first with `report-data.md`, then lay it out here.

## Fixed rules you compute yourself

**Writing verdict** (from the seven ratings of the original CV; "unassessed" counts as neither):
- **Needs rework:** three or more areas rated 1.
- **Ready to send:** no area rated 1 and at least four rated 3.
- **Needs sharpening:** everything else.

Pair it with one sentence: Needs rework, "Several core areas need rebuilding before this CV competes."; Ready to send, "Your original CV already makes a credible case. The suggestion sharpens it."; Needs sharpening, "The experience is there, but the original CV undersells or obscures it." Always add: "This rates the document, not you or your chances."

**Role fit** (only with a target). Score each requirement: Clearly demonstrated 1, Partly demonstrated 0.5, Not demonstrated in supplied material 0, Confirmed gap 0. Average the scores over requirements that are not Desirable (over all of them if every one is Desirable). "Core" means marked core or Essential.
- **Weak:** any core requirement Not demonstrated or a Confirmed gap, or half or more of all requirements not shown, or an average below 0.5.
- **Partial:** otherwise, if any core requirement is only Partly demonstrated, or the average is below 0.8.
- **Strong:** everything else.

Fit sentences: Weak, "X of Y requirements are not shown in your CV, including what the role treats as core. Better wording cannot close this; only evidence can."; Partial, "Your CV shows much of what the role asks for, but at least one core requirement is only partly shown. That is where a hiring manager will press."; Strong, "Your CV shows evidence for the core requirements of this role."

## Brand

- Colours: navy #0F1B2D (text, headings, header rows, callouts), deep navy #1C2C44 (sub-headings), gold #C8A24A (rules, accents), dark gold #A9853A (eyebrow labels, links), slate #5A6779 (secondary text), cream #F7F4EE (tiles, alternate table rows), warm cream #EFE9DF (note boxes), divider #E4DDD0 (table borders), light #D4DCEB (text on navy). Status colours: green #2E7D5B, gold #C8A24A, red #B5483B.
- Fonts: Georgia for the report title, section headings and big numbers; Arial for everything else. Body 10 pt.
- Page: A4, top margin 1.25", bottom 0.9", sides 1".

## Report page furniture

- **Header (every page except the first):** `assets/cai-logo.png` on the left, about 2.5" wide, keeping its proportions; on the right, in small slate capitals with wide letter spacing, "REVIEW MY CV · ASSESSMENT" followed by " · <CANDIDATE NAME IN CAPITALS>" when a name was supplied; a thin divider line under it. **First page:** the logo only.
- **Footer (every page), required word for word:** "© <year> Career Agility International Pte Ltd. Review My CV v1.0.1. AI-assisted.  Contact: info@CareerAgility.org", 7 pt slate, with a thin divider above and "Page N" right-aligned on every page except the first.

## Report building blocks

- **Eyebrow:** a small label above a heading, dark gold, bold, capitals, wide letter spacing (for example "SECTION 2").
- **Section heading:** Georgia 17 pt navy, with a gold rule beneath it. Each section starts on a new page unless stated.
- **Callout:** a navy box with a thick gold bar on its left edge; a small gold capital label, a large Georgia line in white, then an optional sentence in light text.
- **Note box:** a warm cream box with a gold bar on the left; a bold Georgia title, then plain paragraphs.
- **Tiles:** a row of two or three cream boxes, each with a big Georgia value on top and a small slate label below.
- **Table:** a navy header row with white bold text, alternating white and cream rows, thin divider borders, first column bold, header row repeated if the table breaks across pages, rows not split across pages.
- **Rating meter:** three squares (■) in a cell, filled navy up to the rating and pale grey after it (all three gold for a 3), followed by Weak, Adequate or Strong.
- **Status marks:** ● green Clearly demonstrated, ● gold Partly demonstrated, ○ slate Not demonstrated in supplied material, ● red Confirmed gap.
- **Health marks:** ✓ green "Fine", ! dark gold "Fixed in suggestion", ✗ red "Your action".

## Report sections, in order

1. **Cover (page 1).** A navy box: gold capitals "REVIEW MY CV · ASSESSMENT REPORT"; the candidate's supplied name (or "Your CV Assessment") in large white Georgia; the subtitle in italic light Georgia; "Assessed <day Month year> · Source: <file name>". Then eyebrow "AT A GLANCE" and three tiles: with a target, the writing verdict (gold), the role fit (green, gold or red for Strong, Partial or Weak) and "X of Y" requirements clearly evidenced; without one, the writing verdict, "X of 7" areas rated strong, and "Not assessed" with the label "Role fit: no job description supplied". Then eyebrow "THE 30-SECOND READ" and a two-column table: What's strong, What changed, What still needs evidence. Then this note box, word for word:
   - Title: "Your CV, read through the eyes of the person who decides"
   - "Most CV tools write from the candidate's side, to make you sound good. This assessment reads your CV the way a hiring manager or C-suite headhunter does: what they notice first, what makes them doubt you, and what gets you shortlisted."
   - "The method draws on more than 50 years of combined C-suite headhunting and career coaching, and tens of thousands of CVs reviewed, by Adrian Choo and Sze-Yen Chee. This report is AI-assisted: it applies their method, and they have not personally reviewed it."
2. **Section 1: "Here Is How a Hiring Manager Reads Your CV".** Callout "IN THE FIRST 30 SECONDS" with the first impression. Sub-heading "What makes them hesitate" with the hesitations as bullets. Sub-heading "What gets you shortlisted" with the shortlist case. Note box "What an interviewer will probe".
3. **Section 2: "Here Is How Your Original CV Scores".** Callout "VERDICT ON THE WRITING" with the writing verdict and its sentence (with a target, add "Fit for the target role is assessed separately in the next section."). If the host can make a simple chart image, add a small radar or bar chart of the seven ratings in navy and gold; otherwise skip it. Then a table: Area | Rating (meter) | "What we saw in your original CV, and the fix" (evidence, then "Fix: ..."). Keep the section to one page.
4. **Section 3: "Here Is How You Match the Role"** (only with a target). "Target: <role>" line. Callout "ROLE FIT" with the fit and its sentence. Note box "Level check: <In line with the brief | Above the brief | Below the brief | Not clear from the job description>" with three lines: "The role asks for: ...", "Your CV shows: ...", and what it means. Requirements table: Requirement (add " (core)" to core ones) | Priority | Evidence status (status mark) | Where it shows in your CV | Next action. Sub-heading "Key terms from the job description", one sentence ("X of N key terms appeared in your original CV; Y of N appear in the suggested CV, added only where your own experience supports them."), then a two-column table with up to three rows: "✓ Already in your CV", "+ Added, with evidence" (each term with its reason in brackets), "– Not added: no evidence".
5. **"Here Is Your CV Health Check"** (no page break). One line: "Basic checks a hiring manager or recruiter makes before reading properly. Items marked ✗ need your action in Word." Table: Check | Result (health mark) | Detail.
6. **"Here Is What We Changed, and Why".** Without a target, start with a bold dark-gold "No job description supplied:" and "your CV was improved against general best practice for experienced professionals. Run Review My CV again with a job description to see how you match a specific role." Then the changes as a numbered list, each starting with its label in bold (green for "Applied in suggested CV", dark gold for "Additional evidence needed"). Sub-heading "Before and after", table: Your original CV (italic slate) | Suggested CV | Why it reads better. Note box "What we refused to inflate, and why". Note box "How we read your file" only when there are layout notes.
7. **"Here Is the Skills Language Recruiters Search For".** The sentence "Recruiters and applicant tracking systems search for specific, named capabilities. Most CVs describe the work in job titles, tools or in-house language instead, so strong candidates never surface." A one-row box: "Your original CV" | the Skills language meter and its evidence. Sub-heading "A sample of what your experience already supports", table: Skill, in recruiter language | Your evidence. Then one paragraph: bold dark gold "Optional next step: ", then "CARLY™ <module>, from Career Agility International, <what the module does>. <why>" and the link www.careeragility.org/carly. Nothing more about CARLY™.
8. **Close (same page).** Eyebrow "YOUR NEXT STEPS" with three bullets: "Open your suggested improved CV in Word and check every date, number, title and claim."; "Add any evidence marked "Additional evidence needed", if you have it. Wording cannot create experience you do not have."; "Fix any health-check items marked ✗." Eyebrow "IMPORTANT NOTES" with three small slate paragraphs: the accuracy notice word for word ("This AI-assisted CV and assessment are suggestions, not a guarantee of employment; you are responsible for checking all facts and claims before using them."); "AI-assisted assessment using the Career Agility International method. Ratings describe the original supplied CV, not hiring probabilities. Evidence statuses describe what your CV shows: "Not demonstrated in supplied material" means we could not see it, not that you lack it."; and "Questions about this report? Contact: info@CareerAgility.org".

CARLY™ module descriptions: Skills, "maps your experience to the market-standard skills recruiters search for."; Adjacencies, "tests which adjacent roles and industries your experience transfers to, and what it takes to cross."; Target Map, "maps the companies and contacts worth approaching for your target role."; Headhunter Call-list, "finds the search consultants who cover your field and level."; Daily Alert, "watches the market each day for roles that match your profile."; Diagnose, "pinpoints why a job search is stalling and what to fix first."

Aim for six to eight pages. Never add an empty cover page.

## The suggested CV

Clean, editable and unbranded: no logo, header, Career Agility International, CARLY™ or Review My CV text anywhere.

- A4, margins 0.7" top and bottom, 0.75" sides. Arial 10 pt navy body; the name in Georgia 22 pt.
- Order: name (or the professional heading), headline in bold deep navy, contact line in slate separated by " | ", then sections headed in bold navy capitals with a thin divider under each: PROFILE, KEY SKILLS (items separated by " · "), PROFESSIONAL EXPERIENCE, EARLIER CAREER, EDUCATION, PROFESSIONAL QUALIFICATIONS, then any other sections.
- Each role: a line with the bold official title, " | Employer, Location", and the dates right-aligned on the same line with a right tab stop; a scope line in italic slate; then bullets. An earlier-career role with no bullets is one compact line.
- Page number centred in the footer, nothing else in headers or footers.
- Use real Word bullets and headings, single column, no tables, text boxes or images.

## Self-check before delivery (what a builder would have enforced)

Open both finished files (render them to images if the host can) and confirm every item. Fix and rebuild if any fails.

- Exactly the seven areas, each rated 1, 2, 3 or unassessed. The verdict and role fit match the rules above.
- With a target: six to eight requirements, at least one core, a level check, and, if the role fit is Weak, a first impression that starts "Well written, but a weak match for this role: X of Y requirements are not shown in your CV." (replace "Well written" when the writing verdict is not Ready to send).
- One to five changes, at most three marked "Additional evidence needed". At most three before-and-after rows. Three or four skills in the sample. One CARLY™ module named.
- Every "before" quote appears word for word in the original CV (a "..." may join two exact fragments); a structural change is described, not shown as a quote.
- No placeholders anywhere: nothing in square brackets, no "TBD", "XX" or "lorem ipsum".
- The CV mentions no Career Agility International, CARLY™ or Review My CV, every role has its official title, and it renders to three pages or fewer.
- The report footer text and the contact line in Important notes are present, and the footer appears on every page.
