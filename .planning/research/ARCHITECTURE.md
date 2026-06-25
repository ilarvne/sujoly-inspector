# Architecture Patterns

**Domain:** Geospatial web portal / PWA for hydraulic infrastructure management
**Researched:** 2026-06-25

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (PWA)                              │
│  Next.js 16 + MapLibre GL JS + Serwist + next-intl + IndexedDB  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  │
│  │ Map View  │  │ Passport │  │ Dashboard │  │ Field Capture │  │
│  │ (MapLibre)│  │  Detail  │  │ (Charts)  │  │ (Offline/Dexie)│  │
│  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  └──────┬────────┘  │
│        │             │              │               │            │
│        └─────────────┴──────────────┴───────────────┘            │
│                        TanStack Query                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / REST / OGC API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI (main API) :8000                                │   │
│  │  Auth, business logic, search, AI copilot endpoints      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────┐  ┌────────────────────────────────┐  │
│  │ TiPG :8080           │  │ TiTiler :8081                  │  │
│  │ OGC API Features     │  │ Dynamic raster tiling          │  │
│  │ OGC API Tiles (MVT)  │  │ COG/STAC from MinIO            │  │
│  └──────────┬───────────┘  └──────────────┬─────────────────┘  │
└─────────────┼─────────────────────────────┼────────────────────┘
              │                             │
              ▼                             ▼
┌─────────────────────────┐  ┌──────────────────────────────────┐
│   PostgreSQL + PostGIS  │  │           MinIO :9000            │
│   + pgvector            │  │   S3-compatible object storage    │
│   :5432                 │  │   COGs, STAC items, documents,    │
│                         │  │   photos, voice notes             │
│  ┌───────────────────┐  │  └──────────────────────────────────┘
│  │ structures        │  │
│  │ inspections       │  │  ┌──────────────────────────────────┐
│  │ evidence_sources  │  │  │         Redis :6379              │
│  │ documents (meta)  │  │  │  Cache + Celery broker            │
│  │ match_results     │  │  └──────────────────────────────────┘
│  │ embeddings (pgvec)│  │
│  │ condition_history │  │  ┌──────────────────────────────────┐
│  └───────────────────┘  │  │     Celery Worker (async)        │
│                         │  │  OCR, ingestion, tile gen,       │
└─────────────────────────┘  │  evidence fusion, LangGraph jobs │
                             └──────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Next.js PWA | UI rendering, map display, offline capture, i18n | FastAPI, TiPG, TiTiler (via HTTP) |
| FastAPI Main API | Auth, business logic, search, AI copilot, CRUD | PostgreSQL, Redis, Celery, MinIO, pgvector |
| TiPG | OGC API Features + Tiles from PostGIS (standards-compliant geo API) | PostgreSQL (read-only) |
| TiTiler | Dynamic raster tile serving from COGs/STAC | MinIO (read COGs), optionally PostgreSQL (STAC metadata) |
| PostgreSQL/PostGIS | System of record — all structure data, spatial indexes, vector embeddings | All backend services |
| Redis | Response cache, Celery message broker, session store, rate limiting | FastAPI, Celery |
| MinIO | Binary asset storage — COGs, documents, photos, voice notes | TiTiler, FastAPI, Celery |
| Celery Worker | Background processing — OCR, data ingestion, tile pre-gen, LangGraph workflows | Redis (broker), PostgreSQL, MinIO |
| LangGraph | Workflow orchestration — human-in-the-loop review, RAG pipeline | FastAPI (invokes), PostgreSQL (checkpoint store), pgvector (retrieval) |

### Data Flow

**Map rendering:**
1. Next.js loads MapLibre with a base style (OpenFreeMap or custom)
2. MapLibre requests vector tiles from TiPG (`/collections/{id}/tiles/{z}/{x}/{y}`)
3. TiPG queries PostGIS with `ST_AsMVT()` + spatial bbox filter
4. MapLibre renders MVT as styled vector layers
5. Click on feature → MapLibre fires event → TanStack Query fetches full passport from FastAPI

**Raster imagery:**
1. STAC metadata stored in PostgreSQL or JSON files in MinIO
2. TiTiler receives tile request with STAC item URL
3. TiTiler reads COG from MinIO via S3 HTTP range requests
4. TiTiler extracts tile, applies band math/color map, returns PNG/WebP
5. MapLibre displays as raster layer overlay

**Data ingestion (Kazvodhoz spreadsheet):**
1. Upload spreadsheet via FastAPI endpoint
2. FastAPI enqueues Celery task
3. Celery worker parses spreadsheet (openpyxl/pandas)
4. Worker normalizes data (Russian text, coordinate transforms)
5. Worker inserts into PostgreSQL with provenance metadata
6. Worker enqueues matching task against existing records
7. LangGraph matching workflow runs, produces match taxonomy
8. Human review queue populated for uncertain matches

**AI copilot Q&A:**
1. User asks question in natural language (RU/KK/EN)
2. FastAPI endpoint receives query, invokes LangGraph workflow
3. LangGraph node: translate query if needed
4. LangGraph node: hybrid search — pgvector (semantic) + tsvector (keyword) in one SQL query
5. LangGraph node: LLM generates answer with retrieved context
6. LangGraph node: format response with source citations and confidence
7. Response streamed to frontend

**Offline field capture:**
1. Inspector opens PWA (installed or browser)
2. Service worker (Serwist) serves cached app shell
3. Inspector captures: photo (camera API), voice note (MediaRecorder API), coordinates (Geolocation API), condition assessment (form)
4. Data saved to IndexedDB (Dexie) with sync flag = pending
5. When online, background sync pushes pending records to FastAPI
6. FastAPI validates, stores in PostgreSQL, uploads binary to MinIO
7. Sync queue updated, conflicts flagged for review

## Patterns to Follow

### Pattern 1: PostGIS as System of Record with Provenance
**What:** All canonical structure data lives in PostgreSQL/PostGIS. Every record has a `provenance` JSONB column tracking source, confidence, timestamp, and contributor. External data (OSM, satellite, documents) are evidence sources, not canonical records.

**When:** Always — this is the architectural principle.

**Example:**
```python
class Structure(Base):
    __tablename__ = "structures"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    name_kk: Mapped[Optional[str]]
    name_en: Mapped[Optional[str]]
    geometry: Mapped[WKBElement] = mapped_column(Geometry("POINT", srid=4326))
    structure_type: Mapped[str]
    condition_status: Mapped[str]
    
    # Provenance — every fact has a source
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)
    # {"source": "kazvodhoz_registry", "confidence": 0.95, 
    #  "ingested_at": "2026-06-25T...", "ingested_by": "system"}
    
    # Evidence links — many sources, one canonical record
    evidence: Mapped[list] = mapped_column(JSONB, default=list)
    # [{"type": "osm", "id": 12345, "tags": {...}, "match_confidence": 0.88}]
```

### Pattern 2: Hybrid Search in Single SQL Query (pgvector)
**What:** Combine full-text search and vector similarity in one PostgreSQL query. No cross-system orchestration.

**When:** AI copilot retrieval, semantic search across structure documents.

**Example:**
```sql
-- Hybrid search: keyword (tsvector) + semantic (pgvector) with RRF-style fusion
WITH text_search AS (
    SELECT id, 1.0 / (ROW_NUMBER() OVER (ORDER BY ts_rank(tsv, query) DESC) + 1) AS score
    FROM structures, plainto_tsquery('russian', $1) AS query
    WHERE tsv @@ query
    LIMIT 20
),
vector_search AS (
    SELECT id, 1.0 / (ROW_NUMBER() OVER (ORDER BY embedding <=> $2) + 1) AS score
    FROM structures
    ORDER BY embedding <=> $2
    LIMIT 20
)
SELECT s.*, COALESCE(t.score, 0) + COALESCE(v.score, 0) AS combined_score
FROM structures s
LEFT JOIN text_search t ON s.id = t.id
LEFT JOIN vector_search v ON s.id = v.id
WHERE t.id IS NOT NULL OR v.id IS NOT NULL
ORDER BY combined_score DESC
LIMIT 10;
```

### Pattern 3: LangGraph Human-in-the-Loop with Checkpointing
**What:** Workflow pauses at decision points, waits for human input, then resumes. State is checkpointed to PostgreSQL so it survives restarts.

**When:** Candidate structure verification, matching review, condition assessment review.

**Example:**
```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt, Command

def review_candidate(state):
    """Human reviews a candidate structure match."""
    candidate = state["current_candidate"]
    
    # Pause workflow, wait for human decision
    decision = interrupt({
        "candidate": candidate,
        "evidence": state["evidence_summary"],
        "prompt": "Accept, link to existing, or reject?"
    })
    
    # Resume with human's decision
    return Command(update={"decision": decision, "reviewed_by": state["reviewer_id"]})

# Compile with Postgres checkpoint store — survives restarts
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
app = workflow.compile(checkpointer=checkpointer)
```

### Pattern 4: OGC API as Integration Boundary
**What:** TiPG serves OGC API Features/Tiles directly from PostGIS. External GIS clients (QGIS, ArcGIS) connect to TiPG, not the custom FastAPI. Custom business logic stays in FastAPI.

**When:** Any external integration requirement.

**Why:** Standards compliance without custom code. TiPG auto-discovers PostGIS tables/views. QGIS connects via OGC API Features URL with zero configuration.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Dual System of Record (PostGIS + Milvus)
**What:** Storing canonical structure data in PostGIS but duplicating searchable attributes in Milvus.
**Why bad:** Data synchronization complexity. Two sources of truth. Provenance tracking split across systems. Operational overhead for 2-3 person team.
**Instead:** Use pgvector in PostgreSQL. Vectors live next to relational data in one transaction. If scale demands Milvus later, migrate with export tools.

### Anti-Pattern 2: Pre-generating All Tiles
**What:** Pre-generating vector tiles for all zoom levels and storing as PMTiles/MBTiles.
**Why bad:** Data changes frequently (new inspections, condition updates). Pre-generated tiles become stale. Regeneration is expensive. Storage grows.
**Instead:** Use TiPG for dynamic tile generation from PostGIS (`ST_AsMVT`). Cache with Redis/CDN. Only pre-generate for static basemap layers if needed.

### Anti-Pattern 3: LLM as Decision Maker
**What:** Using LLM output directly for condition assignment or repair priority without human review.
**Why bad:** Safety-critical infrastructure. LLMs hallucinate. Not defensible in regulatory contexts. Violates project principle.
**Instead:** LLMs provide evidence-backed recommendations with confidence levels. LangGraph human-in-the-loop gate enforces review. Final assignment is always human.

### Anti-Pattern 4: Monolithic FastAPI with Embedded TiPG/TiTiler
**What:** Embedding TiPG and TiTiler routers directly into the main FastAPI app to reduce service count.
**Why bad:** Couples geo API lifecycle to business logic lifecycle. TiPG and TiTiler have different scaling characteristics. Harder to debug. Mixes OGC API with custom API.
**Instead:** Run TiPG and TiTiler as separate services. They share PostgreSQL/MinIO but are independently deployable and scalable.

## Scalability Considerations

| Concern | At ~1,400 structures | At ~50K structures | At ~1M structures |
|---------|----------------------|--------------------|--------------------|
| Vector tile serving | TiPG sub-100ms, no cache needed | TiPG + Redis cache, ~100ms | Martin for tiles + TiPG for features |
| Vector search (pgvector) | <10ms, HNSW index | <50ms, HNSW index | Consider Milvus migration |
| Raster tiling (TiTiler) | Sub-second from COG | Sub-second, add CDN | TiTiler + CDN + pre-generation for popular extents |
| Database | Single instance, no replica needed | Read replica for analytics | Partitioning by region, read replicas |
| Background jobs | Single Celery worker | 2-3 workers by queue type | Worker pool with autoscaling |
| Storage (MinIO) | Single node, <100GB | Single node, ~500GB | MinIO distributed mode |

## Sources

- TiPG architecture: https://developmentseed.org/tipg/advanced/ogc_tiles_server/
- TiTiler + STAC: Context7 `/developmentseed/titiler` docs
- LangGraph human-in-the-loop: Context7 `/websites/langchain_oss_python_langgraph`
- Martin architecture: https://maplibre.org/martin/architecture/
- GeoLens reference: https://getgeolens.com/ (PostGIS + pgvector + MapLibre + TiTiler + FastAPI)
- eoAPI reference: Development Seed's earth observation API (TiPG + TiTiler + STAC)
- maplibre-martin-postgis reference: https://github.com/watergis/maplibre-martin-postgis (Varnish cache pattern)
- geostack reference: https://github.com/faisalaffan/geostack (Martin + TiTiler + GeoServer + MinIO)
