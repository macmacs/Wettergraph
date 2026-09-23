# Rewrite the graph visual specification

Type: grilling
Status: open
Blocked by: 00, 01, 02

## Question

Rewrite `.scratch/wettergraph-ha-widget/assets/graph-spec.md` so it specifies the cloned layout instead of the current one, clause by clause, with the same "every length at design width, scaled by k" discipline.

## Done when

- Every §-clause that the redesign invalidates is rewritten, not patched: canvas and aspect (§1), palette for both themes (§2), layout bands (§3), the 60 h window and its hour/day labels (§4), the temperature axis and gradient curve (§5), 24 px icons every 2 h (§6), rain bars on the fixed 0..10 mm axis including the over-max case (§7), states (§8), not-shown (§9), defaults (§10).
- New clauses exist for what the current spec has no words for: the cell grid, the day separators, the two-sided axis labelling, the legend row, the bar width/gap rule.
- Each geometric clause cites the reference from ticket 01, so no number is invented.
- `§9 Not shown` is updated: `kein Niederschlag` moves out of the spec, wind and attribution stay out.
- The spec is still readable as a contract a render check can diff against clause by clause.

## Constraints

- The charting decisions on the map are settled input, not open questions: fixed 60 h window, 12.2373 px/h columns, fixed 0..10 mm rain axis, both themes, German numeric labels, icons every 2 h, age chip kept, `kein Niederschlag` dropped.
- Keep the clause numbering stable where a clause survives unchanged; renumbering costs every citation elsewhere.

## Answer must record

The rewritten spec's path, and a list of which clauses changed, which are new, and which were deleted.

## Answer
