# Import Fastapi, framework que facilita a criação de APIs
from fastapi import FastAPI, HTTPException, Depends
import redis
import time
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging
import json
import os 
import requests
logging.basicConfig(level=logging.INFO)
app = FastAPI()
url_base = "https://pokeapi.co/api/v2/"

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



class PokemonDB(Base):
    __tablename__ = "Pokemons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    weight = Column(Integer, index=True)
    height = Column(Integer, index=True)

class Pokemon(BaseModel):
    name: str
    weight: int
    height: int   

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

REDIS_URL = os.getenv("REDIS_URL")

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
        logging.warning("Redis não está disponível.")
        return {"message": "Redis não disponível"}

    pokemons = []
    try:
        keys_iter = redis_client.scan_iter(match="pokemons:*")
    except Exception:
        try:
            keys_iter = redis_client.keys("pokemons:*")
        except Exception as e:
            logging.warning(f"Falha ao listar chaves do Redis: {e}")
            return {"message": "Erro ao listar chaves do Redis"}

    for chave in keys_iter:
        try:
            valor = redis_client.get(chave)
            
            if isinstance(valor, (bytes, bytearray)):
                valor_s = valor.decode("utf-8")
            else:
                valor_s = valor

            
            try:
                parsed = json.loads(valor_s) if valor_s else None
            except Exception:
                parsed = valor_s

            try:
                ttl = redis_client.ttl(chave)
            except Exception:
                ttl = None

            pokemons.append({"chave": chave, "valor": parsed, "ttl": ttl})
        except Exception as e:
            logging.warning(f"Erro ao ler chave do Redis ({chave}): {e}")

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
                "next": f"https://apis-gsuq.onrender.com/pokemons?limit={limit}&offset={offset + limit}",
                "previous": f"https://apis-gsuq.onrender.com/pokemons?limit={limit}&offset={max(offset - limit, 0)}", # placeholder, arrumar problema de numeros negativos
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

@app.get("/data")
async def get_pokemons(page: int = 1, limit: int = 10, db: Session = Depends(sessao_db)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page ou limit com valores inválidos.")

    cache_key = f"pokemons:page={page}:limit={limit}"

    
    cached = None
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
        except Exception as e:
            logging.warning(f"Erro ao acessar cache: {e}")
            cached = None

    if cached:
        try:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            return json.loads(cached)
        except Exception:
            logging.warning("Cache inválido. Continuando para consulta ao DB.")

    
    pokemons = db.query(PokemonDB).offset((page - 1) * limit).limit(limit).all()
    if not pokemons:
        return {"message": "Não existe nenhum Pokémon."}

    total_pokemons = db.query(PokemonDB).count()

    paginacao = {
        "page": page,
        "limit": limit,
        "total": total_pokemons,
        "pokemons": [
            {"id": pokemon.id, "name": pokemon.name, "weight": pokemon.weight, "height": pokemon.height}
            for pokemon in pokemons
        ],
    }

    
    if redis_client:
        try:
            redis_client.setex(cache_key, 90, json.dumps(paginacao))
        except Exception as e:
            logging.warning(f"Falha ao escrever no Redis: {e}")

    return paginacao

@app.post("/pokemons")
async def post_pokemons(pokemon: Pokemon, db: Session = Depends(sessao_db)):
    db_pokemon = db.query(PokemonDB).filter(PokemonDB.name == pokemon.name, PokemonDB.weight == pokemon.weight).first()
    if db_pokemon:
        raise HTTPException(status_code=400, detail="Esse pokémon já existe no banco de dados.")
    novo_pokemon = PokemonDB(name=pokemon.name, weight=pokemon.weight, height=pokemon.height)
    db.add(novo_pokemon)
    db.commit()
    db.refresh(novo_pokemon)

    return {"message": "O Pokémon foi adicionado."}


@app.put("/pokemons/{id_pokemon}")
async def put_pokemons(id_pokemon: int, pokemon: Pokemon, db: Session = Depends(sessao_db)):
    db_pokemon = db.query(PokemonDB).filter(PokemonDB.id == id_pokemon).first()
    if not db_pokemon:
        raise HTTPException(status_code=404, detail="Pokemon não encontrado.")
    db_pokemon.name = pokemon.name
    db_pokemon.weight = pokemon.weight
    db_pokemon.height = pokemon.height
    db.commit()
    db.refresh(db_pokemon)

    return {"message": "O Pokémon foi atualizado."}    

@app.delete("/pokemons/{id_pokemon}")
async def del_pokemons(id_pokemon: int, db: Session = Depends(sessao_db)):
    db_pokemon = db.query(PokemonDB).filter(PokemonDB.id == id_pokemon).first()

    if not db_pokemon:
        raise HTTPException(status_code=404, detail="Esse pokémon não existe.")
    
    db.delete(db_pokemon)
    db.commit()

    return {"message": "Pokémon deletado com sucesso!"}
    
