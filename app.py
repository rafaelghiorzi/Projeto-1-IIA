# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import database
import filtros

database.inicializar_banco() 

if 'dataframes_carregados' not in st.session_state:
    st.session_state.df_produtores, \
    st.session_state.df_produtos, \
    st.session_state.df_estoque, \
    st.session_state.df_avaliacoes, \
    st.session_state.df_usuarios = filtros.carregar_dfs_completos()
    st.session_state.df_resultados_filtrados = st.session_state.df_produtores.copy()
    st.session_state.map_key_counter = 0
    st.session_state.dataframes_carregados = True

# --- Navegação ---
st.sidebar.title("Projeto 1 de IIA")
st.sidebar.header("Filtros de busca")

# == PÁGINA DE VISUALIZAR PRODUTORES E FILTROS ==
st.title("Busca por produtores locais")
    
# Filtro por Distância
with st.sidebar.expander("📍 Por Distância", expanded=False):
    default_lat, default_lon = -15.793889, -47.882778 
    user_lat = st.number_input("Sua Latitude", value=default_lat, format="%.6f", key="user_lat_s")
    user_lon = st.number_input("Sua Longitude", value=default_lon, format="%.6f", key="user_lon_s")
    max_raio_km = st.slider("Raio Máximo (km)", 1, 200, 20, key="raio_dist_s")
    aplicar_distancia = st.button("Aplicar filtro", key="btn_dist_s")

# Filtro por Preferência de Produtos
lista_prods_opts = filtros.get_lista_todos_produtos_df(st.session_state.df_produtos)
with st.sidebar.expander("🍎 Por Preferência", expanded=False):
    produtos_selecionados = st.multiselect("Quais produtos?", options=lista_prods_opts, key="pref_prod_s")
    aplicar_preferencia = st.button("Aplicar filtro", key="btn_prefiltros")

# Filtro por Sazonalidade
estacao_atual = filtros.pegar_estacao()
lista_saz_opts = filtros.get_lista_sazonalidades_df()
try: default_saz_idx = lista_saz_opts.index(estacao_atual)
except ValueError: default_saz_idx = 0

with st.sidebar.expander("🍂 Por Sazonalidade", expanded=False):
    saz_sel = st.selectbox("Estação:", options=lista_saz_opts, index=default_saz_idx, key="saz_sel_s")
    st.caption(f"Estação atual: {estacao_atual}")
    aplicar_sazonalidade = st.button("Aplicar filtro", key="btn_saz_s")

if st.sidebar.button("Mostrar Todos", key="btn_clear_s"):
    st.session_state.df_resultados_filtrados = st.session_state.df_produtores.copy()
    st.session_state.map_key_counter += 1
    st.rerun()

if st.sidebar.button("Limpar Filtros", key="btn_clear_filters_s"):
    st.session_state.df_resultados_filtrados = st.session_state.df_produtores.copy()
    st.session_state.map_key_counter += 1
    st.session_state.user_lat = default_lat
    st.session_state.user_lon = default_lon
    st.session_state.produtos_selecionados = []
    st.session_state.saz_sel = lista_saz_opts[default_saz_idx]
    st.session_state.aplicar_colaborativo = False
    st.rerun()

# --- Lógica de Aplicação dos Filtros ---
df_para_exibir = st.session_state.df_resultados_filtrados # Começa com todos ou o último resultado

if aplicar_distancia:
    df_para_exibir = filtros.filtro_distancia(user_lat, user_lon, max_raio_km, st.session_state.df_produtores)
    st.session_state.df_resultados_filtrados = df_para_exibir
    st.session_state.map_key_counter += 1
elif aplicar_preferencia:
    if produtos_selecionados:
        df_para_exibir = filtros.filtro_preferencia(produtos_selecionados, st.session_state.df_produtores, st.session_state.df_produtos, st.session_state.df_estoque)
        st.session_state.df_resultados_filtrados = df_para_exibir
        st.session_state.map_key_counter += 1
    else:
        st.warning("Selecione produtos para o filtro de preferência.")
elif aplicar_sazonalidade:
    df_para_exibir = filtros.filtro_sazonalidade(saz_sel, st.session_state.df_produtores, st.session_state.df_produtos, st.session_state.df_estoque)
    st.session_state.df_resultados_filtrados = df_para_exibir
    st.session_state.map_key_counter += 1

# --- Exibição dos Resultados ---
if not df_para_exibir.empty:
    st.subheader(f"Exibindo {len(df_para_exibir)} Produtores:")
    df_mapa = df_para_exibir.dropna(subset=['lat', 'long']).copy()
    
    if not df_mapa.empty:
        map_center_lat = df_mapa['lat'].iloc[0]
        map_center_lon = df_mapa['long'].iloc[0]
        m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=10, key=f"map_s_{st.session_state.map_key_counter}")
        for _, row in df_mapa.iterrows():
            popup_text = f"<b>{row['nome']}</b><br>{row.get('logradouro', 'N/A')}"
            if 'distancia_km' in row: popup_text += f"<br>Dist: {row['distancia_km']:.1f} km"
            folium.Marker([row['lat'], row['long']], popup=popup_text, tooltip=row['sigla']).add_to(m)
        folium.Marker([user_lat, user_lon], popup="Você está aqui", icon=folium.Icon(color='red')).add_to(m)
        st_folium(m, width=900, height=600)
    else:
        st.info("Nenhum produtor com coordenadas para exibir no mapa.")

    cols_display = ['nome', 'sigla', 'logradouro']
    if 'distancia_km' in df_para_exibir.columns: cols_display.append('distancia_km')
    st.dataframe(df_para_exibir[[col for col in cols_display if col in df_para_exibir.columns]])
else:
    st.info("Nenhum produtor encontrado com os filtros atuais.")


st.sidebar.info("IIA - Rafael Dias Ghiorzi - 2025")