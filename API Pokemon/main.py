# Import Fastapi, framework que facilita a criação de APIs
from fastapi import FastAPI, HTTPException
import redis
import json 
import requests
app = FastAPI()
redis_client = redis.Redis(host='redis', port=6379, db= 0, decode_responses=True)
url_base = "https://pokeapi.co/api/v2/"


@app.get("/cache")
def pokemon_cache():
    chaves = redis_client.keys("pokemons:*")
    pokemons = []

    for chave in chaves:
        valor = redis_client.get(chave)
        ttl = redis_client.ttl(chave)
        pokemons.append({"chave": chave, "valor": json.loads(valor), "ttl": ttl})

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
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
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

        redis_client.setex(cache_key, 90, json.dumps(resultado))

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
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
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

        redis_client.setex(cache_key, 90, json.dumps(paginacao))
        
        return paginacao
    else:
        return {"message": f"Falha ao retornar dados. {resposta.status_code}"}
    
    
