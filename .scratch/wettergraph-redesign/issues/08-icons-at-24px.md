# Do the webp-backed icons hold at 24 px?

Type: prototype
Status: resolved
Blocked by: 05

## Question

The icon set is 83 codes: 7 vector, lifted straight from yr's meteogram, and 76 wrapping the app's raster art, drawn so far at 28 px and now at 24 (spec §6.2, a ceiling the 2 h step fixes). Do the raster-backed ones still read at 24 px on a real render, and if any do not, what replaces them - a redrawn code, a vector substitute, or nothing?

Graduated from the map's fog by [ticket 05](05-redraw-renderer.md): the question was unanswerable until a render at the new size existed. It does now - `../assets/render-sample-{light,dark}.png` - and the reference sidestepped it by using yr's own art throughout, so nothing has actually judged our 76.

## Done when

- A contact sheet exists showing every code at 24 px, in both themes, over the real background colour - not on white, and not at 92 px where everything reads.
- The operator names the codes that fail, or confirms none do.
- If any fail: the fix is decided (and its cost stated), not performed. This ticket is a decision, not a redraw.

## Constraints

- `tools/extract-icons.py` already builds a contact sheet at 92 px and 28 px; extend it rather than writing a second sheet, and keep its 28 px column so the two sizes can be compared side by side.
- The icon set itself is the previous map's ticket 03 and is otherwise out of scope: this ticket judges legibility at a size, it does not reopen the extraction.
- Night art carries night (§9.3): a code that reads badly only because it is dark art on a dark ground is still a failure here.

## Answer must record

The sheet's path, the operator's verdict per failing code, and the decided fix for each.

## Answer

**All 83 hold at 24 px; no code fails, no fix.** Sheet: `.scratch/wettergraph-ha-widget/assets/icon-contact-sheet.png` (1432 x 1692), built by `tools/extract-icons.py`, which kept its 92 px and 28 px columns and gained two 24 px patches per code: a 4 x 3 cell cut of the light (`#ffffff` / grid `#c3d0d8`) and dark (`#020a14` / grid `#374759`) plot, the icon centred on an hour line so its left edge lands off the pixel grid as in a real render (`odd hour x 12.2373 - 12`). 1x pixels, no DPR boost - the harshest case.

Operator verdict, viewed at 100 %: **"moon is a bit dark on dark, rest ok."** The grey moon (`#686E73`) on `#020a14` reads, just dimly - judged a pass, not a failure. Weighed and declined:

- a dark-only light halo behind every icon (one SVG filter, works on the webp art too, but a §6.5 amendment and a risk of every icon looking glowy);
- yr's dark moon tint `#E1C578` on night codes (trivial on the 2 vector ones, but the ~26 webp night codes would need a second raster set, and it reverses §9.3).

So §6.2, §6.5 and §9.3 stand as written. If the dim moon grates after living with it, the halo filter is the cheap way back in.
