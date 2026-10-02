# Local human review exports

Generated human review packages are stored in `local/`, which is ignored by Git. They contain short source excerpts and references to raw snapshots that are also ignored by Git. This keeps material marked CC BY-NC-ND and material with unknown reuse terms out of repository distribution.

The repository tracks only the package index and hashes at `data/human_review_package_index.json`. A reviewer must receive the local export and exact source snapshots through an authorized channel, verify each snapshot hash, and make an explicit qualified human decision. `READY_FOR_HUMAN_REVIEW` is not approval. No source-derived record may be published while its license gate is blocked.

To inspect locally, open the Markdown file matching a candidate ID in `local/`. The JSON package carries the full snapshot manifest, candidate hash, snapshot-bound locator, short evidence string, reviewer questions and blank human decision.
