# Import Fastapi, framework que facilita a criação de APIs
from fastapi import FastAPI, HTTPException
import redis
import time
import logging
import json
import os 
import requests

logging.basicConfig(level=logging.INFO)
app = FastAPI()
url_base = "https://pokeapi.co/api/v2/"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def connect_redis(url, retries=3, delay=2):
    for attempt in range(1, retries + 1):
        try:
            client = redis.from_url(url, decode_responses=True)
            client.ping()  
            logging.info("Redis conectado com sucesso.")
            return client
        except Exception as e:
            logging.warning(f"Tentativa {attempt}/{retries} de conectar ao Redis falhou: {e}")
            time.sleep(delay)
    logging.error("Não foi possível conectar ao Redis. Seguindo sem cache.")
    return None

redis_client = connect_redis(REDIS_URL)

@app.get("/cache")
def pokemon_cache():
    if not redis_client:
        logging.warning("/Redis não está disponível.")
        return {"message": "Redis não disponível"}
    
    chaves = redis_client.keys("pokemons:*")
    pokemons = []

    for chave in chaves:
        try:
            valor = redis_client.get(chave)
            ttl = redis_client.ttl(chave)
            pokemons.append({"chave": chave, "valor": json.loads(valor), "ttl": ttl})
        except Exception as e:
            logging.warning(f"Erro ao ler chave do Redis: {e}")
            
    return pokemons

# Endpoint GET que retornará os dados dos Pokémons
@app.get("/pokemons")
async def get_pokemons(limit: int = 20, offset: int = 0):
    url = f"{url_base}/pokemon?limit={limit}&offset={offset}"
    resposta = requests.get(url)
    dados_pokemons = resposta.json()
    pokemons = dados_pokemons["results"]

    if limit < 1 or offset < 0:
        raise HTTPException(status_code=400, detail="Valores inválidos.")
    
    cache_key = f"pokemons:offset={offset}&limit={limit}"
    try:
        cached = redis_client.get(cache_key)
    except Exception as e:
        logging.warning(f"Erro ao acessar cache: {e}")
        cached = None

    if cached:
        try:
            return json.loads(cached)
        except Exception:
            logging.warning("Cache inválido")

    if resposta.status_code == 200:
        resultado = {
            "data": pokemons,
            "pagination": {
                "total": 1025,
                "limit": limit,
                "offset": offset,
                "next": f"localhost:8000/pokemons?limit={limit}&offset={offset + limit}",
                "previous": f"localhost:8000/pokemons?limit={limit}&offset={max(offset - limit, 0)}", # placeholder, arrumar problema de numeros negativos
            }
        }
        if redis_client:
            try:    
                redis_client.setex(cache_key, 90, json.dumps(resultado))
            except Exception as e:
                logging.warning(f"Erro ao escrever no Redis. {e}")

        return resultado
    else:
        return {"message": f"Falha ao retornar dados. {resposta.status_code}"}


# Endpoint GET que retorna dados do Pokémon especificado por ID
@app.get("/pokemons/{id}")
async def get_pokemons_id(id: int):
    if id > 1025 or id < 1:
        raise HTTPException(status_code=404, detail="Pokémon não encontrado.")
    
    url = f"{url_base}/pokemon/{id}"
    resposta = requests.get(url)
    dados_pokemon = resposta.json()

    cache_key = f"pokemons:{id}"
    try: 
        cached = redis_client.get(cache_key) if redis_client else None
    except Exception as e:
        logging.warning(f"Erro ao acessar cache: {e}")
        cached = None

    if cached:
        try:
            return json.loads(cached)
        except Exception:
            logging.warning("Cache inválido.")
    
    if resposta.status_code == 200:
        sprites = dados_pokemon["sprites"]
        sprites_selecionados = {
            "front_default": sprites.get("front_default"),
            "back_default": sprites.get("back_default")
        }
        tipos = [tipo["type"]["name"] for tipo in dados_pokemon["types"]]
        paginacao = {
            "name": dados_pokemon["name"].capitalize(),
            "id": dados_pokemon["id"],
            "height": dados_pokemon["height"],
            "weight": dados_pokemon["weight"],
            "types": tipos,
            "sprites": sprites_selecionados    
        }
        if redis_client:
            try:
                redis_client.setex(cache_key, 90, json.dumps(paginacao))
            except Exception as e:
                logging.warning(f"Falha ao escrever no Redis: {e}")

        return paginacao
    else:
        return {"message": f"Falha ao retornar dados. {resposta.status_code}"}
    
    
