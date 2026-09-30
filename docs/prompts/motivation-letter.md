# Prompt template: motivation letter

## 1. What this prompt does

It writes a one-page motivation letter (cover letter) for one job posting, as an editable Word document. It researches the company first, opens with one specific and true connection between you and this employer, and tells a short story with one or two real proof points from your CV, instead of listing everything you have done.

## 2. What you need to fill in

- $\color{orange}{\texttt{\{\{YOUR\_NAME\}\}}}$: your full name, as it should appear in the signature. Example: `Alex Example`
- $\color{orange}{\texttt{\{\{YOUR\_CONTACT\_DETAILS\}\}}}$: the sender block: city with postal code, phone, e-mail. Example: `12345 Example City, +00 000 0000000, alex.example@example.com`
- $\color{orange}{\texttt{\{\{YOUR\_CV\}\}}}$: your CV or structured profile, the only allowed source of facts about you. Example: `the attached master_cv.tex`
- $\color{orange}{\texttt{\{\{JOB\_POSTING\}\}}}$: the full text of the posting. Example: the pasted job ad for *Working Student Data Analytics*
- $\color{orange}{\texttt{\{\{COMPANY\_NAME\}\}}}$: the employer's name. Example: `Contoso GmbH`
- $\color{orange}{\texttt{\{\{JOB\_TITLE\}\}}}$: the job title as written in the posting. Example: `Working Student Data Analytics (m/f/d)`
- $\color{orange}{\texttt{\{\{CONTACT\_PERSON\}\}}}$: the named contact in the posting, or `none`. Example: `Ms. Jane Doe`
- $\color{orange}{\texttt{\{\{OUTPUT\_LANGUAGE\}\}}}$: the language the letter should be written in, your choice (usually the language of the posting). Example: `German`
- $\color{orange}{\texttt{\{\{LANGUAGE\_LEVEL\}\}}}$: how simple the language should be. Example: `B2: short sentences, everyday words`
- $\color{orange}{\texttt{\{\{AVAILABILITY\}\}}}$: when you can start and how many hours per week. Example: `from 1 October, up to 20 hours per week, more during semester breaks`

## 3. The prompt

```text
Write a motivation letter for the position {{JOB_TITLE}} at {{COMPANY_NAME}}, in {{OUTPUT_LANGUAGE}}, as a native, editable .docx file (not a PDF). I will edit it by hand before sending. Maximum one A4 page.

INPUTS
- My CV, the only source of facts about me: {{YOUR_CV}}
- The job posting: {{JOB_POSTING}}
- Contact person: {{CONTACT_PERSON}}

TRUTHFULNESS
- Every statement about me must be grounded in my CV. Never invent a skill, experience, trait or interest.
- Never claim a specialization, focus or qualification that I haven't stated in my CV. Describe interests as interests.
- Only use completed courses, projects or jobs as proof points, never planned ones.

RESEARCH FIRST
- Read the posting carefully, then look up the company (its own website and the posting) for a few sentences of real grounding: what it does, for whom, what this role contributes.
- Find one authentic, specific connection between me and this company or role. It must be true and already visible in my CV. No generic praise of the company.

CONTENT
- The letter must show motivation and who I am, not only data. Do not list courses, modules or skills one after another. Weave one or two concrete proof points from my CV into a short story about what I enjoy or why this work matters to me.
- Name 2-3 concrete tasks from the posting and connect them to real items in my CV.
- If the posting asks for something I don't have yet, write one honest sentence that turns the gap into a wish to learn it. That is the one place for enthusiasm; don't scatter it across every paragraph.
- Language level: {{LANGUAGE_LEVEL}}. Short sentences, common words, no abstract nouns, idioms or long subordinate clauses.
- Abbreviations: the first time, write the full term with the abbreviation in brackets; after that, use only the abbreviation.
- No salesy or flattering phrasing. No dashes as sentence connectors.

STRUCTURE (no visible section labels)
- Sender block: {{YOUR_NAME}}, {{YOUR_CONTACT_DETAILS}}. Then the recipient, then the date (right-aligned), then a bold subject line "Application for {{JOB_TITLE}}" (in the letter's language).
- Salutation: if the posting names a contact person ({{CONTACT_PERSON}}), greet them by name; otherwise use a general greeting.
- Opening: start with the researched, specific connection, not with "I read your posting with interest".
- Middle: the story with one or two proof points, plus the honest gap sentence if relevant.
- Closing: availability ({{AVAILABILITY}}) and that I would like to talk. Write start dates so they can't be read as end dates (e.g. "from 01.10." not "to 01.10."). Don't mention remote or on-site work unless the posting requires it, and don't mention documents (transcripts, certificates) unless the posting asks for them.
- Formal closing and my name: {{YOUR_NAME}}.
- Same order every time, so parsers and recruiters know where to look.

FORMATTING FOR APPLICANT-TRACKING SYSTEMS
- Plain paragraphs only: no text boxes, no tables, no content in headers or footers (some parsers skip them), a standard font.

REPORT
Say which connection you chose for the opening and where you found it, which proof points you used, and whether you added a gap sentence. Flag anything you could not ground in my CV.
```

## 4. Why it's written this way

- **Not purely data-based.** Early letters walked through courses and skills one by one ("in course X I learned Y, in course Z I did W"). They were accurate but read like a transcript: they showed what the applicant had covered, not why they wanted this job or who they are. A motivation letter's job is the second part. The rule is therefore narrative over enumeration, with at most one or two proof points.
- **A researched, specific opening.** Generic openings and generic praise are interchangeable between companies and get skimmed. One true, specific connection shows the letter was written for this employer.
- **The hook must already be in the CV.** A personal angle is only convincing if it holds up in the interview. Anything invented for the letter fails there.
- **Simple language.** Dense, formal phrasing with abstract nouns sounded more like a template than like the applicant, and it was harder to edit by hand. Short sentences in everyday words read as a person and stay easy to adjust.
- **Fewer, better details.** A letter packed with every keyword from the posting reads as generated. Two or three concrete points, given room, read as genuine.
- **One honest gap sentence.** Pretending to have every skill is not credible; naming one gap and the wish to close it is, and it is the right place for enthusiasm.
- **A loose structure instead of a fixed schema.** A rigid four-part schema (interest, what I learned, broader interest, availability) produced letters that all sounded alike and leaned on course content. The looser opening/middle/closing structure keeps the order predictable without forcing the content.
- **Availability only in the closing.** Unrequested remarks about remote work or attached documents raise questions the posting didn't ask. Ambiguous date wording once made a start date readable as an end date.
- **Editable .docx, one page.** The applicant edits every letter before sending, so it must be a Word file, not a PDF. One page keeps it readable.
- **Plain paragraphs.** Text boxes, tables and header/footer content are often skipped or scrambled by applicant-tracking systems.
- **No claimed specialization.** Declaring a focus you haven't stated in your CV overclaims and can be factually wrong; interests are honest.
- **Full term first, then the abbreviation.** The first reader may not be technical; the full term once, with the short form in brackets, keeps the letter clear without making it long.
- **Only completed work as proof.** A planned course or project can't be backed up in an interview yet.
