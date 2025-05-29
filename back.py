import time
from db import *
from sqlalchemy.orm import Session
from geopy.distance import geodesic
from sqlalchemy import create_engine, func

# engine principal para rodar querys do banco de dados
engine = create_engine('sqlite:///db.db')

# usuário padrão usado no banco de dados
usuario = None
with Session(engine) as session:
    usuario = session.query(Usuario).filter(Usuario.nome == "rafael" and Usuario.senha ==  "123").first()


# ================= funções auxiliares =================
def get_produtos() -> list[str]:
    """Retorna uma lista com os nomes dos produtos ordenados por nome."""
    with Session(engine) as session:
        produtos = session.query(Produto.nome).order_by(Produto.nome).all()
        produtos = [produto[0] for produto in produtos if isinstance(produto[0], str)]
        return produtos

def get_produtores() -> list[str]:
    """Retorna uma lista com os nomes dos produtores ordenados por nome."""
    with Session(engine) as session:
        produtores = session.query(Produtor.nome).order_by(Produtor.nome).all()
        produtores = [produtor[0] for produtor in produtores if isinstance(produtor[0], str)]
        return produtores

def get_estacao():
    """Retorna a estação atual com base no mês."""
    mes = time.localtime().tm_mon
    estacao = {
        1: "Verão", 2: "Verão", 3: "Outono", 
        4: "Outono", 5: "Outono", 6: "Inverno", 
        7: "Inverno", 8: "Inverno", 9: "Primavera",
        10: "Primavera", 11: "Primavera", 12: "Verão"
    }
    return estacao[mes]

def get_produtor_produtos(produtor_nome: str) -> list[Produto]:
    """Retorna os produtos oferecidos por um produtor específico."""
    with Session(engine) as session:
        produtos = (
            session.query(Produto)
            .join(produtor_produto, Produto.id == produtor_produto.c.produto_id)
            .join(Produtor, produtor_produto.c.produtor_id == Produtor.id)
            .filter(Produtor.nome == produtor_nome)
            .all()
        )
        return produtos

def get_avaliacoes_produtor(produtor_nome: str) -> list[tuple[str, int]]:
    """Retorna as avaliações de um produtor específico."""
    with Session(engine) as session:
        avaliacoes = (
            session.query(Produtor.nome, Usuario.nome, Avaliacao.nota)
            .join(Produtor, Avaliacao.produtor_id == Produtor.id)
            .join(Usuario, Avaliacao.usuario_id == Usuario.id)
            .filter(Produtor.nome == produtor_nome)
            .all()
        )
        
        # Converte para o formato [(nota, usuario.nome)]
        resultado = []
        for produtor_nome, usuario_nome, nota in avaliacoes:
            resultado.append((usuario_nome, nota))
        return resultado

def get_avaliacoes_usuario() -> dict[str, int]:
    """Retorna todas as avaliações do usuário como um dicionário {produtor: nota}"""
    with Session(engine) as session:
  
        # utiliza o usuário padrão definido no início
        if usuario is None:
            return {}
        
        avaliacoes = (
            session.query(Avaliacao, Produtor.nome)
            .join(Produtor, Avaliacao.produtor_id == Produtor.id)
            .filter(Avaliacao.usuario_id == usuario.id)
            .all()
        )

        # Constrói o dicionário diretamente
        return {produtor_nome: avaliacao.nota for avaliacao, produtor_nome in avaliacoes}

# ================= funções de filtros =================
def filtro_distancia(user_lat: float, user_lon: float, raio: float) -> list[Produtor]:
    """Retorna os produtores dentro de um raio especificado a partir da localização do usuário."""
    with Session(engine) as session:
        # Busca todos os produtores
        produtores = session.query(Produtor).all()

        # Calcula a distância entre o usuário e cada produtor
        resultado = []
        for produtor in produtores:
            if produtor.lat is not None and produtor.lon is not None:
                # Calcula a distância usando geopy
                distancia = geodesic(
                    (user_lat, user_lon),
                    (produtor.lat, produtor.lon)
                ).km
                # Filtra a distancia para ver se adiciona nos resultados
                if distancia <= raio:
                    resultado.append(produtor)
        
        # Retorna os produtores dentro do raio ordenados pela distância
        return resultado
    
def filtro_preferencia(preferencia: list) -> list[Produtor]:
    """Retorna os produtores que oferecem todos os produtos da preferência."""
    with Session(engine) as session:
        if not preferencia:
            return []
            
        # Busca todos os ids dos produtos da preferência
        produtos_id = session.query(Produto.id).filter(
            Produto.nome.in_(preferencia)).all()
        produtos_id = [produto[0] for produto in produtos_id]

        if not produtos_id:
            return []
        
        from db import produtor_produto
        # Busca os produtores que oferecem todos os produtos da preferência
        produtores = session.query(Produtor).join(
            produtor_produto).filter(
                produtor_produto.c.produto_id.in_(produtos_id)).group_by(
                    Produtor.id).having(
                        func.count(
                            produtor_produto.c.produto_id
                            ) >= len(produtos_id)).all()

        return produtores
    
def filtro_sazonalidade() -> list[Produtor]:
    """Retorna os produtos disponíveis na estação atual."""
    estacao = get_estacao()

    with Session(engine) as session:
        # Busca os produtos disponíveis na estação atual
        produtos = session.query(Produto).filter(
            Produto.sazonalidade == estacao).all()

        if not produtos:
            return []
        produtos_id = [produto.id for produto in produtos]

        from db import produtor_produto
        produtores = session.query(Produtor).join(
            produtor_produto).filter(
                produtor_produto.c.produto_id.in_(produtos_id)).distinct().all()

        return produtores

# ================= funções principal ==================
# Criação e treinamento de modelo KNN para recomendações
# ======================================================
import pandas as pd
from sklearn.neighbors import NearestNeighbors

def recomendar_produtores():
    """Cria ou treina um modelo KNN para recomendações de produtores."""
    with Session(engine) as session:
        # Busca as informações necessárias
        query = session.query(Avaliacao.usuario_id, Avaliacao.produtor_id, Avaliacao.nota)
        dataframe = pd.read_sql(query.statement, session.connection())

    # Cada linha dessse dataframe é uma avaliação
    # Colunas usuario_id, produtor_id, nota
    matriz = dataframe.pivot_table(
        index='usuario_id',
        columns='produtor_id',
        values='nota',
        fill_value=0
    )
    matriz.fillna(0)
    # cada coluna é um produtor, cada linha é um usuario

    # Criar e treinar o modelo KNN
    modelo = NearestNeighbors(metric='cosine', n_neighbors=5, algorithm='brute')
    modelo.fit(matriz.values)

    # Criar um dicionario com os ids na ordem que aparecem na matriz
    usuarios_idx = {id: i for i, id in enumerate(matriz.index.tolist())}

    idx_usuario = usuarios_idx[usuario.id]
    # criar uma lista de avaliacoes do usuario
    # essa lista mostra o valor da nota para cada produtor na ordem das colunas
    # da matriz pivotada
    avaliacoes_usuario = matriz.iloc[idx_usuario].to_numpy().reshape(1, -1)
    
    # knn retorna a distancia dos vizinhos [[]] e o indice deles na matriz [[]]
    _ , vizinhos_k = modelo.kneighbors(avaliacoes_usuario, n_neighbors=20)

    # inverte o usuarios_idx para encontrar o usuario com base no indice
    usuarios_idx = {value: key for key, value in usuarios_idx.items()}

    vizinhos = []
    # encontrar os vizinhos para colocar na lista
    for i in range(1, len(vizinhos_k[0])):
        idx = vizinhos_k[0][i]
        id = usuarios_idx.get(idx)

        if id is not None:
            vizinhos.append(id)

    # ====================================================
    # Com a lista de vizinhos ordenada e feita, encontrar
    # os vizinhos, seus produtores avaliados e pegar os que
    # o usuário não avaliou e tem uma nota boa para recomendar

    # encontrar os produtores dos vizinhos
    produtores = []
    with Session(engine) as session:    
        for id in vizinhos:
            avaliacoes = session.query(
                Avaliacao.produtor_id).filter(
                    Avaliacao.usuario_id == id).all()
            # Adicionar os ids na lista de produtores
            produtores.extend(aval[0] for aval in avaliacoes)
            
        # pegar os produtores avaliados pelo usuário
        produtores_usuario = session.query(
            Avaliacao.produtor_id).filter(
                Avaliacao.usuario_id == usuario.id).all()
        produtores_usuario = [produtor[0] for produtor in produtores_usuario]

        produtores_finais = [produtor for 
                             produtor in produtores if 
                             produtor not in produtores_usuario]
        # remover duplicados
        produtores_finais = list(set(produtores_finais))

        recomendacoes = session.query(Produtor).filter(
            Produtor.id.in_(produtores_finais)).all()
        # pegar apenas os com nota maior que 3
        produtores_finais = []
        for produtor in recomendacoes:
            avg_nota = session.query(func.avg(Avaliacao.nota)).filter(
                Avaliacao.produtor_id == produtor.id).scalar()
            if avg_nota is not None and avg_nota >= 3:
                produtores_finais.append(produtor)

        print(len(produtores_finais), "produtores recomendados")
        return produtores_finais[:10]  # Retorna os 10 primeiros produtores recomendados

