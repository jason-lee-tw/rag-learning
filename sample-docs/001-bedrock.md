# Bedrock Knowledge Bases

Amazon Bedrock's managed RAG service — an OpenSearch-backed vector store plus an ingestion pipeline that parses, chunks, embeds, and indexes source files; most of its operational pain comes from which configuration changes force a destructive recreate.

## Key Concepts

- Knowledge base (KB) structure — a KB groups one or more **data sources** (typically S3 prefixes) and is bound to a single OpenSearch vector index and a single embedding model at creation time.
- Data source — the unit of ingestion; a KB can host multiple data sources (e.g. five "sources of truth") that index into the same underlying vector store.
- Ingestion pipeline stages — parse source files, chunk extracted text, embed chunks, index vectors in OpenSearch. Parsing and chunking configuration sit adjacent and share the same immutability constraint.
- Parsing model options — default text-only parser, Amazon Bedrock Data Automation (BDA), or a foundation model invoked as a parser. FM and BDA parsers are non-deterministic: identical inputs can yield different extracted text across runs, especially on tables, figures, captions, and OCR-adjacent work.
- `StartIngestionJob` semantics — normally incremental, reprocessing only files added, modified, or deleted since the last successful sync. Incrementality depends on the data source retaining prior state, so a freshly recreated data source always cold-starts.
- Cold-start cost — on a recreated data source, every file is re-parsed, every chunk re-embedded, and every vector re-indexed. Wall time routinely exceeds normal CI/CD deploy windows.
- `dataDeletionPolicy` (`DELETE` vs `RETAIN`) — controls whether OpenSearch entries are removed when a data source is deleted. `RETAIN` only preserves stale vectors produced by the old parser, which are worthless after a parser swap, so it cannot shortcut a cold start.
- `IngestKnowledgeBaseDocuments` (Direct Ingestion API) — pushes documents directly to the KB for immediate chunk+vectorize, bypassing the S3 scan phase used by `StartIngestionJob`. Caller owns the book-keeping for what has been ingested.
- Custom data source connector — decouples ingestion from Bedrock's built-in S3 crawler; documents are pushed rather than pulled, enabling application-level parallelism, batching, prioritization, and dual writes at the cost of owning the pipeline.

## Severity Hierarchy of Configuration Changes

Not every KB configuration change is equally destructive. Understanding the hierarchy determines whether a data source recreate, a KB recreate, or nothing at all is required.

- **In-place updates (safe)** — adding/removing/modifying source files, rotating IAM roles, updating Secrets Manager references, changing the KMS key, and toggling `dataDeletionPolicy` between `DELETE` and `RETAIN` can all be performed via `UpdateDataSource` without destroying state. Subsequent syncs remain incremental.
- **Data source recreate (medium-destructive)** — `chunkingConfiguration` is explicitly documented as immutable: _"You can't change the chunking configurations. You must re-create the data source."_ Practical experience indicates parser configuration follows the same constraint. Blast radius is limited to the vectors belonging to the recreated data source; other data sources in the same KB are unaffected.
- **KB recreate (most destructive)** — the embedding model is bound to the KB's vector index at creation time and cannot be changed in place. A new KB with the new embedding model must be created, vectors re-generated from scratch, and the application's KB ID changed. This affects every data source in the KB at once and forces an application-side configuration change, so blue-green KB becomes the only practical option.

Because chunking and parsing are both immutable and sit next to each other in the pipeline, an upgrade plan should treat them as a single upgrade surface — if a parser swap already forces a data source recreate, that is the opportune moment to revisit chunking, since the cold-start cost is already being paid.

## Parser-Swap Destruction Sequence

Changing the parser model on a data source triggers this sequence:

1. Bedrock destroys the data source resource.
2. OpenSearch entries belonging to that data source are removed (governed by `dataDeletionPolicy`; `RETAIN` is not useful here because the retained vectors are stale).
3. Bedrock creates a new data source with the new parser configuration.
4. First sync is a cold start — no prior ingestion state to diff against.
5. Every file is re-parsed by the new parser (slow and billed per page or per token for BDA and FM parsers).
6. Every chunk is re-embedded.
7. Every vector is re-indexed in OpenSearch.
8. Total wall time greatly exceeds the CI/CD deploy window; during the gap, RAG queries against affected sources return degraded or empty results.

The deploy window is the binding constraint. The work cannot run as an in-band step of a normal deployment — that is the problem teams are trying to solve.

## Non-Prod vs Prod Drift With Identical Models

Even with identical model IDs and prompts between environments, FM parsers (and to a lesser degree BDA) are non-deterministic. Each environment that re-ingests independently drifts in chunk boundaries and extracted text, which propagates into embedding differences and divergent retrieval results. Verifying an upgrade in non-prod does not guarantee identical behavior in prod. Mitigations include pinning a low temperature, versioning the parsing prompt, and hashing parsed output per source document so divergence is observable rather than silent.

## Chunking Strategies

Chunking configuration carries the same immutability constraint as parsing, so it is worth knowing the options when planning any upgrade.

- **Fixed-size chunking** — specify max tokens per chunk and overlap percentage. Simplest, cheapest, most predictable; weak on documents with strong structure.
- **Semantic chunking** — splits by semantic boundaries rather than token counts. Higher retrieval quality on prose, more expensive to ingest because it runs an embedding model during chunking.
- **Hierarchical chunking** — nested parent/child chunks. Retrieval fetches child chunks then swaps them for parents to give the generation model more context. Best for technical manuals, legal documents, and academic papers with nested structure.
- **Custom Lambda chunking** — a Lambda defines the logic, giving full control at the cost of owning the implementation. Also usable as a post-processing step after Bedrock's built-in chunking.

## Zero-Downtime Upgrade Patterns

The parser-upgrade problem is a specific instance of the broader zero-downtime vector-index migration problem. The community has converged on several patterns; each trades operational complexity for a different part of the pain.

### OpenSearch index aliases (Bedrock-specific workaround)

Decouple the Bedrock KB from the physical vector index via an Amazon OpenSearch Service alias:

1. Create a named alias (e.g. `kb_alias`) initially pointing at `bedrock_index_v1`.
2. Configure the KB to use the alias name rather than the raw index name.
3. For an upgrade, create `bedrock_index_v2` with new mappings/dimensions/shards/engine.
4. Populate `v2` via `_reindex` from `v1` (fast path, same vectors) or by re-ingesting from source (slow path, new vectors).
5. Validate with sample queries directly against `v2`.
6. Atomically flip the alias; Bedrock never sees the change from its side.
7. Rollback is an alias flip back to `v1`, effectively instant.

Caveat: aliases do **not** eliminate the cold-start re-parse cost for parser swaps (the parser runs before any vectors hit the index). What they do solve is the deploy-window problem — the long ingestion work happens into the shadow index on its own clock, and the cutover moment is a single fast alias flip. Until Bedrock natively supports aliases as a first-class KB configuration, this pattern requires managing the OpenSearch index lifecycle outside the Bedrock console/API surface.

### Blue-green knowledge base (default community answer)

Stand up `kb_green` with the new parser config and a fresh OpenSearch index, run `StartIngestionJob` out-of-band, validate with a golden-query suite, flip the application's KB ID config (secret, parameter store, or feature flag) from `kb_blue` to `kb_green`, keep `kb_blue` as a rollback target during a soak period, delete `kb_blue` once verified. This is the only feasible pattern when the **embedding model** needs to change, because embedding models are bound at KB creation. It is the higher-ceremony but lower-risk alternative to the alias pattern for parser swaps.

### Parallel data sources in one KB

Create new data sources with the new parser alongside existing ones inside the same KB, let both index, delete the old ones once retrieval quality is verified. Preserves the KB ID so the application requires no configuration change. Does not help with embedding-model changes.

### Shadow indexing and dual writes (general vector-DB pattern)

Borrowed from Elasticsearch zero-downtime reindexing practice:

- **Shadow indexing** — build the new index alongside the live one. Offline construction can use higher-cost settings (e.g. higher `efConstruction` for HNSW) because query latency is irrelevant during build.
- **Dual writes** — during long migrations, new documents write to both indexes so the shadow stays fresh. Increases write latency during migration but avoids a stale cutover.
- **Golden-query validation** — compare a curated suite against both indexes before flipping traffic. Regressions block the cutover.
- **Progressive cutover** — flip a small percentage of traffic to the shadow index, monitor, ramp.

Bedrock does not natively support dual writes — one data source writes to one vector store — so implementing this requires two KBs in parallel with application-level fan-out, or a custom ingestion pipeline.

### Direct Ingestion API (cold-start shortcut)

`IngestKnowledgeBaseDocuments` skips the S3 scan phase that `StartIngestionJob` needs before processing, and streams documents as they become available so retrieval starts returning useful results earlier in the cold start. Trade-off: caller owns the book-keeping for which documents have been ingested.

### Custom data source connector

Documents are pushed to the KB by caller code rather than pulled by Bedrock's S3 crawler. Enables full application-level control: parallelism, batching, prioritizing hot documents, incremental cutover, dual-write patterns. Heaviest option; the team owns the ingestion pipeline. Several teams end up here when deploy windows become unworkable.

### IaC lifecycle awareness (Terraform / CloudFormation)

Changing `parsingConfiguration` on an `aws_bedrockagent_data_source` forces resource **replacement** (destroy then create) — the IaC-level manifestation of the same destructive behavior. Practices that make this tractable:

- `lifecycle { create_before_destroy = true }` so the new data source is fully provisioned and ingesting before the old one is torn down. Requires unique names on every version.
- Split the data source into its own Terraform state or module so a replace does not ripple into unrelated resources.
- Ensure the execution role carries `aoss:DeleteIndex` on the OpenSearch Serverless collection — destroy fails without it.
- Add a `time_sleep` (~20 seconds) after IAM role creation before the KB is created, to work around IAM propagation eventual consistency.

The key realization: the deploy window problem cannot be solved by IaC alone — the IaC run will block on the same cold-start ingestion. IaC should **orchestrate** the cutover, not absorb the full rebuild inline. That typically means one IaC change that provisions the green resources, a separate out-of-band job that populates them, and a final small IaC change that flips the pointer.

## Mitigation Patterns Beyond Full Rebuilds

- **Pre-warm and cutover** — decouple recreate-and-ingest from the deploy itself. Trigger recreation and sync ahead of the deploy window via automation, monitor to completion, make the actual deploy a configuration flip only.
- **Narrow the re-ingest scope** — audit which data sources genuinely require the new parser (typically only those with tables, figures, or multimodal content) and leave the rest on the current parser. Reduces total cold-start time and cost.
- **Detect drift explicitly** — for FM parsers, pin a low temperature, version the parsing prompt, and hash parsed output per source document so non-prod/prod divergence is observable.
- **What does not help** — `dataDeletionPolicy=RETAIN` preserves vectors already invalidated by the parser change, so it cannot shortcut the cold start. Incremental sync cannot help a freshly recreated data source because there is no prior state to diff against.

## Pattern Comparison

| Pattern                         | Solves parser swap                      | Solves embedding-model swap | Bedrock-native                 | Ops complexity |
| ------------------------------- | --------------------------------------- | --------------------------- | ------------------------------ | -------------- |
| OpenSearch index aliases        | Partial — decouples cutover from ingest | Yes                         | No — external index management | Medium         |
| Blue-green KB                   | Yes                                     | Yes                         | Yes                            | Low            |
| Parallel data sources in one KB | Yes                                     | No — embedding bound to KB  | Yes                            | Low            |
| Shadow index + dual writes      | Yes                                     | Yes                         | No — manual                    | High           |
| Direct Ingestion API            | Shortens cold start                     | No                          | Yes                            | Medium         |
| Custom data source connector    | Yes, on your own pipeline               | Yes                         | Yes                            | High           |
| IaC `create_before_destroy`     | Makes IaC runs non-blocking             | Yes                         | Partial                        | Medium         |

## Community Consensus

Across AWS re:Post threads, dev.to posts, Medium write-ups, and AWS sample repos, three conclusions recur:

1. **The destructive-swap behavior is a constraint to design around at the architecture level, not a bug to work around at the resource level.** Teams that try to update in place eventually adopt one of the patterns above.
2. **Decouple the cutover from the ingestion.** The single most important architectural property is that the moment-of-switch is fast and reversible, regardless of whether the underlying rebuild takes minutes or hours.
3. **Always pair a cutover with a golden-query validation suite.** Parser non-determinism and embedding drift mean "the job finished successfully" is not the same as "retrieval still works." Teams that skip this have to roll back in production — which is what the patterns were meant to prevent.

## Sources

- AI Upgrade Related Issue (Bedrock KB parser-swap deploy-window pain) — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (internal chat + extended context compiled from AWS docs and community write-ups)
- Modify a data source for your Amazon Bedrock knowledge base — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS docs, https://docs.aws.amazon.com/bedrock/latest/userguide/kb-ds-update.html)
- Parsing options for your data source — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS docs, https://docs.aws.amazon.com/bedrock/latest/userguide/kb-advanced-parsing.html)
- Sync your data with your Amazon Bedrock knowledge base — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS docs, https://docs.aws.amazon.com/bedrock/latest/userguide/kb-data-source-sync-ingest.html)
- How content chunking works for knowledge bases — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS docs, https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking.html)
- Ingest changes directly into a knowledge base (Direct Ingestion API) — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS docs, https://docs.aws.amazon.com/bedrock/latest/userguide/kb-direct-ingestion.html)
- Connect your knowledge base to a custom data source — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS docs, https://docs.aws.amazon.com/bedrock/latest/userguide/custom-data-source-connector.html)
- How to Use Amazon OpenSearch Service Index Aliases with Knowledge Bases in Amazon Bedrock — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS Builders community, dev.to)
- Deploy Amazon Bedrock Knowledge Bases using Terraform for RAG-based generative AI applications — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (AWS ML blog)
- How To Manage an Amazon Bedrock Knowledge Base Using Terraform — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (Avangards blog)
- Vector Database Reindexing Pipeline — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (Medium, @kandaanusha)
- Zero Downtime Reindex in Elasticsearch — `digested-original/bedrock-knowledge-bases/ai-upgrade-related-issue.md` (tuleism.github.io, 2021)

## Related Topics
