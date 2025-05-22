import folium
import filtros
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# Ative o modo wide para ocupar toda a largura da tela
st.set_page_config(layout="wide", page_title="Busca por Produtores Locais")

st.title("Busca por produtores locais")

# Ajuste as proporções das colunas para ficarem mais largas
col1, col2 = st.columns([1, 1])

# ============== Exibição dos filtros! ==============
with col1:
    with st.container(border=True):
        st.text("Filtro por distância 📍")
        lat, lon = st.columns([1, 1])
        with lat:
            user_lat = st.number_input("Sua latitude", value=-15.793889, format="%.6f")
        with lon:
            user_lon = st.number_input("Sua longitude", value=-47.882778, format="%.6f")
        raio = st.slider("Raio máximo (km)", 1, 200, 50)

    lista_produtos = filtros.get_produtos()
    with st.container(border=True):
        st.text("Filtro por preferência 🍎")
        produtos_selecionados = st.multiselect("Quais produtos?", options=lista_produtos)

    estacao_atual = filtros.get_estacao()
    with st.container(border=True):
        st.text("Filtrar por sazonalidade 🍂")
        st.caption(f"Estação atual: {estacao_atual}")
        usar_filtro_sazonalidade = st.checkbox("Mostrar apenas produtos da estação atual")

    # Botão para aplicar os filtros
    aplicar_filtros = st.button("Aplicar filtros", type="primary")

# ============== Aplicação dos filtros! ==============
produtores = []

if aplicar_filtros:
    with st.spinner("Buscando produtores..."):
        # Filtro por distancia
        produtores = filtros.filtro_distancia(user_lat, user_lon, raio)

        if produtos_selecionados:
            # Filtro por preferência
            produtores_preferencia = filtros.filtro_preferencia(produtos_selecionados)
            produtores = [produtor for produtor in produtores if produtor in produtores_preferencia]

        # Filtro por sazonalidade
        if usar_filtro_sazonalidade:
            produtores_sazonalidade = filtros.filtro_sazonalidade()
            produtores = [produtor for produtor in produtores if produtor in produtores_sazonalidade]

        st.caption(f"Produtores encontrados: {len(produtores)}")

# Tornar os resultados em um DataFrame
if produtores:
    dados = []
    for produtor in produtores:
        # Adiciona os dados do produtor ao DataFrame
        dados.append({
            "nome": produtor.nome,
            "sigla": produtor.sigla if hasattr(produtor, 'sigla') else "",
            "logradouro": produtor.logradouro if hasattr(produtor, 'logradouro') else "",
            "lat": produtor.lat,
            "lon": produtor.lon,
            "nota": round(produtor.nota, 1) if produtor.nota else 0,
        })
    df_produtores = pd.DataFrame(dados)
else:
    df_produtores = pd.DataFrame(columns=["nome", "sigla", "logradouro", "lat", "lon", "nota", "produtos"])

# ============== Exibição dos resultados no mapa! ==============
with col2:
    # Exibir os resultados em um mapa
    if not df_produtores.empty:
        st.subheader(f"Exibindo {len(df_produtores)} produtores:")

        # Mapa
        centro_lat = user_lat
        centro_lon = user_lon
        mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=10)

        # Marcadores para cada produtor
        for _, row in df_produtores.iterrows():
            popup = f"""
            <div style="width: 200px">
                <h4>{row['nome']}</h4>
                <p><b>Nota:</b> {row['nota']} ⭐</p>
            </div>
            """
            folium.Marker(
                [row['lat'], row['lon']],
                popup=folium.Popup(popup, max_width=200),
                tooltip=row['sigla'],
            ).add_to(mapa)

        folium.Marker([user_lat, user_lon], popup="Você está aqui", tooltip="Você").add_to(mapa)
        st_folium(mapa, width=900, height=600)

    else:
        st.info("Nenhum produtor encontrado com os filtros atuais.")
        centro_lat = user_lat
        centro_lon = user_lon
        mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=10)
        st_folium(mapa, width=900, height=600)
        # Adiciona o marcador do usuário
        folium.Marker([user_lat, user_lon], popup="Você está aqui", tooltip="Você").add_to(mapa)


st.info("Projeto de introdução à inteligência artificial - Rafael Dias Ghiorzi - 2025/1")