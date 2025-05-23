from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, Session, declarative_base
import pandas as pd
import random
from random import randint
from faker import Faker

Base = declarative_base()

# Tabela de associação para relação muitos-para-muitos entre Produtor e Produto
produtor_produto = Table('produtor_produto', Base.metadata,
    Column('produtor_id', Integer, ForeignKey('produtores.id')),
    Column('produto_id', Integer, ForeignKey('produtos.id'))
)

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    senha = Column(String(100), nullable=False)
    
    # Relacionamento com Avaliacao
    avaliacoes = relationship("Avaliacao", back_populates="usuario")
    
    def __repr__(self):
        return f"<Usuario(nome='{self.nome}')>"

class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    sazonalidade = Column(String(50))
    descricao = Column(String(200))
    kcal_por_100g = Column(Integer)
    
    # Relacionamento com Produtor
    produtores = relationship("Produtor", secondary=produtor_produto, back_populates="produtos")
    
    def __repr__(self):
        return f"<Produto(nome='{self.nome}')>"

class Produtor(Base):
    __tablename__ = 'produtores'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    sigla = Column(String(20))
    logradouro = Column(String(200))
    lat = Column(Float)
    lon = Column(Float)
    nota = Column(Float, default=0)  # Média das avaliações
    
    # Relacionamentos
    avaliacoes = relationship("Avaliacao", back_populates="produtor")
    produtos = relationship("Produto", secondary=produtor_produto, back_populates="produtores")
    
    def __repr__(self):
        return f"<Produtor(nome='{self.nome}')>"
    
    def calcular_nota_media(self):
        if not self.avaliacoes:
            return 0
        return sum(a.nota for a in self.avaliacoes) / len(self.avaliacoes)
    
    def atualizar_nota(self):
        self.nota = self.calcular_nota_media()

class Avaliacao(Base):
    __tablename__ = 'avaliacoes'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    produtor_id = Column(Integer, ForeignKey('produtores.id'))
    nota = Column(Integer, nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="avaliacoes")
    produtor = relationship("Produtor", back_populates="avaliacoes")
    
    def __repr__(self):
        return f"<Avaliacao(nota={self.nota})>"

# Criação do banco de dados
def criar_banco():
    engine = create_engine('sqlite:///db.db')
    Base.metadata.create_all(engine)
    return engine

# Função para importar produtos do CSV
def importar_produtos(session):
    df = pd.read_csv('data/produtos.csv')
    produtos = {}
    
    print("Importando produtos...")
    for _, row in df.iterrows():
        # Convertendo kcal/100g para inteiro
        kcal = int(float(row['kcal/100g'])) if not pd.isna(row['kcal/100g']) else 0
        
        produto = Produto(
            nome=row['Nome'],
            sazonalidade=row['Sazonalidade'],
            descricao=row['Descricao'],
            kcal_por_100g=kcal
        )
        session.add(produto)
        produtos[row['Nome']] = produto
        
    session.flush()  # Para gerar os IDs
    print(f"Importados {len(produtos)} produtos")
    return produtos

# Função para importar produtores do CSV com nomes únicos
def importar_produtores(session, produtos_dict):
    df = pd.read_csv('data/produtores.csv')
    produtores = []
    
    print("Importando produtores...")
    
    # Cada linha do CSV agora será um produtor único
    for _, row in df.iterrows():
        # Cria um nome único combinando o nome original e o logradouro
        nome_completo = f"{row['Nome']} - {row['Logradouro']}"
        
        produtor = Produtor(
            nome=nome_completo,
            sigla=row['Sigla'],
            logradouro=row['Logradouro'],
            lat=row['lat'],
            lon=row['lon']
        )
        session.add(produtor)
        
        # Adiciona produtos que são True para este produtor
        for coluna in df.columns[5:]:  # Colunas dos produtos começam no índice 5
            if str(row[coluna]).lower() == 'true':
                if coluna in produtos_dict:
                    produtor.produtos.append(produtos_dict[coluna])
        
        produtores.append(produtor)
    
    session.flush()  # Para gerar os IDs
    print(f"Importados {len(produtores)} produtores únicos")
    return produtores

# Função para criar usuários aleatórios
def criar_usuarios(session, num_usuarios=30):
    print(f"Criando {num_usuarios} usuários aleatórios...")
    fake = Faker('pt_BR')

    usuarios = []
    for i in range(num_usuarios):
        nome = fake.name()
        senha = fake.password()
        usuario = Usuario(nome=nome, senha=senha)
        session.add(usuario)
        usuarios.append(usuario)

    # Adiciona usuario padrão (eu)
    usuario_padrao = Usuario(nome="rafael", senha="123")
    session.add(usuario_padrao)
    usuarios.append(usuario_padrao)

    session.flush()
    print(f"Criados {len(usuarios)} usuários")
    return usuarios

# Função para criar avaliações aleatórias
def criar_avaliacoes(session, usuarios, produtores):
    print("Criando avaliações aleatórias...")
    avaliacoes = []
    
    # Cada usuário avalia entre 1 e 5 produtores aleatórios
    for usuario in usuarios:
        # Escolhe um número aleatório de produtores para avaliar (entre 3 e 8)
        num_avaliacoes = randint(6, min(12, len(produtores)))
        produtores_para_avaliar = random.sample(produtores, num_avaliacoes)
        
        for produtor in produtores_para_avaliar:
            # Notas aleatórias entre 1 e 5
            nota = randint(1, 5)
            avaliacao = Avaliacao(usuario=usuario, produtor=produtor, nota=nota)
            session.add(avaliacao)
            avaliacoes.append(avaliacao)
    
    session.flush()
    print(f"Criadas {len(avaliacoes)} avaliações")
    return avaliacoes

# Função principal para popular o banco
def popular_banco():
    engine = criar_banco()
    with Session(engine) as session:
        # Verifica se o banco já está populado
        if session.query(Produto).count() > 0:
            print("Banco de dados já populado!")
            return
        
        # Importa produtos e produtores
        produtos = importar_produtos(session)
        produtores = importar_produtores(session, produtos)
        
        # Cria usuários e avaliações aleatórias
        usuarios = criar_usuarios(session, 200)
        criar_avaliacoes(session, usuarios, produtores)
        
        # Atualiza as notas médias dos produtores
        print("Atualizando notas médias dos produtores...")
        for produtor in produtores:
            produtor.atualizar_nota()
        
        # Commit das alterações
        session.commit()
        print("Banco de dados populado com sucesso!")

# Função para exibir estatísticas do banco
def mostrar_estatisticas():
    engine = create_engine('sqlite:///db.db')
    with Session(engine) as session:
        
        num_produtos = session.query(Produto).count()
        num_produtores = session.query(Produtor).count()
        num_usuarios = session.query(Usuario).count()
        num_avaliacoes = session.query(Avaliacao).count()
        
        print("\n=== ESTATÍSTICAS DO BANCO ===")
        print(f"Produtos: {num_produtos}")
        print(f"Produtores: {num_produtores}")
        print(f"Usuários: {num_usuarios}")
        print(f"Avaliações: {num_avaliacoes}")
        print("==============================\n")

# Exemplo de uso
if __name__ == "__main__":
    # Popular o banco
    popular_banco()
    
    # Mostrar estatísticas
    mostrar_estatisticas()