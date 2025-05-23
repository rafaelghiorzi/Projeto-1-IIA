import db
import folium
import filtros
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# session_state do Streamlit
if 'filtros' not in st.session_state:
    st.session_state.filtros = False
if 'produtores' not in st.session_state:
    st.session_state.produtores = []
if 'usuario' not in st.session_state:
    st.session_state.usuario = "rafael"
if 'recomendados' not in st.session_state:
    st.session_state.recomendados = []

# Ative o modo wide para ocupar toda a largura da tela
st.set_page_config(layout="wide", page_title="Busca por Produtores Locais")

st.title("Busca por produtores locais")
st.subheader(f"Olá, {st.session_state.usuario}!")
recomendar = st.checkbox("Mostrar recomendações?", value=False, key="recomendacoes")

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
        raio = st.slider("Raio máximo (km)", 1, 70, 15)

    lista_produtos = filtros.get_produtos()
    with st.container(border=True):
        st.text("Filtro por preferência 🍎")
        produtos_selecionados = st.multiselect("Quais produtos?", options=lista_produtos)

    estacao_atual = filtros.get_estacao()
    with st.container(border=True):
        st.text("Filtrar por sazonalidade 🍂")
        st.caption(f"Estação atual: {estacao_atual}")
        usar_filtro_sazonalidade = st.checkbox("Mostrar quem possui produtos da estação atual", value=False)

# ============== Aplicação dos filtros! ==============
# Filtro por distancia
produtores = filtros.filtro_distancia(user_lat, user_lon, raio)

if recomendar:
    recomendacoes = filtros.recomendar_produtos(top_n=5, nota_minima=4)
    recomendacoes_ids = [produtor.id for produtor in recomendacoes]
    st.session_state.recomendados = recomendacoes
    # remover os recomendados da lista de produtores
    produtores = [produtor for produtor in produtores if produtor.id not in recomendacoes_ids]
else:
    st.session_state.recomendados = []	

if produtos_selecionados:
    # Filtro por preferência
    produtores_preferencia = filtros.filtro_preferencia(produtos_selecionados)

    ids = [produtor.id for produtor in produtores_preferencia]
    produtores = [produtor for produtor in produtores if produtor.id in ids]

if usar_filtro_sazonalidade:
    # Filtro por sazonalidade
    produtores_sazonalidade = filtros.filtro_sazonalidade()
    ids = [produtor.id for produtor in produtores_sazonalidade]
    produtores = [produtor for produtor in produtores if produtor.id in ids]

# Salvar os resultados no session_state
st.session_state.produtores = produtores
st.session_state.filtros = True

# ============== Exibição dos resultados no mapa! ==============
with col2:

    # Criando o DataFrame para os produtores
    df_produtores = pd.DataFrame()
    if st.session_state.produtores:
        dados = []
        for produtor in st.session_state.produtores:
            # Adiciona os dados do produtor ao DataFrame
            dados.append({
                "nome": produtor.nome,
                "sigla": produtor.sigla if hasattr(produtor, 'sigla') else "",
                "logradouro": produtor.logradouro if hasattr(produtor, 'logradouro') else "",
                "lat": produtor.lat,
                "lon": produtor.lon,
                "nota": round(produtor.nota, 1) if produtor.nota else 0,
            })
        if dados:
            df_produtores = pd.DataFrame(dados)
            df_produtores.sort_values(by="nota", ascending=False, inplace=True)

    # Criando o DataFrame para os recomendados
    df_recomendados = pd.DataFrame()
    if st.session_state.recomendados:
        dados = []
        for produtor in st.session_state.recomendados:
            dados.append({
                "nome": produtor.nome,
                "sigla": produtor.sigla if hasattr(produtor, 'sigla') else "",
                "logradouro": produtor.logradouro if hasattr(produtor, 'logradouro') else "",
                "lat": produtor.lat,
                "lon": produtor.lon,
                "nota": round(produtor.nota, 1) if produtor.nota else 0,
            })
        if dados:
            df_recomendados = pd.DataFrame(dados)
            df_recomendados.sort_values(by="nota", ascending=False, inplace=True)


    # Exibir os resultados em um mapa
    if not df_produtores.empty:
        st.subheader(f"Exibindo {len(df_produtores)} produtores:")

        # Mapa
        mapa = folium.Map(location=[user_lat, user_lon], zoom_start=10)

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
                icon=folium.Icon(color='blue', icon='fa-thumb-tack', prefix='fa'),
                tooltip=row['sigla'],
            ).add_to(mapa)

        for _, row in df_recomendados.iterrows():
            popup = f"""
            <div style="width: 200px">
                <h4>{row['nome']}</h4>
                <p><b>Nota:</b> {row['nota']} ⭐</p>
            </div>
            """
            folium.Marker(
                [row['lat'], row['lon']],
                popup=folium.Popup(popup, max_width=200),
                icon=folium.Icon(color='green', icon='fa-thumb-tack', prefix='fa'),
                tooltip=row['sigla'],
            ).add_to(mapa)

        # Adiciona o marcador do usuário
        folium.Marker([user_lat, user_lon], icon=folium.Icon(color='red'), tooltip="Você").add_to(mapa)
        st_folium(mapa, width=900, height=500, key="mapa")

    else:
        if st.session_state.filtros:
            st.warning("Nenhum produtor encontrado com os filtros atuais.")
        else:
            st.info("Use os filtros à esquerda e clique em 'Aplicar filtros'.")
        mapa = folium.Map(location=[user_lat, user_lon], zoom_start=10)
        # Adiciona o marcador do usuário
        folium.Marker([user_lat, user_lon], icon=folium.Icon(color='red'), tooltip="Você").add_to(mapa)
        st_folium(mapa, width=900, height=500, key="mapa")

# ============== Exibição dos resultados em tabela ==============
with st.container(border=True):
    st.subheader("Tabela de Produtores filtrados:")
    if not df_produtores.empty:
        # escolhe as colunas a serem exibidas
        st.dataframe(df_produtores[["nome", "sigla","logradouro", "nota"]], hide_index=True, use_container_width=True)
    else:
        st.warning("Nenhum produtor encontrado com os filtros atuais.")


# ============== Recomendações personalizadas ==============
with st.container(border=True):
    st.subheader("Recomendações personalizadas:")
    st.text("Essas recomendações são baseadas em usuários semelhantes ao você, com avaliações semelhantes (via algoritmo KNN).")

    if st.session_state.recomendados:
        st.dataframe(df_recomendados[["nome", "sigla","logradouro", "nota"]], hide_index=True, use_container_width=True)
    else:
        st.warning("Nenhuma recomendação disponível no momento.")


st.info("Projeto de introdução à inteligência artificial - Rafael Dias Ghiorzi - 2025/1")