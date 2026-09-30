# file-document-photo-video-organizer

## Summary

The repository is a small, standard-library Python prototype for organizing photo
records and assembling product listings. All runtime logic lives in
[`organizer.py`](organizer.py), with nine unit tests in
[`tests/test_organizer.py`](tests/test_organizer.py). Data stays in memory.

Despite the project name, there is currently no document or video processing,
directory scanning, file moving, database, command-line interface, or web UI.
The organizer uses paths, tags, and supplied metadata; it does not open images,
perform visual analysis, or estimate market prices.

## Features

| Existing capability | Behavior |
| --- | --- |
| Photo records | `Photo` stores an ID, path, tags, and arbitrary metadata. `inject_photostream()` appends supplied records. |
| Product classification | A parseable price, matching tag, or matching filename token identifies a product photo. Default keywords are `product`, `catalog`, `listing`, and `item`; callers can supply custom keywords. Matching is case-insensitive. |
| Listing fields | `analyze_photos()` returns results keyed by photo ID. Titles use supplied metadata or the filename stem and are title-cased; descriptions use supplied metadata or a category-based template. Prices come from numeric values or numeric strings, including zero. Other metadata becomes attributes. |
| Photo grouping | `group_alike_photos()` groups by explicit `group`, then `product_id`, then a lowercase filename stem with trailing sequence suffixes such as `_01` or `-12` removed. This is identifier-based grouping, not visual similarity. |
| Shared characteristics | Groups retain metadata keys whose values are equal across all member photos. |
| Nested product collections | `PhotoGroup` can hold child groups. `create_product_groups()` builds a collection with one child per product ID, including only product photos and groups within inclusive image-count bounds (default 1–10). Callers can request 4–10 photos per watch. |
| Product listings | `create_product_listings()` produces one listing per eligible product group, using its first photo's title, description, and price, plus shared metadata and all member image IDs. |

The existing tests cover listing fields, zero and invalid prices, shared metadata,
nested collections, filename suffix handling, custom keywords, and grouped listings.

## Proposed changes

These are recommendations for future implementation, in priority order.

1. **Validate inputs and make exclusions visible.** Define a duplicate-ID policy:
   analysis currently overwrites repeated IDs while grouping retains their records.
   Validate image-count bounds and report groups excluded by those bounds. Reject
   boolean, negative, and non-finite prices while preserving valid zero prices;
   add tests for these cases and non-product photos. Allow an explicit empty keyword
   set, which currently falls back to defaults.
2. **Make listing generation consistent across a group.** Define how conflicting
   titles, descriptions, and prices should be resolved instead of silently using
   the first image. Preserve intentional brand capitalization. Reuse one analysis
   result per listing-generation call; it currently analyzes photos twice through
   `create_product_groups()`. Test conflicting and missing metadata.
3. **Add a usable local workflow.** Build a CLI around the existing `Organizer`
   methods to load photo records from a JSON manifest and export analyses, groups,
   and listings as JSON. Include a sample manifest and round-trip tests. Keep the
   current explicit `product_id` and `group` metadata as grouping overrides.
4. **Add persistence and controlled file ingestion.** Start with saved manifests;
   introduce SQLite if search and larger collections require it. Add directory
   scanning and image metadata extraction with clear handling of unsupported or
   missing files. Any later file-moving workflow should offer a preview and an
   undo log.
5. **Extend media analysis after the local workflow is reliable.** Add optional
   image similarity or vision analysis through the existing analysis/grouping
   entry points, with confidence scores and manual overrides. Add document text
   extraction and video metadata through a shared media-record model if those
   workflows are required. Keep price assignment explicit until a pricing source
   and currency policy are defined.

## Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```
