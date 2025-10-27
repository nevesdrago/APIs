import json
import pytest
import sys
import os
from fastapi.testclient import TestClient
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main

SQLITE_MEMORY = "sqlite:///:memory:"

engine = create_engine(SQLITE_MEMORY, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

main.Base.metadata.create_all(bind=engine)

def sessao_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

main.app.dependency_overrides[main.sessao_db] = sessao_db

client = TestClient(main.app)

def test_post_cria_pokemons():
    pokemon = {"name": "pokemon", "weight": 12, "height": 3}
    resposta = client.post("/pokemons", json=pokemon)
    assert resposta.status_code == 200 or resposta.status_code == 201 or resposta.json()["message"]

    db = next(sessao_db())
    r = db.query(main.PokemonDB).filter(main.PokemonDB.name == "pokemon").first()
    assert r is not None
    assert r.weight == 12

def test_put_atualiza_pokemons():
    db = next(sessao_db())
    novo = main.PokemonDB(name="pokemon", weight = 1, height = 1)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    pokemon = {"name": "update", "weight": 99, "height": 10}
    resposta = client.put(f"/pokemons/{novo.id}", json=pokemon)
    assert resposta.status_code == 200
    db.refresh(novo)
    assert novo.name == "update"
    assert novo.weight == 99

def test_delete_deleta_pokemons():
    db = next(sessao_db())
    novo = main.PokemonDB(name = "deletar", weight = 1, height = 1)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    resposta = client.delete(f"/pokemons/{novo.id}")
    assert resposta.status_code == 200
    r = db.query(main.PokemonDB).filter(main.PokemonDB.id == novo.id).first()
    assert r is None