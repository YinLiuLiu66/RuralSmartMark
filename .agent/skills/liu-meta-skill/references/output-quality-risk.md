# Output Quality Risk

Read this when the generated skill produces tutorials, reports, Markdown pages, screenshots, tables, code snippets, or research summaries that people will read.

## Principle

A skill that routes and executes is not finished. It also has to predict the small, visible ways its final output will fail, and stop those failures before the user sees them.

## Common Failure Modes

- generic headings that make a tutorial look like a template
- dense footnotes or citation markers that interrupt reading
- tables that render badly, or hide decisions inside long cells
- screenshots that show the wrong state, are cropped wrongly, or miss a resource
- polished summaries that lose the user's real audience or scenario
- commands or snippets that omit working directory, inputs, outputs, or side effects

## Required Author Behavior

Before finalizing a generated skill:

1. infer the most likely output family from the job and target output
2. write that family's most likely mistakes as guardrails, directly into the generated skill's `SKILL.md` or `references/`
3. for reports, tutorials, screenshots, and visualizations, also state what counts as acceptable and what counts as fabrication
4. put unresolved output risks into "candidate next steps"; do not pretend the first version is complete

This local edition does not generate a separate risk report file; guardrails live in the skill itself.

## Self-Repair Rule

Every output-facing skill should do a final pass:

- specificity: do titles and summaries fit the real domain
- readability: are Markdown, tables, and lists easy to scan
- evidence hygiene: do citations support real conclusions without piling up
- visual truth: are screenshots and images real, relevant, and described correctly
- execution clarity: do commands and snippets state their assumptions and expected results
