import time
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from geopy.distance import geodesic
from db import Produto, Produtor, Usuario, Avaliacao

engine = create_engine('sqlite:///db.db')

def get_produtos():
    """Retorna uma lista de produtos disponíveis no banco de dados."""
    with Session(engine) as session:
        produtos = session.query(Produto.nome).order_by(Produto.nome).all()
        produtos = [produto[0] for produto in produtos]
        return produtos

def get_produtores():
    with Session(engine) as session:
        produtores = session.query(Produtor.nome).all()
        produtores = [produtor[0] for produtor in produtores]
        return produtores

def get_produtor_produtos(produtor_nome: str):
    """Retorna os produtos de um produtor específico"""
    with Session(engine) as session:
        from db import produtor_produto
        
        produtos = (
            session.query(Produto)
            .join(produtor_produto, Produto.id == produtor_produto.c.produto_id)
            .join(Produtor, produtor_produto.c.produtor_id == Produtor.id)
            .filter(Produtor.nome == produtor_nome)
            .all()
        )
        
        return produtos

def get_avaliacao(produtor_nome: str):
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

def get_avaliacao_usuario():
    """Retorna todas as avaliações do usuário como um dicionário {produtor: nota}"""
    with Session(engine) as session:
        # Busca o usuário
        usuario = session.query(Usuario).filter(Usuario.nome == "rafael" and Usuario.senha ==  "123").first()

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

def filtro_distancia(user_lat, user_lon, raio):
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

def filtro_preferencia(preferencia: list):
    """Retorna os produtores que oferecem todos os produtos da preferência."""
    with Session(engine) as session:
        if not preferencia:
            return []
            
        # Busca todos os ids dos produtos da preferência
        produtos_id = session.query(Produto.id).filter(Produto.nome.in_(preferencia)).all()
        produtos_id = [produto[0] for produto in produtos_id]

        if not produtos_id:
            return []
        
        from db import produtor_produto
        # Busca os produtores que oferecem todos os produtos da preferência
        produtores = session.query(Produtor).join(
            produtor_produto).filter(
                produtor_produto.c.produto_id.in_(produtos_id)).group_by(
                    Produtor.id).having(
                        func.count(produtor_produto.c.produto_id) >= len(produtos_id)).all()

        return produtores

def filtro_sazonalidade(estacao: str = ""):
    """Retorna os produtos disponíveis na estação atual."""
    if estacao == "":
        # Se a estação não for passada, pega a estação atual
        estacao = get_estacao()

    with Session(engine) as session:
        # Busca os produtos disponíveis na estação atual
        produtos = session.query(Produto).filter(Produto.sazonalidade == estacao).all()

        if not produtos:
            return []
        produtos_id = [produto.id for produto in produtos]

        from db import produtor_produto
        produtores = session.query(Produtor).join(
            produtor_produto).filter(
                produtor_produto.c.produto_id.in_(produtos_id)).distinct().all()

        return produtores


# =============== Função principal para o projeto ================
# criação e treinamento de modelo KNN para recomendações personalizadas

import pandas as pd
import joblib
from sklearn.neighbors import NearestNeighbors
            
def criar_matriz():
    """Cria uma matriz de produtos e usuários a partir das avaliações."""

    with Session(engine) as session:
        # Busca todos os dados de avaliações
        query = session.query(Avaliacao.usuario_id, Avaliacao.produtor_id, Avaliacao.nota)
        avaliacoes_df = pd.read_sql(query.statement, session.bind)

        if avaliacoes_df.empty:
            print("Nenhuma avaliação encontrada.")
            return pd.DataFrame(), {}, {}
        
        matriz = avaliacoes_df.pivot_table(
            index='usuario_id',
            columns='produtor_id',
            values='nota',
            fill_value=0
        )

        # Mapeamento de ID para Ids
        usuarios_ids = matriz.index.tolist()
        usuarios_map = {usuario: i for i, usuario in enumerate(usuarios_ids)}

        # Preencher possíveis NaN com 0
        matriz = matriz.fillna(0)

        return matriz, usuarios_map
    
def treinar_knn(matriz, n_neighbors=6, metrica='cosine'):
    """Treina o modelo KNN com a matriz de produtos e usuários."""
    if matriz.empty:
        print("Matriz vazia. Não é possível treinar o modelo.")
        return None
    
    print("Treinando o modelo KNN...")
    modelo = NearestNeighbors(metric=metrica, n_neighbors=n_neighbors, algorithm='brute', n_jobs=-1)
    modelo.fit(matriz.values)
    # Salva o modelo em disco
    joblib.dump(modelo, 'modelo_knn.pkl')

    print("Modelo KNN treinado e salvo como modelo_knn.pkl")
    return modelo

def encontrar_vizinhos(usuario: Usuario, modelo: NearestNeighbors, matriz: pd.DataFrame, usuarios_map: dict):
    """Encontra os vizinhos mais próximos para um usuário específico."""
    
    if modelo is None:
        print("Modelo não treinado. Não é possível encontrar vizinhos.")
        return []
    if usuario.id not in usuarios_map:
        print(f"Usuário {usuario.id} não encontrado na matriz.")
        return []
    
    idx_usuario = usuarios_map[usuario.id]
    # Transforma as avaliações do usuário em um vetor
    vetor_usuario = matriz.iloc[idx_usuario].values.reshape(1, -1)

    # Retorna distancia e indices dos vizinhos mais próximos
    distancias, indices_vizinhos = modelo.kneighbors(vetor_usuario, n_neighbors=5)

    # Mapear indices da matriz de volta para os IDs dos usuarios
    vizinhos_distancia = []
    user_map_invertido = {v: k for k, v in usuarios_map.items()} # inverte o dicionário

    for i in range(1, len(indices_vizinhos[0])):
        idx_vizinho = indices_vizinhos[0][i]
        id_vizinho = user_map_invertido.get(idx_vizinho)
        distancia_vizinho = distancias[0][i]

        if id_vizinho is not None:
            vizinhos_distancia.append((id_vizinho, distancia_vizinho))

    return vizinhos_distancia

def recomendar_produtores(top_n=10, nota_minima=3):
    """Recomenda produtores com base nas avaliações do usuário."""
    with Session(engine) as session:
        # Utilizando usuário padrão
        usuario = session.query(Usuario).filter(Usuario.nome == "rafael" and Usuario.senha ==  "123").first()

        matriz, usuarios_map = criar_matriz()
        try:
            modelo = joblib.load('modelo_knn.pkl')
            print("Modelo KNN carregado com sucesso.")
        except FileNotFoundError:
            print("Modelo KNN não encontrado. Treinando um novo modelo.")
            modelo = treinar_knn(matriz)
        
        if modelo is None:
            print("Modelo não encontrado. Não é possível fazer recomendações.")
            return []
        
        vizinhos_distancia = encontrar_vizinhos(usuario, modelo, matriz, usuarios_map)

        # Dado os vizinhos, ordena os produtores por distancia
        vizinhos_distancia.sort(key=lambda x: x[1])

        # salva os ids dos produtores avaliados pelos vizinhos
        ids_produtores = []
        for vizinho, _ in vizinhos_distancia:
            # Busca os produtores avaliados pelo vizinho
            aval_vizinho = session.query(Avaliacao).filter(Avaliacao.usuario_id == vizinho).all()
            for avaliacao in aval_vizinho:
                if avaliacao.nota >= nota_minima:
                    ids_produtores.append(avaliacao.produtor_id)

        # Com esses ids, remove os ids dos produtores que o usuario já avaliou
        query = session.query(Avaliacao).filter(Avaliacao.usuario_id == usuario.id).all()
        ids_avaliados = {avaliacao.produtor_id for avaliacao in query}
        ids_produtores = [produtor for produtor in ids_produtores if produtor not in ids_avaliados]
        # Remove duplicados
        ids_produtores = list(set(ids_produtores))
        # Busca os produtores recomendados
        recomendacoes = session.query(Produtor).filter(Produtor.id.in_(ids_produtores)).all()
        # Ordena os produtores recomendados pela nota média
        recomendacoes.sort(key=lambda x: x.nota, reverse=True)
        # Limita o número de recomendações
        recomendacoes = recomendacoes[:top_n]
        return recomendacoes

