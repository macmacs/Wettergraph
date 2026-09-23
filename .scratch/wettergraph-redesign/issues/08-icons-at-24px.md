# Do the webp-backed icons hold at 24 px?

Type: prototype
Status: open
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
