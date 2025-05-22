import folium
import filtros
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# Ative o modo wide para ocupar toda a largura da tela
st.set_page_config(layout="wide")

st.title("Busca por produtores locais")

# Ajuste as proporções das colunas para ficarem mais largas
col1, col2 = st.columns([1, 1])

# ============== Exibição dos filtros! ==============
with col1:
    with st.container(border=True):
        st.text("Filtro por distância 📍")
        lat, lon = st.columns([1, 1])
        with lat:
            user_lat = st.number_input("Sua latitude", value=-15.0, format="%.6f")
        with lon:
            user_lon = st.number_input("Sua longitude", value=-47.0, format="%.6f")
        raio = st.slider("Raio máximo (km)", 1, 200, 10)

    lista_produtos = filtros.get_produtos()
    with st.container(border=True):
        st.text("Filtro por preferência 🍎")
        produtos = st.multiselect("Quais produtos?", options=lista_produtos)

    estacao_atual = filtros.get_estacao()
    lista_sazonalidades = ["Ano todo", "Verão", "Outono", "Inverno", "Primavera"]
    with st.container(border=True):
        st.text("Filtrar por sazonalidade 🍂")
        st.caption(f"Estação atual: {estacao_atual}")
        sazonalidade = st.selectbox("Estação:", options=lista_sazonalidades)

# aplicar os filtros dinamicamente
produtores = pd.DataFrame()


# ============== Exibição dos resultados no mapa! ==============
with col2:
    # Exibir os resultados em um mapa
    if not produtores.empty:
        st.subheader(f"Exibindo {len(produtores)} produtores:")
        mapa_dataframe = produtores.dropna(subset=["lat", "lon"]).copy()

        if not mapa_dataframe.empty:
            centro_lat = user_lat
            centro_lon = user_lon

            mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=10)

            for _, row in mapa_dataframe.iterrows():
                popup = f"<p>{row['nome']} ({row.get("logradouro, 'N/A")})</p>"
                folium.Marker([row['lat'], row['lon']], popup=popup, tooltip=row['sigla']).add_to(mapa)

            folium.Marker([user_lat, user_lon], popup="Você está aqui", icon=folium.Icon(color='red')).add_to(mapa)
            st_folium(mapa, width=900, height=600)

        else:
            st.info("Nenhum produtor com coordenadas para exibir no mapa.")

    else:
        st.info("Nenhum produtor encontrado com os filtros atuais.")

st.info("Projeto de introdução à inteligência artificial - Rafael Dias Ghiorzi - 2025/1")