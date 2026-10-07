# The Brothers Karamazov

A complete, AI-generated English translation of Fyodor Dostoevsky’s novel, translated from the Russian with Astra as the literary lead and separate AI reviewers, including Sol. Includes all twelve books, the epilogue, and the author’s front matter.

## Download and read

The finished books are in **[exports/](exports/)**. Choose either edition:

- **[Download the annotated EPUB](https://github.com/dusty-g/karamazov-translation/raw/refs/heads/main/exports/The%20Brothers%20Karamazov.epub)** — 83 notes, mainly translations of foreign phrases and explanations of unfamiliar references.
- **[Download the no-notes EPUB](https://github.com/dusty-g/karamazov-translation/raw/refs/heads/main/exports/The%20Brothers%20Karamazov%20%E2%80%94%20No%20Notes.epub)** — the same complete novel without note markers or annotations. Foreign-language passages remain as in the annotated edition, but their note translations are omitted.

You can open either file in an EPUB reader. If you browse to a file on GitHub instead of using a download link, choose **Download raw file**.

### Send to Kindle

The easiest route is [Amazon’s Send to Kindle website](https://www.amazon.com/sendtokindle): sign in, upload the EPUB, and enable **Add to your library**. Amazon supports EPUB uploads and converts them for Kindle. See [Amazon’s Send to Kindle overview](https://www.amazon.com/gp/help/customer/display.html?nodeId=G5WYD9SAF7PGXRNA).

To send it by email:

1. Find your device’s **Send to Kindle email address** in Amazon’s **Manage Your Content and Devices → Preferences → Personal Document Settings**.
2. Add the address you will send from to your **Approved Personal Document Email List**.
3. Attach the downloaded EPUB to an email sent to your Send to Kindle address, then connect your Kindle to the internet and sync.

Amazon’s [email-to-Kindle instructions](https://www.amazon.com/gp/help/customer/display.html?nodeId=G7NECT4B4ZWHQ8WV) explain the delivery requirements. Your Kindle address is the destination; your ordinary email address is the approved sender.

## How the translation was made

The aim was readable modern English that preserves the novel’s voices, repetitions, uncertainty, and historical setting. The project began with a few pilot passages to test a workflow before scaling up to complete chapters. Those comparisons guided a practical choice of drafting and review roles; they were not a benchmark proving one model superior to another.

Production used Russian texts from [the Russian Virtual Library](https://rvb.ru/dostoevski/) and [iLibrary](https://www.ilibrary.ru/text/1199/index.html). These electronic witnesses were compared, with transcription differences resolved before a chapter’s source packet was frozen. They may share an editorial ancestry, so agreement between them was not treated as two wholly independent confirmations.

The recurring chapter workflow was:

1. **Fix the source and its boundaries.** Record the selected Russian text, a checksum, and stable paragraph IDs before drafting.
2. **Draft from the Russian.** Astra was the main literary drafting role. The production method was not to rewrite an existing modern English translation.
3. **Review accuracy separately.** A separate AI reviewer checked the draft against the Russian for omissions, additions, agency, negation, relationships, and ambiguous wording. Sol served in this role during much of production; configurations varied across the project.
4. **Edit the English, then check the changes back against Russian.** A smoother sentence was not automatically an improvement if it changed meaning or erased a speaker’s deliberate repetitions.
5. **Check structure and package the book.** Verify paragraph order, names and note references; later, compare the rendered EPUB with the reading masters.

Model names describe the requested roles and configurations. The records did not independently expose the actual serving model and effort for every run. A separate AI review is also not independent human review.

## Process lessons and decisions

**Source preparation was a real part of the work.** Early sampling exposed a missing continuation; later preparation had to handle printed-page breaks and misleading HTML boundaries. Giving each source unit a stable ID made completeness something that could be checked rather than inferred from fluent prose. The completed manuscript carries 4,990 ordered source-unit markers across 96 chapters and the front matter.

**Accuracy and readability needed different passes.** Reviewing only for fidelity left some English overly tied to Russian syntax. Reviewing only for fluency could hide a change in meaning. The workflow therefore separated those questions and checked revised clauses against the source again.

**More parallel drafts were not always useful.** After the pilots, the default became one draft, one separate source review, and editorial integration. Extra opinions were reserved for specific unresolved problems. This was a workflow choice, not a measured claim about cost or model performance.

**Formatting could lose information even when the words survived.** A late check found 43 verse line breaks that needed explicit Markdown hard breaks. The correction was verified through the parser as well as the text. Export checks also compare emphasis, bold, blockquotes, and line breaks.

**Annotation needed editing too.** The first complete export had 105 notes, with 20 crowded into the opening three chapters. Reader feedback led to cutting redundant explanations and translator disclaimers: those chapters now have six notes, and a second pass brought the whole book to 83. The no-notes edition is generated from the same masters, so the two versions do not require separate narrative edits.

**Export conversion needed its own checks.** Creating the no-notes variant initially changed a quotation mark during a Markdown round trip. Comparing the exported text against the masters caught it; disabling that punctuation transformation fixed it. Notes are removed structurally, including references in chapter headings, rather than by deleting arbitrary text from the EPUB.

## What has been checked—and what has not

Both EPUBs are checked against all 96 chapter masters for rendered text and basic formatting. Their contents navigation, internal links, cover, credits, and ordered source markers are checked too. The release EPUBs pass EPUBCheck 5.4.0 without errors or warnings.

The production archive also records bounded late reviews of accuracy samples, quantities and relationships, and embedded material. Those checks found and corrected specific issues; they do not establish an error rate or certify the entire translation. This remains an AI-generated translation with AI review and revision. **It has not received independent review by a human Russian-language specialist.** EPUB validation does not guarantee identical behavior on every Kindle or after Amazon conversion.

## Files and rebuilding

- `exports/` — the two ready-to-read EPUBs.
- `reading/` — the current Markdown reading masters; edit these to change the book.
- `book-manifest.json` — reading order and expected source-unit IDs.
- `artwork/` — the AI-generated cover used in both editions.
- `scripts/` — the EPUB builder, styles, note-removal filter, and comparison checks.

To rebuild, install Python 3 and Pandoc, then run from this repository:

```sh
python3 scripts/build_complete_edition.py
python3 scripts/build_complete_edition.py --no-notes
python3 scripts/check_complete_epub.py
python3 scripts/check_complete_epub.py --no-notes
```

Intermediate Markdown goes into the ignored `build/` directory. The scripts need no API key or model access. They rebuild the EPUBs from the existing English masters; they do not rerun the translation or its Russian-source audits. The public repository contains the reading edition and its packaging tools; raw website downloads, preliminary drafts, private correspondence, and internal review logs are not included.

For an additional package check, run [EPUBCheck](https://www.w3.org/publishing/epubcheck/) against each file in `exports/`.
