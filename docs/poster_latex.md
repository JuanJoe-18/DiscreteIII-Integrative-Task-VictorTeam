# Research poster in LaTeX

The editable source is `resumelens-poster.tex`. Its exported PDF is
`../output/pdf/resumelens-poster-latex.pdf`. The previous poster remains available
as `../output/pdf/research_poster.pdf`.

## Format and reproduction

- A1 landscape (841 × 594 mm), one page, in English.
- Latin Modern text, mathematical and sans-serif heading fonts.
- Native TikZ vector diagrams; no external image or bibliography files required.
- Dependencies: a LaTeX distribution with `lmodern`, `geometry`, `amsmath`,
  `amssymb`, `xcolor`, `tikz` and `tabularx` (MiKTeX or TeX Live).

From the repository root:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -jobname=resumelens-poster-latex -output-directory=output/pdf docs/resumelens-poster.tex
```

Use the explicit job name to preserve the original PDF. The source can also be
opened in the Codex LaTeX editor or uploaded as a standalone file to Overleaf.

## Evidence and review

The test result (883 passing) was rerun on 11 October 2026, based on commit
`29f3c82`. Update it if the implementation changes. The poster summarizes the
implemented pipeline and draws references from `literature_review.md`; it does
not claim measured extraction accuracy or recruitment performance.

The Machine Learning diagram is one accepted trace with shortened state names,
not the complete DFA. The DSL illustration is abbreviated and explicitly
marked as such. Complete diagrams and validated examples remain in `docs/`.

The author line uses the existing team name. Confirm any required full author
names and institutional details before submitting or printing. Print at actual
size to preserve the intended font sizes.
