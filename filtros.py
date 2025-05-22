import time
import pandas as pd
from geopy.distance import geodesic

def get_produtos():
    df = pd.read_csv("data/produtores.csv", sep=",")

    return df.columns[5:]

def get_df():
    return pd.read_csv("data/produtores.csv", sep=",")

def get_estacao():
    mes = time.localtime().tm_mon
    estacao = {
        1: "Verão",
        2: "Verão",
        3: "Outono",
        4: "Outono",
        5: "Outono",
        6: "Inverno",
        7: "Inverno",
        8: "Inverno",
        9: "Primavera",
        10: "Primavera",
        11: "Primavera",
        12: "Verão"
    }
    return estacao[mes]

def filtro_distancia(user_lat, user_lon, raio) -> pd.DataFrame:
    df = get_df()

    df['distancia'] = df.apply(
        lambda row: geodesic(
            (user_lat, user_lon),
            (row['lat'], row['lon'])
        ).km, axis=1)

    df = df[df['distancia'] <= raio]
    return df

def filtro_preferencia(preferencia: list):
    # retorna os produtores que tem as colunas presentes na preferencia como true
    
    df = get_df()
    filtro = df[preferencia].all(axis=1)
    return df[filtro]


if __name__ == "__main__":
    # Teste filtro_distancia
    user_lat = -15.8
    user_lon = -47.9
    raio = 50  # km
    print("Produtores dentro do raio:")
    print(filtro_distancia(user_lat, user_lon, raio)[['Nome', 'distancia']])

    # Teste filtro_preferencia
    preferencia = ['Cenoura']
    print("\nProdutores com todos os produtos da preferência:")
    print(filtro_preferencia(preferencia)[['Nome']])