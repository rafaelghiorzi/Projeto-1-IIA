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

def filtro_sazonalidade(estacao: str = None):
    """Retorna os produtos disponíveis na estação atual."""
    if estacao is None:
        # Se a estação não for passada, Ano todo
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
