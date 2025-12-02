# app/services/supabase_client.py

import httpx
from app.config import settings


class SupabaseClient:
    """Simple wrapper around Supabase REST API."""

    def __init__(self):
        # REST endpoint
        self.base_url = f"{settings.supabase_url}/rest/v1"

        # Required headers
        self.headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"   # 👈 this ensures Supabase returns JSON
        }

    # ----------------------------------------------------
    # INSERT ROW
    # ----------------------------------------------------
    async def insert(self, table: str, data: dict):
        """Insert one row into a table."""
        url = f"{self.base_url}/{table}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=data, headers=self.headers)

        try:
            if response.status_code == 409:  # Conflict (duplicate)
                return {"status": "duplicate", "url": data.get("url")}
            response.raise_for_status()

        except Exception:
            print("INSERT ERROR:", response.status_code, response.text)
            raise

        # Safely parse JSON (sometimes Supabase returns empty bodies)
        try:
            return response.json()
        except Exception:
            return {"status": response.status_code, "message": response.text}

    # ----------------------------------------------------
    # FETCH ALL
    # ----------------------------------------------------
    async def fetch_all(self, table: str):
        """Fetch all rows."""
        url = f"{self.base_url}/{table}?select=*"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=self.headers)

        response.raise_for_status()
        return response.json()

    # ----------------------------------------------------
    # FETCH WITH QUERY
    # Example: query="url=eq.https://site.com"
    # ----------------------------------------------------
    async def fetch_by_query(self, table: str, query: str):
        url = f"{self.base_url}/{table}?{query}&select=*"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=self.headers)

        response.raise_for_status()
        return response.json()

    # ----------------------------------------------------
    # UPDATE ROWS
    # query example: "id=eq.10"
    # ----------------------------------------------------
    async def update(self, table: str, query: str, data: dict):
        url = f"{self.base_url}/{table}?{query}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.patch(url, json=data, headers=self.headers)

        response.raise_for_status()
        return response.json()

    # ----------------------------------------------------
    # DELETE ROWS
    # ----------------------------------------------------
    async def delete(self, table: str, query: str):
        url = f"{self.base_url}/{table}?{query}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(url, headers=self.headers)

        response.raise_for_status()
        return {"deleted": True}
