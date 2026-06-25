# Pitfalls Research

**Domain:** Geospatial hydraulic infrastructure management system (web portal, PWA, AI copilot, trilingual RU/KK/EN, Kazakhstan)
**Researched:** 2026-06-25
**Confidence:** HIGH (verified against official docs, EPSG registry, GitHub issues, and production post-mortems)

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Kazakhstan Coordinate System Transition (QazTRF-23 vs Pulkovo 1942)

**What goes wrong:**
Kazakhstan officially replaced the Pulkovo 1942 coordinate system (EPSG:4284) with QazTRF-23 (EPSG:10941) on 2025-01-01. Legacy registry data, cadastral documents, and scanned passports use Pulkovo 1942 / CS63 zones (e.g., EPSG:2939 for Zhambyl). If the system stores or transforms coordinates without accounting for this transition, structures appear tens to hundreds of meters from their real positions on the map. The transformation between Pulkovo 1942 and QazTRF-23 requires an NTv2 grid shift file (`qazgrid_kz.gsb`), not a simple 7-parameter transform. The `proj4` field for EPSG:10941 returns `null` on some registries, indicating PROJ library support may be incomplete in older versions.

**Why it happens:**
- The EPSG dataset only added QazTRF-23 in July 2025 (v12.056, Change ID 2025.066). PROJ/GDAL versions released before late 2025 do not know about EPSG:10941 or the Gauss-Kruger zones EPSG:10942 through 10949.
- The transformation requires a grid file (`qazgrid_kz.gsb`) that must be installed in PROJ's data directory. It is not bundled by default.
- Developers assume `ST_Transform(geom, 4326)` works universally, but Pulkovo 1942 to WGS 84 uses different (less accurate) parameters than Pulkovo 1942 to QazTRF-23 to WGS 84.
- Government data may arrive in either system with no metadata indicating which CRS was used.

**How to avoid:**
- Standardize on EPSG:4326 (WGS 84) as the storage and display CRS in PostGIS. Transform all incoming data to 4326 at ingestion time.
- Install the `qazgrid_kz.gsb` NTv2 grid file in the PROJ data directory. Verify with `projinfo -o PROJ EPSG:10941`.
- Pin PROJ >= 9.4 and GDAL >= 3.8 in Docker images. Verify QazTRF-23 support with `gdaltransform -s_srs EPSG:4284 -t_srs EPSG:10941` before processing any data.
- Store the source CRS alongside every geometry in a `source_srid` column for auditability.
- Document the transformation chain: source CRS to QazTRF-23 (if from Pulkovo) to WGS 84. Never transform Pulkovo directly to WGS 84 if QazTRF-23 grid is available (accuracy: 0.1m via grid vs 2-5m via 7-parameter).

**Warning signs:**
- Structures appear offset from visible canal/river features on satellite imagery by 50-200m.
- `projinfo EPSG:10941` returns an error or "unknown CRS."
- `ST_Transform` silently produces coordinates in the wrong location without error (fallback to towgs84 parameters).
- Cadastral numbers do not match known locations when plotted.

**Phase to address:**
Data Ingestion phase. The very first phase that handles coordinate data. Must be solved before any map display or spatial matching.

---

### Pitfall 2: PostGIS Geometry/Geography Type Mixing Causing Silent Index Bypass

**What goes wrong:**
Queries that cast between `geometry` and `geography` types at runtime bypass GiST spatial indexes entirely, triggering sequential scans across all rows. A query like `WHERE ST_DWithin(geom::geography, point, 100)` looks correct but forces PostgreSQL to cast every row to geography before evaluation, ignoring the GiST index on the `geometry` column. The same query that returns in 10ms with proper indexing takes 2+ seconds with millions of rows. This is the single most common PostGIS performance anti-pattern in production.

**Why it happens:**
- `ST_DWithin` behaves differently for geometry (units = CRS units, e.g., degrees for 4326) vs geography (units = meters). Developers cast to geography to get meter-based distance, not realizing it breaks indexing.
- The `ST_Distance` function in a WHERE clause is a measurement function, not a filter. It computes exact distance for every row. `ST_DWithin` is the index-aware filter.
- Functions like `ST_Transform` on indexed columns in WHERE clauses also prevent index use.

**How to avoid:**
- Store all geometries as `geometry(POINT, 4326)` with explicit SRID. If you need meter-based distance queries, add a separate `geography` column with its own GiST index using a GENERATED ALWAYS column.
- Use `ST_DWithin` for filtering, `ST_Distance` for measurement. Never put `ST_Distance` in a WHERE clause.
- Transform search parameters, not indexed columns: `WHERE geom && ST_Transform(search_box, 4326)` not `WHERE ST_Transform(geom, 3857) && search_box`.
- Run `EXPLAIN ANALYZE` on every spatial query during development. Look for "Seq Scan" on a spatial column with a GiST index.

**Warning signs:**
- Map pan/zoom feels sluggish when it should be instant.
- API response times scale linearly with table size.
- `EXPLAIN ANALYZE` shows "Seq Scan" on geometry columns despite GiST index existing.
- Database CPU spikes during map interactions.

**Phase to address:**
Backend API phase. When building spatial query endpoints. Establish the geometry/geography schema pattern before any spatial API goes to production.

---

### Pitfall 3: Vector Tile Generation Bloat (ST_AsMVT + SELECT *)

**What goes wrong:**
Using `SELECT *` or including too many properties in `ST_AsMVT` queries generates tiles 50-100x larger than recommended (over 500KB), causes OOM kills on PostgreSQL, and makes the map unusably slow. A tile with 42 properties per feature takes 9x longer to generate than one with 5 properties. Documented cases show 2.7GB memory usage for a single tile generation in PostGIS 3.0.

**Why it happens:**
- `ST_AsMVT` makes it trivially easy to dump all columns. The `*` pulls every column including large text fields, metadata, and geometry.
- Properties encoding dominates tile generation time as column count increases.
- `ST_Transform(geom, 3857)` inside the tile query reprojects every geometry at query time instead of using pre-projected data.
- Parallel query execution multiplies memory usage when tiles are large.

**How to avoid:**
- Explicitly select ONLY the properties needed for map display. Never use `*` in ST_AsMVT queries.
- Store a pre-projected geometry column in Web Mercator (EPSG:3857) for tile generation using a GENERATED ALWAYS column. Index this column separately.
- Set a tile size budget: monitor generated tile sizes. Reject or simplify tiles exceeding 500KB.
- Use TiPG's built-in property selection (it queries only specified columns via the `properties` query parameter).
- Use `ST_Simplify` or `ST_SimplifyPreserveTopology` on polygon/line geometry at low zoom levels.

**Warning signs:**
- Tile responses are slow (over 500ms for a single tile).
- PostgreSQL OOM killer terminates the database process during map use.
- Network tab shows tiles over 500KB in size.

**Phase to address:**
Map and Vector Tiles phase. When setting up TiPG and vector tile generation.

---

### Pitfall 4: Kazakh Cyrillic Extended Font Rendering

**What goes wrong:**
The Kazakh Cyrillic alphabet includes 9 characters beyond the basic Russian Cyrillic set (U+0460 to U+052F block). Standard font loading with only `latin` and `cyrillic` subsets produces broken rendering: these characters fall back to a system font, creating a visual "newspaper clipping" effect where Kazakh text looks like it is from a different typeface mixed into clean Inter text. This affects structure names, place names, and all Kazakh UI labels.

**Why it happens:**
- Most web font services split Cyrillic into `cyrillic` (U+0400 to U+04FF, covering Russian) and `cyrillic-ext` (U+0460 to U+052F, covering Kazakh). Developers load only `cyrillic` because Russian works fine.
- The `cyrillic-ext` subset is approximately 26KB additional. Small but easily forgotten.
- Additionally: Kazakhstan is transitioning Kazakh to a Latin script (target 2031, diacritic-based). The system may eventually need to support Kazakh in BOTH scripts.

**How to avoid:**
- Always load three font subsets: `latin`, `cyrillic`, and `cyrillic-ext`. With Fontsource: `@fontsource/inter/cyrillic-ext.css`.
- Test with actual Kazakh text containing all 9 special characters.
- Design the i18n system to support Kazakh in both Cyrillic and Latin scripts. Store a `script` field alongside `language`.

**Warning signs:**
- Kazakh text in the UI looks visually inconsistent (mixed typefaces).
- `font-family` inspection in DevTools shows fallback to system font for specific characters.
- Users report "broken text" but only for Kazakh, not Russian.

**Phase to address:**
Frontend Foundation phase. When setting up the design system and font loading.

---

### Pitfall 5: MinIO Presigned URL Signature Mismatch Behind Reverse Proxy

**What goes wrong:**
MinIO presigned URLs fail with `SignatureDoesNotMatch` errors when MinIO is behind a reverse proxy (Nginx, Caddy). The client signs the request against one hostname (e.g., `cdn.example.com`) but the proxy forwards it with a different Host header (e.g., `127.0.0.1:9000`). MinIO computes a different signature and rejects the request. This breaks document preview, image loading, and field photo upload workflows. The error message is cryptic and does not point to the Host header as the cause.

**Why it happens:**
- S3 signatures are computed over a canonical request that includes the Host header. If the proxy changes the Host header, the signature MinIO computes will not match.
- `MINIO_SERVER_URL` environment variable must be set to the public URL MinIO should sign against. If unset, MinIO uses the container hostname (e.g., `minio:9000`), which is unreachable from the browser.
- Docker internal networking uses container names (`minio:9000`) but browsers need the external URL. Presigned URLs generated with the internal hostname fail in the browser.
- Nginx `proxy_set_header Host $host` is required, not `Host $http_host` or `Host 127.0.0.1`.

**How to avoid:**
- Set `MINIO_SERVER_URL` to the public-facing URL (e.g., `https://cdn.example.org`) in the MinIO Docker container environment.
- Configure Nginx with `proxy_set_header Host $host` to forward the original Host header.
- Use `forcePathStyle: true` in all S3 clients. MinIO serves buckets at `/bucket-name/` paths, not as subdomains.
- Do not expose port 9000 directly to the public. Route all traffic through the proxy with TLS.
- For Docker-internal access (FastAPI to MinIO), use the container name. For browser-facing presigned URLs, use the public URL. The `MINIO_SERVER_URL` controls what hostname presigned URLs are generated with.

**Warning signs:**
- `SignatureDoesNotMatch` errors when accessing presigned URLs from the browser.
- Presigned URLs contain `minio:9000` as the hostname instead of the public URL.
- Direct access to MinIO works but proxy access fails.
- Large uploads fail at around 1MB or 10MB (Nginx `client_max_body_size` limit).

**Phase to address:**
Infrastructure phase. When setting up MinIO and the reverse proxy. Must be solved before any document or image serving works.

---

### Pitfall 6: LangGraph State Management Failures (Missing Reducers, Checkpointer Issues)

**What goes wrong:**
LangGraph workflows silently drop data between nodes, "forget" conversation history, or crash with `InvalidUpdateError` when parallel nodes update the same state key. Over 60% of production agent incidents trace back to state management failures. The most common manifestation: a node's output disappears by the time it reaches the next node, or multi-turn conversations "forget" previous exchanges. Without a checkpointer, every graph invocation starts from scratch, so human-in-the-loop review workflows lose state on server restart.

**Why it happens:**
- Every node returns a partial state update, not the full state. If two nodes write to the same key without a reducer, the last write wins silently. For list fields (like message history or evidence lists), this means data is lost.
- The default `Overwrite` behavior for state keys without `Annotated` reducers is almost never what you want for fields that multiple nodes update.
- Without a checkpointer wired at `.compile()` time, the graph has no memory between `.invoke()` calls. Forgetting `thread_id` in the config is the single most common LangGraph bug.
- Conditional edge return values must exactly match mapping keys. A return of `"END"` (string) vs `END` (sentinel) vs `"end"` (custom key) are three different routes, and LangGraph does not tell you which one mismatched.
- Writes to unknown state keys (not declared in the schema) are silently ignored and do not trigger downstream nodes.

**How to avoid:**
- Define explicit reducers for ALL list and dictionary fields using `Annotated[list, add_messages]` or custom reducer functions. The default last-write-wins is almost never correct for accumulation fields.
- Always wire a checkpointer at compile time: `graph.compile(checkpointer=PostgresSaver(...))`. Use PostgresSaver or RedisSaver in production, never MemorySaver.
- Always pass a consistent `thread_id` in the config for every invocation of the same conversation/workflow.
- Type conditional edge return values with `Literal[...]` to catch mismatches at static analysis time.
- Use `stream_mode="values"` streaming as your primary debugging tool to trace state through the graph node by node.
- Never mutate the incoming state dict directly. Return only the keys you own.

**Warning signs:**
- `messages` list only contains the last message, not the full history.
- A node's output disappears by the time it reaches the next node.
- Multi-turn conversations "forget" previous exchanges.
- `KeyError` or `None` when accessing state inside a node.
- `InvalidUpdateError` exception when parallel nodes execute.
- Graph "restarts" when you expected it to continue from an interrupt.

**Phase to address:**
AI Copilot phase. When building LangGraph workflows for evidence-grounded Q&A and human-in-the-loop review.

---

### Pitfall 7: PWA Offline Sync Data Loss (Last-Write-Wins Without Conflict Resolution)

**What goes wrong:**
Field inspectors work offline, capturing photos, voice notes, and condition updates. When they return online, the sync engine uses last-write-wins (LWW) at the document level. A field inspector's detailed condition update is silently overwritten because the server had a more recent timestamp from a minor metadata change. Alternatively, two inspectors edit different fields of the same structure offline, and one edit is lost. The system provides no conflict notification, no audit trail of discarded versions, and no recovery path.

**Why it happens:**
- LWW is the cheapest and simplest sync strategy, so it is the default in most PWA sync libraries. But timestamps are not truth. A later write does not automatically mean a better one.
- Client clocks lie. A device with a wrong system clock can "win" every conflict.
- Document-level LWW is especially destructive: if User A updates the condition assessment and User B updates the inspector name, LWW at the document level loses one of the changes even though they edited different fields.
- Without revision tracking, the system cannot detect stale writes. Without tombstones, deleted records crawl back from the dead during sync.

**How to avoid:**
- Design the conflict resolution model BEFORE designing anything else in the offline system. This is the core engineering challenge.
- Use field-level merge instead of document-level LWW. One inspector edited condition, another edited the name. Both survive. Conflicts shrink to the rare case of the same field changed twice.
- Track revisions on every record. When a client tries to update revision 12 and the server is on revision 14, the system knows there is a conflict instead of blindly accepting.
- Use Hybrid Logical Clocks (HLC) instead of wall-clock time. HLCs combine physical timestamp with a monotonic counter, surviving clock skew.
- For inspection records (high-stakes data), never auto-resolve. Queue for explicit human review. Surface the conflict: "This record was changed on another device. Keep yours, theirs, or merge?"
- Use UUIDs for record IDs, not auto-increment. Auto-increment does not work across devices.
- Implement an outbox pattern: all writes go to local IndexedDB first, then a sync queue drains to the server when online.
- Always log what was resolved automatically. An audit trail of discarded versions turns "the app ate my data" into a recoverable event.

**Warning signs:**
- Inspectors report missing field updates after syncing.
- Two devices show different data for the same structure after sync.
- Deleted records reappear after sync.
- No conflict notification UI exists in the design.
- Sync queue grows unbounded with no error handling.

**Phase to address:**
PWA Field Mode phase. The conflict resolution model must be designed before any offline capture code is written.

---

### Pitfall 8: Docker Compose Dependency Ordering (depends_on Does Not Mean Ready)

**What goes wrong:**
The FastAPI backend crashes on boot with a connection-refused error against PostgreSQL, even though `depends_on` lists the database. Milvus starts before etcd is ready and enters CrashLoopBackOff. TiPG cannot connect to PostGIS because the database has not finished running init scripts. The entire stack fails to start reliably, requiring manual restarts. This is the classic startup race in multi-service Docker Compose stacks.

**Why it happens:**
- `depends_on` only orders container creation and start. It returns as soon as the container process launches, not when the application inside is ready.
- A database daemon takes several seconds after container start to run init scripts, bind its socket, and accept connections.
- `condition: service_started` (the default) means "container is running," not "service is accepting connections."
- Healthchecks are often too shallow (checking TCP port open instead of a real query).

**How to avoid:**
- Add meaningful healthchecks to every stateful dependency:
  - PostgreSQL: `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`
  - Redis: `redis-cli ping`
  - MinIO: `mc ready local`
  - Milvus: check the proxy health endpoint
- Gate dependents with `condition: service_healthy`:
  ```yaml
  depends_on:
    db:
      condition: service_healthy
    migrate:
      condition: service_completed_successfully
  ```
- Use a one-shot migration service with `condition: service_completed_successfully` so the API waits for migrations to complete.
- Implement client-side retries with exponential backoff in the application. Even with healthchecks, the app should tolerate the DB being late by 30-120 seconds.
- Tune `start_period` to the dependency's real cold-start time so early failing probes do not count against retries.
- Use `docker compose up --wait` to block until all healthchecks pass.

**Warning signs:**
- API container crashes on boot with connection-refused errors.
- Services require manual restart after `docker compose up`.
- Intermittent startup failures that work on retry.
- Milvus or etcd in CrashLoopBackOff.

**Phase to address:**
Infrastructure phase. When setting up Docker Compose orchestration. Must be solved before any reliable local development or deployment.

---

### Pitfall 9: Milvus Over-Provisioning for Small Datasets

**What goes wrong:**
Team deploys Milvus (etcd + MinIO + Milvus containers) for semantic search over approximately 1,400 structures and their documents. The operational overhead (monitoring, backups, updates, debugging) consumes disproportionate team time. Vector count never approaches Milvus's design threshold (100M+). Sync issues between PostGIS canonical data and Milvus embeddings cause inconsistency. Index building OOM is the most common production incident in Milvus deployments.

**Why it happens:**
- "We need vector search, Milvus is the vector database" reasoning without considering scale. PROJECT.md pre-selected Milvus before scale analysis.
- Milvus requires etcd (metadata), MinIO/S3 (vector data segments), and optionally Pulsar/Kafka (message queue). That is 3-4 extra containers minimum.
- Index building is the most memory-hungry operation. Without proper `segment.maxSize` and `buildParallel` configuration, the IndexNode OOM-kills during bulk insert.
- Embedding sync between PostGIS (system of record) and Milvus (search index) creates a distributed consistency problem.

**How to avoid:**
- Use pgvector (PostgreSQL extension) instead. `CREATE EXTENSION vector;` and vectors live in the same database as structure data. Hybrid search (full-text + vector) in one SQL query. No extra containers, no sync problem.
- For approximately 1,400 structures with documents, pgvector with HNSW index handles this trivially. Milvus is designed for 100M+ vectors.
- If scale eventually demands Milvus, migrate with export tools. The pgvector to Milvus path is well-documented.
- If Milvus is absolutely required: set `diskSegmentMaxSize` to 512-1024MB, `buildParallel` to 2 (half CPU cores), enable compaction, and allocate at least 8GB RAM for the index node.

**Warning signs:**
- More time spent managing Milvus containers than building features.
- Embedding sync lag between PostGIS and Milvus.
- Milvus OOM-killed during indexing operations.
- 3-4 extra Docker containers for a dataset of thousands of vectors.

**Phase to address:**
AI Copilot phase. When implementing hybrid search for the evidence-grounded Q&A. Decision should be made before any vector infrastructure is deployed.

---

### Pitfall 10: OCR Quality on Russian Scanned Documents (Preprocessing Critical)

**What goes wrong:**
Scanned hydraulic structure passports (in Russian) are OCR'd with Tesseract. Quality is poor: characters are misrecognized, text sections are dropped entirely, and numbers (critical for technical specs like capacity, length, wear percentage) are garbled. The extracted text propagates errors to search indexing, matching algorithms, and the AI copilot. F1 scores as low as 0.16 have been documented for unpreprocessed scanned documents.

**Why it happens:**
- Tesseract requires at least 300 DPI input. Many scanned government documents are lower resolution.
- Skewed pages (text not horizontal) severely degrade Tesseract's line segmentation. Internal deskewing is often insufficient.
- Noise, uneven lighting, and dark borders from scanning confuse the binarization step (Otsu algorithm).
- The default `tessdata` models use integerized LSTM networks. `tessdata_best` (float models) provides better accuracy but is slower.
- For Russian Cyrillic, certain letter variants (especially in older Soviet-era documents) are misrecognized. The `rus` traineddata may confuse similar Cyrillic characters.
- Tesseract is optimized for sentences of words. Technical documents with tables, numbers, and abbreviations need different page segmentation modes (`--psm`).

**How to avoid:**
- Apply preprocessing before Tesseract: deskew, dewarp, remove dark borders, binarize with adaptive thresholding, add white border padding.
- Use `tessdata_best` for Russian (`rus.traineddata` from the tessdata_best repository) when accuracy matters more than speed. Use `tessdata_fast` for bulk processing where post-processing cleanup is feasible.
- Set appropriate `--psm` (page segmentation mode): `--psm 6` for uniform block of text, `--psm 4` for column of text of variable sizes, `--psm 11` for sparse text.
- For technical documents with tables and numbers, consider disabling dictionaries (`load_system_dawg=false`, `load_freq_dawg=false`) to improve number recognition.
- Store OCR confidence scores alongside extracted text. Route low-confidence extractions to human review.
- Test with actual Kazvodhoz documents early. Government scan quality varies wildly.
- Consider PaddleOCR as an alternative. It handles Cyrillic variants and document layouts better than Tesseract in some cases.

**Warning signs:**
- OCR output has many substitution errors (wrong characters in otherwise readable words).
- Numbers in technical specs are garbled or missing.
- Entire text sections are dropped (Tesseract segmentation failure).
- OCR confidence scores are consistently low (below 60%).
- Search for known structure names returns no results due to OCR errors.

**Phase to address:**
Data Ingestion phase. When building the OCR pipeline for scanned passports. Preprocessing must be in place before any OCR output is trusted for search or matching.

---

### Pitfall 11: TiPG OGC API Compliance Gaps

**What goes wrong:**
The system claims OGC API Features/Tiles compliance for integration, but TiPG does not implement OGC Features Part 2 (CRS by Reference). This means clients cannot request data in alternative coordinate reference systems via the API. Additionally, TiPG fails the official OGC CITE compliance tests due to FastAPI OpenAPI document content-type issues. When a government integration partner runs CITE tests against the API, multiple tests fail or are skipped, undermining the "standards-compliant" credibility claim.

**Why it happens:**
- TiPG explicitly chose NOT to implement Features Part 2 to avoid introducing CRS-based GeoJSON. This is a deliberate design decision, documented in their README.
- The CITE test failures stem from FastAPI's OpenAPI document not matching the exact content-type format the test suite expects. This is a known issue (TiPG issue #84) marked as "WontFix" because the maintainers consider it a FastAPI/test-suite issue, not a TiPG bug.
- Missing conformance classes cause CITE tests to be skipped, which appears as failures in the compliance report.

**How to avoid:**
- Do not claim full OGC API Features compliance. Claim compliance with the specific parts TiPG implements: Common Part 1 and 2, Features Part 1 (Core), Features Part 3 (Filtering/CQL2), Tiles Part 1 (Core).
- Clearly document in the API documentation which conformance classes are supported and which are not.
- If CRS by Reference is required for integration, add a custom endpoint in FastAPI that transforms coordinates on output, or use GeoServer as a fallback for legacy WMS/WFS clients that need CRS support.
- Run CITE tests early and document the known failures. Be transparent with integration partners about what passes and what does not.
- Consider contributing the OpenAPI content-type fix upstream to TiPG or FastAPI.

**Warning signs:**
- Integration partners report CITE test failures.
- Clients cannot request data in CRS other than WGS 84.
- Conformance page lists fewer classes than expected.
- "Standards-compliant" claim is challenged by technical reviewers.

**Phase to address:**
API and Integration phase. When setting up TiPG and defining the integration story. Manage expectations about compliance scope early.

## Moderate Pitfalls

### Pitfall 12: Multilingual Full-Text Search Without Russian Language Configuration

**What goes wrong:**
PostgreSQL full-text search using the default `english` text search configuration on Russian/Cyrillic text produces no results. Russian words are not stemmed correctly (e.g., searching for "водохранилище" does not match "водохранилища"). The `simple` configuration treats every word as a literal token, missing morphological variants. Fuzzy matching with `pg_trgm` works for typos but does not handle inflection.

**Why it happens:**
- PostgreSQL ships with a `russian` text search configuration that handles Cyrillic stemming, but developers often use `english` or `simple` by default.
- The `russian` configuration uses a Snowball stemmer that handles Russian morphology (cases, gender, number).
- For Kazakh, PostgreSQL does not ship a dedicated configuration. The `simple` configuration or a custom one must be used.
- Multi-language search requires storing the language per document and using the correct configuration during both indexing and querying.

**How to avoid:**
- Store a `language` column (REGCONFIG) on every searchable text record. Use `russian` for Russian text, `simple` for Kazakh (until a Kazakh stemmer is available), `english` for English.
- Create a trigger that generates the tsvector using the stored language: `setweight(to_tsvector(NEW.language, NEW.title), 'A')`.
- Create separate GIN indexes on the tsvector column.
- Pair FTS with `pg_trgm` for fuzzy/typo tolerance. FTS handles stemming, pg_trgm handles partial words and misspellings.
- For Kazakh, consider transliterating Kazakh-specific characters to Russian equivalents before indexing, so that searches in either language find the same structures.

**Warning signs:**
- Search for Russian words returns no results even though the text exists in the database.
- Search only matches exact string matches, not morphological variants.
- Russian and Kazakh searches behave inconsistently.

**Phase to address:**
Search and Matching phase. When implementing the structure search and evidence-fusion matching algorithm.

---

### Pitfall 13: COG Generation Without Web-Optimized Alignment

**What goes wrong:**
Satellite imagery is converted to COG but without `--web-optimized` flag. The COG bounds and internal tiles are not aligned with the Web Mercator grid. TiTiler must fetch multiple internal tiles to compose a single web tile, degrading performance. At low zoom levels, a single tile request reads the entire file. Response time is 30+ seconds.

**Why it happens:**
- `rio-cogeo` by default creates valid COGs with internal overviews and tiling, but does NOT align to the Web Mercator grid unless `--web-optimized` is passed.
- Without web-optimized alignment, the tiler must fetch multiple internal tiles for each web tile request.
- Missing or incorrect `nodata` values cause black borders around imagery when displayed.
- Using lossy compression (JPEG) with internal nodata values is not recommended. Internal masking should be used instead.

**How to avoid:**
- Use `rio cogeo create input.tif output.tif --web-optimized` for any COG that will be served via TiTiler.
- Ensure nodata values or alpha bands are properly set. Use `--add-mask` for internal bit masks with Byte/UInt16 data.
- Validate COGs with `rio cogeo validate` before storing in MinIO.
- Check overview levels match the expected zoom range. Overviews should not be smaller than the internal tile size (512x512 by default).
- Use `--config GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR` to prevent GDAL from checking for external overviews that could invalidate the COG.
- For Sentinel-2 specifically: JPEG2000 source bands must be converted to COG. Use the developmentseed/sentinel-2-cog pattern (Lambda or local processing with rio-cogeo).

**Warning signs:**
- TiTiler tile requests take 30+ seconds at low zoom.
- Imagery appears with black borders.
- `rio cogeo info` shows no overviews or misaligned bounds.
- Tile requests return errors for certain zoom levels.

**Phase to address:**
Satellite Imagery phase. When building the COG generation and TiTiler serving pipeline.

---

### Pitfall 14: MapLibre Feature State Performance Degradation

**What goes wrong:**
The map uses `setFeatureState` to highlight structures based on condition (color-coded status). With thousands of features and feature state set on each, zooming becomes laggy. The browser stalls for up to 10 frames per zoom level change when returning to previously loaded tile levels. The map feels unresponsive during pan/zoom interactions.

**Why it happens:**
- MapLibre does not fully clear feature state keys after they are unset. The feature state object grows unboundedly.
- When tiles are loaded from the TileCache (previously visited zoom levels), MapLibre re-evaluates every feature using its feature state against each layer's expressions, reading the entire feature into a new VectorTileFeature object.
- This does not happen for tiles that have not been cached yet (initial load is off the main thread).
- Complex map styles with many layers amplify the problem.

**How to avoid:**
- Minimize the use of `setFeatureState`. Only set state on features that are actually hovered/selected, not on every feature.
- Use data-driven styling via vector tile properties instead of feature state for condition-based coloring. Encode the condition status as a tile property and use a `match` expression in the style layer.
- Set `fadeDuration: 0` in performance-critical map configurations.
- Set `maxZoom` on GeoJSON sources to 12 (not the default 22) to reduce tile generation overhead.
- Adjust `minZoom` on layers to prevent rendering at zoom levels where features are too small to see.
- Consider vector tiles (via TiPG) instead of GeoJSON sources for large datasets. Vector tiles handle feature properties more efficiently.
- This issue was partially fixed in MapLibre PR #7590 (May 2026), so pin to a version that includes this fix.

**Warning signs:**
- Map zoom becomes laggy after initial smooth load.
- Browser frame rate drops during pan/zoom.
- DevTools Performance tab shows main thread stalls during tile cache reads.
- Feature state object grows unboundedly (check via `map.style.sourceCaches[layer]._state.state`).

**Phase to address:**
Map and Frontend phase. When implementing the interactive map with condition-based styling.

---

### Pitfall 15: Service Worker Caching API Responses Too Aggressively

**What goes wrong:**
Serwist runtime caching caches all API responses with StaleWhileRevalidate. Structure data appears stale in the UI even after updates. An inspector updates a condition assessment, but the map and details panel show the old data because the service worker served the cached version. Users lose trust in the system.

**How to avoid:**
- Use NetworkFirst for API data (with short timeout fallback to cache). This ensures fresh data when online, cached data when offline.
- Use CacheFirst only for static assets (images, fonts, map tiles, COG tiles).
- Never cache POST/PUT/DELETE responses.
- Set appropriate expiration per resource type: short TTL (5 minutes) for structure data, longer TTL (1 hour) for reference data.
- Implement cache-busting for critical updates: append a version query param to API URLs when data changes.

**Phase to address:**
PWA Field Mode phase. When configuring service worker caching strategies.

---

### Pitfall 16: LangGraph Checkpoint Store in Memory for Production

**What goes wrong:**
LangGraph workflows use MemorySaver (in-process). Server restarts lose all workflow state. Human-in-the-loop reviews that were paused are lost. Users must restart their review process from the beginning.

**How to avoid:**
- Use PostgresSaver for checkpoint persistence in production. MemorySaver is for development only.
- Ensure `thread_id` is consistent across invocations of the same workflow. Case-sensitive and whitespace-sensitive.
- Use a single shared SQLite/Postgres instance per process. Multiple graph instances sharing the same SQLite file cause "database is locked" errors.

**Phase to address:**
AI Copilot phase. When deploying LangGraph workflows to production.

---

### Pitfall 17: OSM Data Without Attribution

**What goes wrong:**
Evidence-fusion locator uses OSM data but the map does not display OSM attribution. This violates the OSM license (ODbL). Legal risk for government deployment.

**How to avoid:**
- Always display "OpenStreetMap contributors" attribution on the map. MapLibre has built-in attribution control.
- Store OSM contribution metadata in provenance tracking.
- Do not use public Nominatim for geocoding (OSM Foundation policy restricts this). Use cached lookups or self-hosted geocoder.

**Phase to address:**
Map and Data Ingestion phases. When integrating OSM data and displaying the map.

---

### Pitfall 18: Stale Vector Tiles After Data Updates

**What goes wrong:**
Inspector updates a structure's condition. The map still shows the old condition color because the vector tile is cached. Decision-makers see outdated information.

**How to avoid:**
- Implement cache invalidation on data update. TiPG's `CatalogUpdateMiddleware` refreshes the catalog.
- For tile cache, use cache-busting query params or short TTLs for data layers.
- Use Varnish BAN pattern or Redis cache invalidation when structure data changes.
- Consider a tile refresh event via WebSocket to trigger client-side tile reloading.

**Phase to address:**
Map and API phase. When setting up tile caching.

## Minor Pitfalls

### Pitfall 19: MapLibre Style URL Dependency on Third-Party Services

**What goes wrong:** Using a third-party style URL (e.g., demotiles.maplibre.org) that changes or goes down. Map appears blank.
**Prevention:** Self-host the base map style JSON and font glyphs. Use OpenFreeMap or generate custom tiles. Store style JSON in the Next.js public directory.

### Pitfall 20: Celery Task Idempotency

**What goes wrong:** OCR task fails midway, gets retried, and processes the same document twice. Duplicate embeddings in pgvector. Duplicate evidence records.
**Prevention:** Use Celery task acknowledgment with `acks_late=True`. Implement idempotency keys (document hash). Check for existing processing before starting. Use database unique constraints.

### Pitfall 21: Next.js i18n Middleware Redirect Loops

**What goes wrong:** Middleware matcher pattern is too broad, matching static assets and API routes. This causes redirect loops or 404s for static files.
**Prevention:** Use the standard matcher pattern that excludes _next, static files, and API routes: `matcher: ['/((?!_next|_vercel|.*\\..*).*)']`. Use `next-intl` Link instead of Next.js Link for locale-aware navigation.

### Pitfall 22: Trilingual Fuzzy Matching Without Kazakh Character Normalization

**What goes wrong:** pg_trgm fuzzy matching works for Russian but fails on Kazakh-specific characters. Structure names with Kazakh characters do not match their Russian transliterations.
**Prevention:** Build a normalization layer: transliterate Kazakh-specific characters to Russian equivalents before matching. Store both original and normalized forms. Test with real Kazvodhoz data early.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `ST_Transform` inside WHERE clauses | Quick to write, no schema change | Sequential scans, 100x slower at scale | Never in production queries |
| MemorySaver for LangGraph checkpointer | No database setup | All workflow state lost on restart | Development only |
| Document-level last-write-wins for sync | Simple to implement | Silent data loss in field scenarios | Never for inspection data |
| SELECT * in ST_AsMVT queries | Quick to prototype | OOM kills, 50-100x tile bloat | Never, even in MVP |
| Using `tessdata_fast` for critical OCR | Faster processing | Poor accuracy on degraded scans | Bulk processing with post-cleanup only |
| Skipping EXPLAIN ANALYZE on spatial queries | Faster development | Production performance disasters | Never for queries on tables > 1000 rows |
| Storing coordinates without explicit SRID | No conversion needed | Silent coordinate errors, query failures | Never |
| Not setting MINIO_SERVER_URL | Works on localhost | Presigned URL failures in production | Development only |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| MinIO behind Nginx | Forgetting `proxy_set_header Host $host` causing signature mismatch | Forward original Host header, set MINIO_SERVER_URL to public URL |
| MinIO S3 client | Not using `forcePathStyle: true` | MinIO serves at `/bucket/` paths, not subdomains. Always enable path style. |
| TiPG + PostGIS | Not creating GiST index on geometry column | `CREATE INDEX ON table USING GIST (geom)` is mandatory. Without it, all spatial queries seq scan. |
| TiPG + MapLibre | Loading all properties in vector tiles | Use TiPG `properties` query parameter to select only display-needed columns |
| LangGraph + checkpointer | Forgetting `thread_id` in config | Always pass consistent `thread_id` in `config["configurable"]` for every invocation |
| Tesseract + Russian | Using default `tessdata` instead of `tessdata_best` | Use `tessdata_best/rus.traineddata` for accuracy-critical OCR |
| PROJ + Kazakhstan | Assuming Pulkovo 1942 transforms are sufficient | Install `qazgrid_kz.gsb` grid file, use QazTRF-23 as intermediate when available |
| Serwist + Next.js | Using CacheFirst for API responses | Use NetworkFirst for API data, CacheFirst only for static assets |
| Sentinel-2 + COG | Converting JPEG2000 without web-optimized flag | Use `rio cogeo create --web-optimized` for TiTiler-served imagery |
| Docker Compose | Using `depends_on` without `condition: service_healthy` | Add healthchecks to all stateful services, gate dependents on `service_healthy` |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| PostGIS geometry/geography runtime cast | Seq scan, 2s+ query times | Store geography column natively or use ST_DWithin with geometry | 10K+ rows |
| ST_AsMVT with all properties | OOM kills, 500KB+ tiles | Select only needed properties, pre-project geometry | 10K+ features per tile |
| MapLibre feature state on all features | Zoom lag, frame drops | Use data-driven styling via tile properties, not feature state | 20K+ features with state |
| TiPG without cache | Slow tile responses under rapid interaction | Add Redis cache middleware, set Cache-Control headers | 5+ concurrent map users |
| COG without web-optimized alignment | 30s+ tile load at low zoom | Use `--web-optimized` flag in rio-cogeo | Any COG served via TiTiler |
| pg_trgm without GIN index | Slow fuzzy search | `CREATE INDEX USING GIN (text gin_trgm_ops)` | 10K+ rows |
| Milvus index building without memory limits | OOM-killed IndexNode | Set `segment.maxSize` to 512-1024MB, `buildParallel` to 2 | 100K+ vectors or large segments |
| Full-text search without GIN index on tsvector | Seq scan on every search | `CREATE INDEX USING GIN (search_vector)` | 1K+ documents |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| MinIO bucket public read for convenience | Sensitive inspection documents accessible without auth | Use presigned URLs with short expiry for authenticated users. Buckets private by default. |
| Exposing MinIO port 9000 to public | Admin password brute-force, data breach | Route all traffic through Nginx/Caddy with TLS. Bind to 127.0.0.1 internally. |
| LLM making final engineering decisions | Incorrect condition assessments, safety risk | LLMs provide evidence-backed recommendations only. All status assignments are human-reviewed. |
| Storing S3 credentials in frontend code | Credential leak via browser inspection | Generate presigned URLs server-side. Never expose MinIO credentials to the client. |
| OSM data without attribution | Legal violation (ODbL license) | Always display OSM attribution on map. MapLibre attribution control. |
| No provenance on AI-generated facts | Untraceable claims, accountability gap | Every fact from the AI copilot must cite its source evidence record |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Kazakh text with broken font rendering | Unprofessional appearance, illegible characters | Load `cyrillic-ext` font subset explicitly |
| Map shows stale data after update | Users lose trust in system, decisions on outdated info | Implement tile cache invalidation, show "last updated" timestamp |
| Offline sync silently overwrites data | Inspectors lose field work without notification | Surface conflicts for human review, log all auto-resolutions |
| OCR errors in search results | Structures unfindable by name | Store OCR confidence, offer fuzzy search with pg_trgm, human review for low-confidence |
| No conflict notification in PWA | Users don't know their data was overwritten | Build conflict UI: "This record was changed elsewhere. Keep yours, theirs, or merge?" |
| Coordinate offsets on map | Structures appear in wrong locations, credibility loss | Verify transformation accuracy against known landmarks before deployment |

## "Looks Done But Isn't" Checklist

- [ ] **Map rendering:** Often missing proper font glyph hosting (map appears with missing labels) — verify glyphs URL is self-hosted
- [ ] **Trilingual UI:** Often missing Kazakh `cyrillic-ext` font subset — verify all 9 Kazakh-specific characters render in the UI font
- [ ] **Offline mode:** Often missing conflict resolution design — verify what happens when two inspectors edit the same structure offline
- [ ] **OGC compliance:** Often missing CITE test verification — run official OGC CITE tests and document pass/fail per conformance class
- [ ] **Coordinate accuracy:** Often missing transformation validation — verify structure positions match satellite imagery within 5m
- [ ] **OCR pipeline:** Often missing preprocessing (deskew, binarize) — verify OCR accuracy on actual scanned passports, not clean test documents
- [ ] **COG serving:** Often missing `--web-optimized` flag — verify tile load times at low zoom levels
- [ ] **LangGraph persistence:** Often missing production checkpointer — verify workflow state survives server restart
- [ ] **Docker startup:** Often missing healthchecks — verify `docker compose up` starts reliably without manual intervention
- [ ] **MinIO presigned URLs:** Often missing MINIO_SERVER_URL — verify presigned URLs work from the browser, not just from the server
- [ ] **Vector tile properties:** Often missing property selection — verify tile sizes are under 500KB
- [ ] **Spatial query performance:** Often missing EXPLAIN ANALYZE verification — verify GiST index is used, not seq scan

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong coordinate system (Pulkovo vs QazTRF-23) | HIGH | Re-ingest all data with correct transformation. Install grid file. Verify against known landmarks. |
| PostGIS index bypass in production | MEDIUM | Add geography column with GiST index. Rewrite queries to use ST_DWithin without casts. Deploy. |
| Vector tile bloat causing OOM | MEDIUM | Rewrite ST_AsMVT queries to select only needed properties. Add pre-projected geometry column. Clear cache. |
| MinIO signature mismatch | LOW | Set MINIO_SERVER_URL. Fix Nginx Host header. Regenerate presigned URLs. |
| LangGraph state lost on restart | MEDIUM | Switch to PostgresSaver. Re-run interrupted workflows. Notify users to restart reviews. |
| Offline sync data loss | HIGH | Cannot recover silently lost data. Implement audit trail going forward. Notify affected inspectors. Add field-level merge. |
| Milvus OOM during indexing | LOW | Reduce segment size, limit buildParallel. Restart Milvus. Re-index. |
| OCR errors propagated to search | HIGH | Re-run OCR with preprocessing and tessdata_best. Re-index search. Re-run matching. Human review of affected records. |
| Docker startup race conditions | LOW | Add healthchecks and conditions. Restart stack. |
| COG without web-optimized | MEDIUM | Re-generate all COGs with --web-optimized flag. Re-upload to MinIO. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| QazTRF-23 coordinate transition | Data Ingestion | `gdaltransform -s_srs EPSG:4284 -t_srs EPSG:10941` produces correct output. Structures align with satellite imagery. |
| PostGIS geometry/geography mixing | Backend API | `EXPLAIN ANALYZE` on all spatial queries shows index scan, not seq scan. |
| Vector tile bloat (ST_AsMVT) | Map and Vector Tiles | Tile sizes under 500KB. No OOM during map use. |
| Kazakh font rendering | Frontend Foundation | All 9 Kazakh-specific characters render in the UI font. No system font fallback. |
| MinIO presigned URL signatures | Infrastructure | Presigned URLs work from browser. No SignatureDoesNotMatch errors. |
| LangGraph state management | AI Copilot | State persists across server restart. Reducers defined for all list fields. thread_id consistent. |
| PWA offline sync conflicts | PWA Field Mode | Conflict notification UI exists. Field-level merge implemented. Audit trail logs auto-resolutions. |
| Docker Compose startup races | Infrastructure | `docker compose up --wait` starts reliably without manual restart. |
| Milvus over-provisioning | AI Copilot | pgvector used instead of Milvus. No extra containers for vector search. |
| OCR quality on Russian docs | Data Ingestion | OCR F1 score above 0.7 on actual scanned passports. Confidence scores stored. |
| TiPG OGC compliance gaps | API and Integration | CITE tests run. Conformance classes documented. Integration partners informed of limitations. |
| Multilingual FTS configuration | Search and Matching | Russian stemming works (case variants match). Kazakh normalization layer tested. |
| COG web-optimized alignment | Satellite Imagery | TiTiler tile load under 1s at all zoom levels. `rio cogeo validate` passes. |
| MapLibre feature state perf | Map and Frontend | No frame drops during zoom on cached tiles. Version includes PR #7590 fix. |
| Service worker caching | PWA Field Mode | API responses are NetworkFirst. No stale data after updates. |
| OSM attribution | Map and Data Ingestion | Attribution control visible on map. OSM provenance stored. |

## Sources

- EPSG Registry: QazTRF-23 (EPSG:10941), Pulkovo 1942 (EPSG:4284), transformation EPSG:10964 with qazgrid_kz.gsb — https://epsg.org/crs_10941/QazTRF-23.html (HIGH confidence)
- Kazakhstan Government Decree on coordinate systems — https://cis-legislation.com/document.fwx?rgn=148462 (HIGH confidence)
- PostGIS Performance Tips — https://postgis.net/docs/performance_tips.html (HIGH confidence)
- PostGIS Anti-Patterns — https://medium.com/@philmcc/why-your-postgis-queries-are-slow-common-anti-patterns-and-fixes-a199e3db9a68 (MEDIUM confidence, verified against official docs)
- Crunchy Data PostGIS Performance — https://www.crunchydata.com/blog/postgis-performance-indexing-and-explain (HIGH confidence)
- ST_AsMVT Performance — https://rmr.ninja/2020-11-19-waiting-for-postgis-3-1-mvt/ and http://blog.cleverelephant.ca/2019/08/postgis-3-mvt.html (HIGH confidence, PostGIS core developer)
- MapLibre Large Data Guide — https://www.maplibre.org/maplibre-gl-js/docs/guides/large-data/ (HIGH confidence)
- MapLibre Feature State Issue #6633 — https://github.com/maplibre/maplibre-gl-js/issues/6633 (HIGH confidence)
- Milvus Operational FAQ — https://milvus.io/docs/operational_faq.md (HIGH confidence)
- Milvus Production Settings — https://markaicode.com/howto/how-to-configure-milvus-production-settings/ (MEDIUM confidence)
- Tesseract ImproveQuality Guide — https://github.com/tesseract-ocr/tessdoc/blob/main/ImproveQuality.md (HIGH confidence)
- Tesseract Data Files (tessdata_best vs fast) — https://tesseract-ocr.github.io/tessdoc/Data-Files.html (HIGH confidence)
- PWA Sync Conflict Resolution — https://dev.to/crisiscoresystems/sync-conflict-handling-in-offline-first-pwas-how-to-merge-without-lying-to-the-user-59i3 (MEDIUM confidence)
- Offline Sync Patterns — https://www.sachith.co.uk/offline-sync-conflict-resolution-patterns-architecture-tradeoffs-practical-guide-feb-19-2026/ (MEDIUM confidence)
- LangGraph Troubleshooting — https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/troubleshooting-debugging/ (MEDIUM confidence, verified against LangGraph docs)
- LangGraph State Management — https://markaicode.com/troubleshoot-langgraph-state-management/ (MEDIUM confidence)
- LangGraph Errors — https://langchain-ai-langgraph-40.mintlify.app/api/errors (HIGH confidence)
- MinIO Nginx Proxy — https://vineethnk.in/blog/setting-up-minio-cdn-nginx-docker/ (MEDIUM confidence)
- MinIO SignatureMismatch Issues — https://github.com/minio/minio/issues/19394, https://github.com/minio/minio/issues/20765 (HIGH confidence)
- TiPG OGC Compliance — https://github.com/developmentseed/tipg, https://github.com/developmentseed/tipg/issues/84 (HIGH confidence)
- rio-cogeo Advanced Topics — https://cogeotiff.github.io/rio-cogeo/Advanced/ (HIGH confidence)
- PostgreSQL pg_trgm — https://www.postgresql.org/docs/current/pgtrgm.html (HIGH confidence)
- PostgreSQL Multilingual FTS — https://kindatechnical.com/postgresql/text-search-configurations-and-dictionaries.html (MEDIUM confidence)
- Next.js i18n Guide — https://nextjs.org/docs/app/guides/internationalization (HIGH confidence)
- next-intl Pitfalls — https://32blog.com/en/nextjs/nextjs-next-intl-i18n-pitfalls (MEDIUM confidence)
- Kazakh Font Rendering — https://imarch.dev/en/blog/paginaciya-i-shrift/ (MEDIUM confidence, verified against Unicode block definitions)
- Kazakh Alphabet Transition — https://en.wikipedia.org/wiki/Kazakh_alphabets (HIGH confidence)
- Docker Compose Startup Order — https://docs.docker.com/compose/how-tos/startup-order/ (HIGH confidence)
- Docker Compose Healthcheck Races — https://www.local-environment-automation.com/containerized-local-environments-docker-compose-patterns/multi-service-orchestration-with-compose/resolving-service-startup-order-and-healthcheck-races/ (MEDIUM confidence)

---
*Pitfalls research for: Geospatial hydraulic infrastructure management system (Zhambyl Oblast, Kazakhstan)*
*Researched: 2026-06-25*
