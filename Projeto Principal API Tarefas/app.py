# Importação da aplicação para criar APIs "FastAPI" , Pydantic e security para implementar configurações de autenticação de usuários
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import os

# Importação do banco de dados SQLalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Inicialização do FastAPI para criar APIs
app = FastAPI(
    title= "API de tarefas",
    description= "API para gerenciar tarefas",
    version= "1.0.0",
    contact= {
        "name": "Eduardo Drago",
        "email": "eduardondrago05@gmail.com"
    })
security = HTTPBasic()
# Inicialização da lista principal

# Inicialização do Banco de Dados
database_url = os.getenv("database_url")
engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Criação da tabela do banco de dados
class TarefaDB(Base):
    __tablename__ = "Tarefas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String, index=True)
    concluida = Column(Boolean, index=True)

# Criação da classe tarefa que é o modelo de como a informação das tarefas é guardada
class Tarefa(BaseModel):
    nome: str
    descricao: str
    concluida: Optional[bool] = False

Base.metadata.create_all(bind=engine)

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função que usa HTTPBasicCredentials para autenticação do usuário
def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    login = os.getenv("login")
    senha = os.getenv("senha")
    if credentials.username != login or credentials.password != senha:
        raise HTTPException(status_code=401, detail="Acesso negado.")
    return credentials.username

# Endpoint que acessa todas as tarefas
@app.get("/tarefas")
def get_tarefas(page: int = 1, limit: int = 10, db: Session = Depends(sessao_db), credentials: HTTPBasic = Depends(autenticar_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Página ou limite com valores inválidos.")
    tarefa_db = db.query(TarefaDB).offset((page - 1) * limit).limit(limit).all()
    if not tarefa_db:
        return {"message": "Não existe nenhuma tarefa."}

    total_tarefas = db.query(TarefaDB).count()

    return {
        "Page": page,
        "Limit": limit,
        "Total": total_tarefas,
        "Tarefas": [{"Id": tarefa.id, "Nome": tarefa.nome, "Descrição": tarefa.descricao, "Concluída": tarefa.concluida} for tarefa in tarefa_db]
    } 

        
# Endpoint para adicionar novas tarefas
@app.post("/adicionar")
def post_tarefas(tarefa: Tarefa, db: Session = Depends(sessao_db), credentials: HTTPBasic = Depends(autenticar_usuario)):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.nome == tarefa.nome, TarefaDB.descricao == tarefa.descricao).first()
    if tarefa_db:
        raise HTTPException(status_code=400, detail="Essa tarefa já existe.")
    
    nova_tarefa = TarefaDB(nome = tarefa.nome, descricao = tarefa.descricao, concluida = tarefa.concluida)
    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)

    return {"message": "Tarefa criada com sucesso!"}

# Endpoint que checa e atualiza tarefas já existentes
@app.put("/concluir/{nome}")
def put_tarefas(nome: str, concluida: bool = True, db: Session = Depends(sessao_db), credentials: HTTPBasic = Depends(autenticar_usuario)):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.nome == nome).first()
    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    tarefa_db.concluida = concluida
    db.commit()
    db.refresh(tarefa_db)

    return {"message": "A tarefa foi concluida com sucesso!"}
    


# Endpoint que deleta tarefas já existentes 
@app.delete("/deletar/{nome}")
def delete_tarefas(nome: str, db: Session = Depends(sessao_db), credentials: HTTPBasic = Depends(autenticar_usuario)):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.nome == nome).first()

    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    
    db.delete(tarefa_db)
    db.commit()
    
    return {"message": "Sua tarefa foi deletada com sucesso!"}


