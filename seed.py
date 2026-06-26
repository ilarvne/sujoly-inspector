#!/usr/bin/env python3
"""Seed script: run migrations, ingest Excel, generate coordinates, names, risk assessments."""
import asyncio
import os
import sys
import subprocess
import structlog

os.environ.setdefault("PYTHONPATH", "/app/api/src")
os.environ.setdefault("API_DATABASE_URL", "postgresql+asyncpg://sujoly:sujoly_dev@localhost:5432/sujoly")
os.environ.setdefault("API_SYNC_DATABASE_URL", "postgresql+psycopg://sujoly:sujoly_dev@localhost:5432/sujoly")

logger = structlog.get_logger(__name__)

def run_migrations():
    """Run alembic migrations."""
    print(">>> Running migrations...")
    result = subprocess.run(
        ["/app/api/.venv/bin/alembic", "upgrade", "head"],
        cwd="/app/api",
        env={**os.environ, "PYTHONPATH": "/app/api/src"},
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"MIGRATION ERROR: {result.stderr}")
        return False
    print(">>> Migrations done.")
    return True

async def seed_data():
    """Ingest Excel data."""
    print(">>> Seeding data from Excel...")
    try:
        from api.services.ingestion_service import bulk_insert_structures
        count = await bulk_insert_structures(filepath="/app/датасет.xls", force=True)
        print(f">>> Seeded {count} structures.")
    except Exception as e:
        print(f"SEED WARNING: {e}")

def generate_coordinates_and_names():
    """Generate coordinates and fix names via SQL."""
    print(">>> Generating coordinates and names...")
    import psycopg
    conn = psycopg.connect("postgresql://sujoly:sujoly_dev@localhost:5432/sujoly")
    cur = conn.cursor()
    # Generate coordinates within Zhambyl Oblast
    cur.execute("""
        UPDATE structures 
        SET geometry = ST_SetSRID(
            ST_MakePoint(
                68.5 + (abs(hashtext(COALESCE(name_ru, id::text))) % 3500) / 1000.0,
                42.5 + (abs(hashtext(COALESCE(name_ru, id::text) || 'salt')) % 2500) / 1000.0
            ), 4326
        )
        WHERE geometry IS NULL;
    """)
    # Fix names: prefix with "Канал №"
    cur.execute("""
        UPDATE structures 
        SET name_ru = 'Канал №' || name_ru 
        WHERE name_ru !~ 'Канал' AND name_ru ~ '^[0-9]+$';
    """)
    # Add wear percentage based on age
    cur.execute("""
        UPDATE structures 
        SET wear_percentage = LEAST(95, GREATEST(5, 
            CASE 
                WHEN commissioning_year IS NOT NULL THEN 
                    LEAST(90, (2026 - commissioning_year) * 1.5 + (abs(hashtext(id::text)) % 20))
                ELSE 30 + (abs(hashtext(id::text)) % 50)
            END
        ))
        WHERE wear_percentage IS NULL;
    """)
    # Add technical condition
    cur.execute("""
        UPDATE structures
        SET technical_condition = 
            CASE 
                WHEN wear_percentage < 50 THEN 'удов.'
                WHEN wear_percentage < 70 THEN 'неуд.'
                ELSE 'авар.'
            END
        WHERE technical_condition IS NULL;
    """)
    conn.commit()
    cur.close()
    conn.close()
    print(">>> Coordinates and names generated.")

async def seed_risk_assessments():
    """Trigger risk recompute for all structures via API."""
    print(">>> Seeding risk assessments...")
    import httpx
    # Get auth token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/api/v1/auth/token",
            json={"api_key": "dev-admin-key"}
        )
        if resp.status_code != 200:
            print(f"AUTH ERROR: {resp.text}")
            return
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all structure IDs
        resp = await client.get(
            "http://localhost:8000/api/v1/structures?limit=1000",
            headers=headers
        )
        if resp.status_code != 200:
            print(f"FETCH ERROR: {resp.text}")
            return
        data = resp.json()
        items = data.get("items", [])
        print(f">>> Found {len(items)} structures to compute risk for.")
        
        # Recompute risk for each
        for item in items:
            sid = item["id"]
            try:
                await client.post(
                    f"http://localhost:8000/api/v1/structures/{sid}/recompute",
                    headers=headers,
                    timeout=10.0
                )
            except Exception:
                pass
    print(">>> Risk assessments seeded.")

async def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if phase in ("pre", "all"):
        if not run_migrations():
            print("FATAL: migrations failed")
            sys.exit(1)
        await seed_data()
        generate_coordinates_and_names()
        print(">>> PRE-SEED COMPLETE.")
    
    if phase in ("post", "all"):
        # Wait for API to be ready
        print(">>> Waiting for API to start...")
        import httpx
        for i in range(30):
            try:
                r = await httpx.AsyncClient().get("http://localhost:8000/health")
                if r.status_code == 200:
                    print(">>> API is ready.")
                    break
            except Exception:
                await asyncio.sleep(2)
        await seed_risk_assessments()
        print(">>> POST-SEED COMPLETE.")
    
    print(">>> ALL SEEDING COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())
