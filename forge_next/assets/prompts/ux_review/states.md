# Phase 4: States & viewports

Capture screenshots of every page and important state, including empty, loading, success, validation, and error states. Where appropriate, review the experience at multiple screen sizes.

## Injected context

- **Base URL:** {{BASE_URL}}
- **Coverage:**
```
{{COVERAGE_JSON}}
```

## Your task

1. For major views in the plan’s state matrix, force:
   - empty, loading (when possible), populated, validation, error, success
2. At agreed viewports (default desktop; add ~768 and ~375 when the product is responsive / mobile-relevant):
   - **`--quick`:** desktop-only viewport, unless orientation flags the product as responsive/mobile — then still add ~768/~375.
   - Spot-check critical journeys for clipping, overlap, unusable targets, lost primary CTA
3. Update coverage `states` and `viewports` lists with evidence paths.
4. Note broken controls, dead ends, missing states, inconsistent patterns, and friction for step 5.

## Done when

- [ ] Important states attempted or skipped with reason
- [ ] Viewport spot-checks done per plan
- [ ] Coverage updated

**Next:** step 5 — structured findings.
