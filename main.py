from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base


SQLALCHEMY_DATABASE_URL = "sqlite:///./data/estoque.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definição do Modelo ORM (Como a tabela será criada no banco)
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)

# cria a tabela no banco de dados automaticamente
Base.metadata.create_all(bind=engine)

# configuração do Fastapi e validação de dados(pydantic)
app = FastAPI(title="API do Estoque")

class ProdutoCreate(BaseModel):
    nome: str
    quantidade: int

class ProdutoResponse(ProdutoCreate):
    id: int
    class Config:
        from_attributes = True

# dependencia do fastapi para abrir e fechar a conexão com o banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# rotas do CRUD

@app.post("/produtos", response_model=ProdutoResponse)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    novo_produto = Produto(nome=produto.nome, quantidade=produto.quantidade) 
    db.add(novo_produto)
    db.commit() 
    db.refresh(novo_produto)
    return novo_produto

@app.get("/produtos", response_model=list[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all() 

@app.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, produto: ProdutoCreate, db: Session = Depends(get_db)):
    produto_db = db.query(Produto).filter(Produto.id == produto_id).first()
    
    if not produto_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    produto_db.nome = produto.nome
    produto_db.quantidade = produto.quantidade
    db.commit()
    return {"mensagem": "Produto atualizado com sucesso"}

@app.delete("/produtos/{produto_id}")
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto_db = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    db.delete(produto_db)
    db.commit()
    return {"mensagem": "Produto deletado com sucesso"}