# API Pokémon - PT-BR 
Este projeto é uma API RESTful em Python que consome os dados da famosa API PokéAPI, e os retorna de forma paginada, para intuitos educacionais.

## Como rodar localmente

1. Clone o **repositório**:
```
git clone (https://github.com/nevesdrago/APIs/tree/main/API%20Pokemon)
cd API Pokemon
```

2. Com o **Docker** e **Docker Compose** instalados, execute:
```
docker compose up --build
```

3. Então, você pode acessar a documentação automática do **FastAPI (Swagger UI)**:
[http://localhost:8000/docs]

## Exemplo de requisição e resposta da API

1. Na documentação Swagger, no endpoint `/pokemons` a API deve retornar o json:

```json
{
    "data": [...],
    "pagination": {
        "total": 1281,
        "limit": 20,
        "offset": 0,
        "next": "/pokemons?limit=20&offset=20",
        "previous": null    
    }
}
```
1.1. Você também pode atualizar os parâmetros `limit` e `offset` para retornar mais informações dos Pokémons. 



2. O endpoint `/pokemons/{id}` retornará informações específicas de Pokémons especificados por ID.
```json
{
    "name": "pikachu",
    "id": 25,
    "height": 4,
    "weight": 60,
    "types": ["electric"],
    "sprites": {
        "front_default": "https://raw.githubusercontent.com/...",
        "back_default": "https://raw.githubusercontent.com/..."
    } 
}
```

## Execução de testes

Para rodar os testes:

1. Primeiro, certifique-se de que as dependências estão instaladas 
2. Execute o comando abaixo na raiz do projeto:

```
pytest
```

Os testes validarão os principais endpoints, paginação, validação de parâmetros e respostas de erro.

## Link de produção

(link)

# Pokémon API - ENG

This project is a Python RESTful API, that uses data from PokéAPI, returning them paginated, for educational purposes.

## How to run locally

1. Clone the **repository**:
```
git clone (https://github.com/nevesdrago/APIs/tree/main/API%20Pokemon)
cd API Pokemon
```

2. With **Docker** and **Docker Compose** installed, execute:
```
docker compose up --build
```

3. You can then access the automatic **FastAPI (Swagger UI)** documentation:
[http://localhost:8000/docs]

## API request example

1. In the Swagger documentation, the `/pokemons` endpoint must return: 

```json
{
    "data": [...],
    "pagination": {
        "total": 1281,
        "limit": 20,
        "offset": 0,
        "next": "/pokemons?limit=20&offset=20",
        "previous": null    
    }
}
```
1.1. You can update the query parameters `limit` and `offset` to return more Pokémon information.


2. The `/pokemons/{id}` endpoint returns specific Pokémon information by ID.
```json
{
    "name": "pikachu",
    "id": 25,
    "height": 4,
    "weight": 60,
    "types": ["electric"],
    "sprites": {
        "front_default": "https://raw.githubusercontent.com/...",
        "back_default": "https://raw.githubusercontent.com/..."
    } 
}
```

## Tests

To run the tests:

1. First, verify that all the dependencies are installed.
2. Execute the following command:

```
pytest
```

The tests will validate the main endpoints, pagination, parameter validation and errors.

## Production Link

(link)




