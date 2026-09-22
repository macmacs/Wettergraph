# Extract the yr weather icon set

Type: task
Status: resolved

## Question

Extract yr's weather icons (MET art) out of `assets/meteogram-6325496.svg` into standalone files under `assets/icons/`, one per `symbol_code` variant (`clearsky_day`, `partlycloudy_night`, ...), plus an index mapping every `symbol_code` to its file, and prove each icon renders.

## Outcome

83 standalone icon SVGs plus an index, every met.no `symbol_code` covered, art
proven by a render pass and by the operator's eye.

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

## Answer

**Icon directory.** `.scratch/wettergraph-ha-widget/assets/icons/` - 83 SVG files,
one per `symbol_code`, plus `index.json` mapping every code to its file.

**The code set is 83, not just today's weather.** MET's full list: 21 base names
with `_day` / `_night` / `_polartwilight` variants, plus 20 single names. The extra
"s" in `lightssleetshowersandthunder` / `lightssnowshowersandthunder` is MET's own
typo and is kept on purpose - it is what the API sends.

**Where each icon comes from.** 7 codes have vector art in the meteogram, mapped
through MET's legacy id table (weathericons `legend.csv`): `clearsky_day` (`01d`),
`clearsky_night` (`01n`), `fair_day` (`02d`), `partlycloudy_day` (`03d`),
`partlycloudy_night` (`03n`), `cloudy` (`04`), `lightrain` (`46` - id 46 is light
rain, not fog). The other 76 codes wrap the app's `weather_icon_*.webp` MET art as
a data URI inside an SVG. The two sources are the same art, checked side by side,
so the mixed set stays visually consistent. `lightssnowshowersandthunder_day` uses
the app file named `lightsnowshowersandthunder_day.webp`, where the two sources
disagree about the extra "s".

**File contract for the renderer.** Every file is an SVG with
`viewBox="0 0 100 100"`; the art hangs on `<g id="<symbol_code>">`. Vector defs ids
are renamed `<symbol_code>__<part>` (`partlycloudy_day__a`), so several icons can be
inlined into one graph SVG without id collisions.

**Contact sheet.** `.scratch/wettergraph-ha-widget/assets/icon-contact-sheet.png` -
all 83 icons at 92 px and at the 28 px the graph actually uses, with labels.

**Extraction command.**

    uv run --with resvg-py python tools/extract-icons.py --font /tmp/DejaVuSans.ttf

The font only feeds the sheet's labels; the icons need no font. This box has no
DejaVu, so that sheet used a copy fetched to `/tmp`; in the container the script
finds `/usr/share/fonts/dejavu/DejaVuSans.ttf` itself once `font-dejavu` is
installed. A re-run is deterministic: all 83 files, `index.json`, and the sheet
come out byte-identical.

**Checks inside the script.** Every icon is rendered at 100 px and its PNG is
decoded; a blank render aborts the run. The contact sheet then renders all 83 at
92 px and 28 px in one pass.

**Handoff to ticket 05.** `assets/icons/` sits under `.scratch/` and does not ship
in the app image: copy it under `wettergraph/app/` and read `index.json` as the
`symbol_code` -> file table. The Dockerfile also needs `font-dejavu`.

## Done when, checked

- [x] `assets/icons/` holds one SVG per needed variant, each with a stable id: 83
  files, art on `<g id="<symbol_code>">`.
- [x] An index maps the full set of met.no `symbol_code` values to files:
  `assets/icons/index.json`, 83 codes.
- [x] Every icon rendered once and looks right; `assets/icon-contact-sheet.png`
  shows them all - operator confirmed.
- [x] Extraction is a committed reproducible script: `tools/extract-icons.py`; a
  re-run is byte-identical.

## Verification (operator installs, then reports)

Operator eyeballs the contact sheet and confirms the icons match the current graph.

- [x] Confirmed 2026-09-22: the operator checked `assets/icon-contact-sheet.png`;
  the icons match the current graph.
