# Prompt template: CV tailoring

## 1. What this prompt does

It turns your complete master CV into a CV for one specific job posting: it picks the content that earns a place for this job, cuts to a hard page limit, and applies layout and wording rules that keep the result readable for applicant-tracking systems and for a recruiter skimming it in a few seconds. It never adds anything that isn't in your CV.

## 2. What you need to fill in

- $\color{orange}{\texttt{\{\{YOUR\_CV\}\}}}$: your complete master CV, uncut (LaTeX source, Word text or plain text). Example: `the attached master_cv.tex`
- $\color{orange}{\texttt{\{\{JOB\_POSTING\}\}}}$: the full text of the posting. Example: the pasted job ad for *Working Student Data Analytics*
- $\color{orange}{\texttt{\{\{COMPANY\_NAME\}\}}}$: the employer's name. Example: `Contoso GmbH`
- $\color{orange}{\texttt{\{\{JOB\_TITLE\}\}}}$: the job title as written in the posting. Example: `Working Student Data Analytics (m/f/d)`
- $\color{orange}{\texttt{\{\{OUTPUT\_LANGUAGE\}\}}}$: the language the CV should be written in, your choice (usually the language of the posting). Example: `German`
- $\color{orange}{\texttt{\{\{MAX\_PAGES\}\}}}$: the hard page limit for the tailored CV. Example: `2`
- $\color{orange}{\texttt{\{\{CERTIFICATE\_SOURCES\}\}}}$: where the real certificate documents are, so details can be taken from them. Example: `the three attached certificate PDFs` or `none`
- $\color{orange}{\texttt{\{\{OUTPUT\_FORMAT\}\}}}$: the format you want back. Example: `LaTeX, same preamble as my master CV`

## 3. The prompt

```text
Tailor my CV for the position {{JOB_TITLE}} at {{COMPANY_NAME}}. Write it in {{OUTPUT_LANGUAGE}} and return it as {{OUTPUT_FORMAT}}.

INPUTS
- My complete master CV (source of truth, never shortened for length): {{YOUR_CV}}
- The job posting: {{JOB_POSTING}}
- Certificate documents: {{CERTIFICATE_SOURCES}}

TRUTHFULNESS
- Everything must come from my master CV. Never invent skills, experience, grades, dates or certificate content.
- Never claim a specialization, focus or qualification that I haven't stated in my CV. Describe interests as interests ("I am especially interested in ..."), not as a declared focus or specialization.

CONTENT
- Actually tailor it; don't just reword the introduction. Decide per posting which projects, skills and certificates earn a place for this job. Cut the least relevant items first.
- Hard limit: {{MAX_PAGES}} pages for the tailored CV. A tailored CV as long as the master is a failure, not a pass. If you can compile, check the real page count and cut again until it fits.
- Keep one authentic detail that has nothing to do with the job's core requirements (an interest, a language, a side project), so the CV doesn't read like a template.

INTRODUCTION PARAGRAPH
- Several short, plain sentences, in this order: (1) who I am and my current status, (2) the experience that is relevant for this posting, (3) interests or soft skills, (4) languages, as their own closing sentence.
- Write it like a recruiter's summary, not a transcript: state capabilities directly, no references to course names, modules or labs.
- No sentences with an implied third-person subject; use short statements or noun phrases.
- No parentheses in the introduction.
- No "with a focus on X" framing.

SECTIONS AND FORMATTING
- Certificates and skills are two separate sections. Certificates: formal credentials only. Skills: everything else, without issuer or date details.
- Every certificate entry uses the same heading format as the education entries (bold title with right-aligned date, then an italic subtitle line), even for a single credential.
- Certificate details must come from the actual certificate document. Pick 2-4 relevant points it lists and write them as short noun phrases. If there is no document for a certificate, list its name only.
- Don't mark completed certificates as "completed" or "certified": listing them implies that. Only mark what is still in progress.
- Sub-items use "Name: description" with the name in bold.
- In every bullet, bold the concrete technology, tool or deliverable (not whole clauses), so the page can be scanned in a few seconds.
- Skills as a two-column grid of categories. If the number of categories is odd, merge two small related ones so no row is left with a single column.
- Don't repeat the identical skill phrase in the skills section and in a project bullet: project bullets describe what was built and the outcome.
- Abbreviations: the first time, write the full term with the abbreviation in brackets, for example "Test-Driven Development (TDD)"; after that, use only the abbreviation. In the introduction, which has no parentheses, write the full term only.
- Dashes only in date ranges. Never use a dash as a sentence connector or to introduce an explanation: use a colon, a comma or a new sentence.
- No salesy or flattering phrasing.

LAYOUT (if the CV is LaTeX)
- Wrap every entry (heading plus its bullet list) in a block that can't split across pages:
  \newenvironment{cvblock}{\noindent\begin{minipage}{\linewidth}}{\end{minipage}}
  The \noindent is required: without it, every block except the one right after a section heading gets a small paragraph indent, which misaligns its title and the right-aligned date.
- Margins 1.5 cm. Load ragged2e. Set \hyphenpenalty=10000 and \exhyphenpenalty=10000 so long words move to the next line whole. Redefine itemize with \RaggedRight so the missing hyphenation doesn't create stretched gaps.

CHECKS AFTER COMPILING (if you can compile)
- Page count: at most {{MAX_PAGES}}.
- Extract the text (for example pdftotext -layout) and confirm it reads in a sensible order, including the two-column skills block. If a column block comes out garbled, make it single-column.
- Look at each rendered page: no entry split across a page break, no single-column orphan row, all dates aligned.

REPORT
List what you included and what you cut, and why. Flag as an error: more than {{MAX_PAGES}} pages, mixed certificate/skill sections, an entry split across pages, anything you could not verify against my master CV.
```

## 4. Why it's written this way

- **The master CV stays complete; only the tailored copy is cut.** Tailoring from an already-shortened master loses exactly the details a specific posting might need. The master is raw material, not a draft.
- **Real content selection plus a hard page limit.** A version that only reworded the introduction produced four-page "tailored" CVs that were the master with a new first paragraph. Making selection a judgment call per posting, and checking the real page count, fixed that.
- **Short, plain introduction sentences.** Long sentences stacked with qualifiers, "with a focus on" framings and course references read as generated and as a transcript. Short factual sentences in a fixed order read like a person and give a recruiter the answer immediately.
- **No claimed specialization.** A focus that changes from posting to posting is visibly invented, and it can be false (for example before you have chosen any specialization). Interests are honest and still show direction.
- **Certificates come from the document.** Invented or embellished certificate details are easy to check and costly when wrong; the literal points on the certificate are safe and specific.
- **No "completed" labels.** Listing a certificate already says it's done; only the exception (in progress) carries information.
- **Separate sections, same heading format.** Mixed certificate/skill sections and bullet-style certificate lines read as disconnected fragments. One consistent heading format is faster to scan.
- **Bold nouns, no duplicated phrases.** A recruiter skims for technologies; bold concrete nouns make that possible, and repeated phrases waste space.
- **Full term first, then the abbreviation.** A bare abbreviation can lose a non-technical first reader, and an applicant-tracking system may search for either form. Writing the full term once with the abbreviation in brackets covers both, and the short form keeps the rest of the page compact.
- **No dashes as connectors.** Explanatory dashes and em-dashes in running text are a common marker of machine-written prose. Colons and short sentences avoid it.
- **The `cvblock` + `\noindent` rule.** A heading once landed on one page with its bullets on the next. The atomic block fixed that, and then introduced a small indent on every block after the first in a section, which only became visible when the rendered PDF was measured. Both parts belong in the template.
- **No hyphenation plus ragged-right lists.** Hyphenated words in narrow columns are hard to read and hard for parsers; turning hyphenation off without ragged-right lists creates wide gaps.
- **Text-extraction check.** Applicant-tracking systems read the text layer. Two-column layouts usually extract well, but not always, so each PDF is checked.
- **One wildcard line.** A fully optimized CV looks like every other optimized CV; one genuine unrelated detail makes it memorable.
