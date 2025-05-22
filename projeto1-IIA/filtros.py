# filtros.py
import pandas as pd
from geopy.distance import geodesic # Para cálculo de distância
from datetime import datetime
from database import get_dataframe

# --- Funções para carregar DataFrames principais ---
# Estas funções serão chamadas no início do app ou quando necessário
def carregar_dfs_completos():
    """Carrega todos os DataFrames necessários do banco."""
    df_produtores = get_dataframe('produtores')
    df_produtos = get_dataframe('produtos')
    df_estoque = get_dataframe('produtor_estoque')
    df_avaliacoes = get_dataframe('avaliacoes')
    df_usuarios = get_dataframe('usuarios')
    return df_produtores, df_produtos, df_estoque, df_avaliacoes, df_usuarios

def filtro_distancia(lat_usuario, lon_usuario, raio_max_km, df_produtores):
    """Recomenda produtores baseados na distância, usando DataFrame."""
    if df_produtores.empty or lat_usuario is None or lon_usuario is None:
        return pd.DataFrame()

    produtores_proximos = []
    coord_usuario = (lat_usuario, lon_usuario)

    for _, produtor in df_produtores.iterrows():
        if pd.notna(produtor['lat']) and pd.notna(produtor['long']):
            coord_produtor = (produtor['lat'], produtor['long'])
            try:
                dist = geodesic(coord_usuario, coord_produtor).km
                if dist <= raio_max_km:
                    produtor_com_dist = produtor.to_dict()
                    produtor_com_dist['distancia_km'] = dist
                    produtores_proximos.append(produtor_com_dist)
            except ValueError: # Caso de coordenadas inválidas para geopy
                continue
    
    if not produtores_proximos:
        return pd.DataFrame()
        
    df_resultado = pd.DataFrame(produtores_proximos)
    return df_resultado.sort_values(by='distancia_km')

def filtro_preferencia(lista_produtos_desejados, df_produtores, df_produtos, df_estoque):
    """Recomenda produtores que oferecem produtos desejados, usando DataFrames."""
    if df_produtores.empty or df_produtos.empty or df_estoque.empty or not lista_produtos_desejados:
        return pd.DataFrame()

    # Normalizar nomes dos produtos desejados
    produtos_desejados_norm = [p.strip().upper() for p in lista_produtos_desejados]

    # Obter IDs dos produtos desejados
    ids_produtos_desejados = df_produtos[df_produtos['nome'].str.upper().isin(produtos_desejados_norm)]['id'].tolist()

    if not ids_produtos_desejados:
        return pd.DataFrame() # Nenhum dos produtos desejados existe no cadastro

    produtores_qualificados_ids = []
    for id_produtor, group in df_estoque.groupby('id_produtor'):
        produtos_do_produtor_ids = group['id_produto'].tolist()
        # Verifica se o produtor tem TODOS os produtos desejados
        if all(id_desejado in produtos_do_produtor_ids for id_desejado in ids_produtos_desejados):
            produtores_qualificados_ids.append(id_produtor)
            
    if not produtores_qualificados_ids:
        return pd.DataFrame()

    return df_produtores[df_produtores['id'].isin(produtores_qualificados_ids)].copy()

def pegar_estacao():
    """Retorna a estação atual baseada no mês (simplificado)."""
    mes_atual = datetime.now().month
    estacoes_map = {
        1: 'Verão', 2: 'Verão', 3: 'Outono', 4: 'Outono',
        5: 'Outono', 6: 'Inverno', 7: 'Inverno', 8: 'Inverno',
        9: 'Primavera', 10: 'Primavera', 11: 'Primavera', 12: 'Verão'
    }
    return estacoes_map.get(mes_atual, "Indefinida")

def filtro_sazonalidade(estacao_selecionada, df_produtores, df_produtos, df_estoque):
    """Recomenda produtores com produtos da estação, usando DataFrames."""
    if df_produtores.empty or df_produtos.empty or df_estoque.empty or not estacao_selecionada:
        return pd.DataFrame()

    # Produtos da estação ou 'Ano todo'
    produtos_sazonais = df_produtos[
        df_produtos['sazonalidade'].str.upper().isin([estacao_selecionada.upper(), 'ANO TODO'])
    ]
    ids_produtos_sazonais = produtos_sazonais['id'].tolist()

    if not ids_produtos_sazonais:
        return pd.DataFrame()

    # Produtores que oferecem pelo menos um desses produtos sazonais
    produtores_com_sazonais_ids = df_estoque[df_estoque['id_produto'].isin(ids_produtos_sazonais)]['id_produtor'].unique()
    
    if len(produtores_com_sazonais_ids) == 0:
        return pd.DataFrame()

    return df_produtores[df_produtores['id'].isin(produtores_com_sazonais_ids)].copy()


def filtro_colaborativo(df_avaliacoes, df_produtores):
    """Placeholder: Retorna produtores com média de avaliação alta."""
    if df_avaliacoes.empty or df_produtores.empty:
        print("Dados insuficientes para recomendação colaborativa placeholder.")
        return pd.DataFrame()

    media_avaliacoes = df_avaliacoes.groupby('id_produtor')['nota'].mean().reset_index()
    media_avaliacoes = media_avaliacoes.sort_values(by='nota', ascending=False)
    
    # Top N produtores (ex: top 5)
    top_produtores_ids = media_avaliacoes.head(5)['id_produtor'].tolist()

    if not top_produtores_ids:
        return pd.DataFrame()
        
    return df_produtores[df_produtores['id'].isin(top_produtores_ids)].copy()

# ========== Funções de auxiliares ==========
def get_lista_todos_produtos_df(df_produtos):
    if df_produtos.empty: return []
    return sorted(df_produtos['nome'].unique().tolist())

def get_lista_sazonalidades_df():
    return sorted(["Primavera", "Verão", "Outono", "Inverno", "Ano todo"])

if __name__ == '__main__':
    print("--- Teste Filtros (Simplificado com DataFrames) ---")
    df_produtores_main, df_produtos_main, df_estoque_main, df_avaliacoes_main, _ = carregar_dfs_completos()

    if df_produtores_main.empty or df_produtos_main.empty or df_estoque_main.empty:
        print("ERRO: Não foi possível carregar os DataFrames básicos para teste. Verifique o banco de dados.")
    else:
        print(f"Carregados: {len(df_produtores_main)} produtores, {len(df_produtos_main)} produtos, {len(df_estoque_main)} itens de estoque.")

        # Teste de distância
        lat_bsb, lon_bsb = -15.793889, -47.882778 
        raio = 50
        print(f"\n[Distância: Produtores a até {raio}km de ({lat_bsb}, {lon_bsb})]")
        res_dist = filtro_distancia(lat_bsb, lon_bsb, raio, df_produtores_main)
        print(res_dist[['nome', 'distancia_km']].head() if not res_dist.empty else "Nenhum produtor encontrado.")

        # Teste de preferência
        lista_prods = get_lista_todos_produtos_df(df_produtos_main)
        if len(lista_prods) >= 2:
            prods_desejados = [lista_prods[0], lista_prods[1]]
            print(f"\n[Preferência: Produtores que oferecem: {', '.join(prods_desejados)}]")
            res_pref = filtro_preferencia(prods_desejados, df_produtores_main, df_produtos_main, df_estoque_main)
            print(res_pref[['id', 'nome']].head() if not res_pref.empty else "Nenhum produtor encontrado.")
        else:
            print("Produtos insuficientes para teste de preferência.")

        # Teste de sazonalidade
        estacao_teste = pegar_estacao()
        print(f"\n[Sazonalidade: Produtores com produtos de '{estacao_teste}']")
        res_saz = filtro_sazonalidade(estacao_teste, df_produtores_main, df_produtos_main, df_estoque_main)
        print(res_saz[['id', 'nome']].head() if not res_saz.empty else "Nenhum produtor encontrado.")
        
        # Teste colaborativo placeholder
        print(f"\n[Colaborativo Placeholder: Top avaliados]")
        res_colab = filtro_colaborativo(df_avaliacoes_main, df_produtores_main)
        print(res_colab[['id', 'nome']].head() if not res_colab.empty else "Nenhum produtor encontrado ou sem avaliações.")
