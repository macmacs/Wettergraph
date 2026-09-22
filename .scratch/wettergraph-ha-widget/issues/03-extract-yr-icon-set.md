# Extract the yr weather icon set

Type: task
Status: claimed

## Question

Extract yr's weather icons (MET art) out of `assets/meteogram-6325496.svg` into standalone files under `assets/icons/`, one per `symbol_code` variant (`clearsky_day`, `partlycloudy_night`, ...), plus an index mapping every `symbol_code` to its file, and prove each icon renders.

## Done when

- `assets/icons/` holds one SVG per needed variant, each with a stable id.
- An index maps the full set of met.no `symbol_code` values the graph can receive to files - not just today's weather.
- Every icon has been rendered once and looks right; a contact-sheet PNG in `assets/` shows them all.
- Extraction is a committed reproducible script (`tools/extract-icons.*`), not hand work.

## Refs

- `assets/graph-spec.md` §6: the graph draws one icon every 3 h, in a 28 x 28 box
  at W=782, scaled with the render width. The extracted art has to hold up at
  28 px, so a variant drawn for 80 px needs checking small.

## Note

yr's icons sit in `<g>` elements with `<defs>` ids keyed by MET symbol (`01d__01d__a`, `03n__03n__*`, `04__04__*`, ...). Map those ids to `symbol_code` values. The 88 webp equivalents in `app/src/main/res/drawable/` serve as a naming cross-check and a fallback source.

## Answer must record

Icon directory, the `symbol_code` -> file mapping, variant count, contact-sheet path, and the extraction command.

## Verification (operator installs, then reports)

Operator eyeballs the contact sheet and confirms the icons match the current graph.
