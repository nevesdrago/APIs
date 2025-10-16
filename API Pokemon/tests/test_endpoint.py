from unittest.mock import patch
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis_client():
    with patch("main.redis_client") as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = None
        yield

def test_get_pokemons_200():
    response = client.get("/pokemons?limit=20&offset=0")

    assert response.status_code == 200

def test_get_pokemons_id_200():
    response = client.get("/pokemons/1")

    assert response.status_code == 200    

def test_get_pokemons_limit_invalido():
    response = client.get("/pokemons?limit=0")

    assert response.status_code == 400

def test_get_pokemons_offset_invalido():
    response = client.get("/pokemons?limit=10&offset=-1")

    assert response.status_code == 400

def test_get_pokemons_id_invalido():
    response = client.get("/pokemons/0")

    assert response.status_code == 404

def test_get_pokemons_paginacao_correta():
    limit = 20
    offset = 0
    response = client.get("/pokemons")

    data = response.json() 
    assert "pagination" in data

    paginacao = data["pagination"]
    assert paginacao["limit"] == limit
    assert paginacao["offset"] == offset
    assert paginacao["total"] == 1025
    assert paginacao["next"] == f"localhost:8000/pokemons?limit={limit}&offset={offset + limit}"
    assert paginacao["previous"] == f"localhost:8000/pokemons?limit={limit}&offset={max(offset - limit, 0)}"