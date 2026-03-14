"""Smoke tests for API health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Training Analyzer API"
    assert "version" in data


@pytest.mark.unit
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # /health nutzt die Production-Engine (nicht den Test-Override),
    # daher kann der DB-Check fehlschlagen → "degraded" ist akzeptabel.
    assert data["status"] in ("ok", "degraded")


@pytest.mark.unit
async def test_training_health_endpoint(client: AsyncClient):
    response = await client.get("/api/training/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "training"
