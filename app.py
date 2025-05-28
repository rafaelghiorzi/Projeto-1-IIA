import folium
import pandas as pd
import streamlit as st
from back import *
from streamlit_folium import st_folium

# ==================== INICIALIZAÇÃO DO SESSION STATE ====================
# Garante que as variáveis de estado da sessão existam.
def init_session_state():
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = False # Indica se os filtros da Página 1 foram aplicados
    if 'produtores_filtrados' not in st.session_state:
        st.session_state.produtores_filtrados = [] # Lista de produtores após filtros da Página 1
    if 'usuario' not in st.session_state:
        st.session_state.usuario = "rafael" # Nome do usuário (pode ser alterado/logado)
    if 'recomendados_lista' not in st.session_state:
        st.session_state.recomendados_lista = [] # Lista de produtores recomendados
    if 'user_lat' not in st.session_state:
        st.session_state.user_lat = -15.793889 # Latitude padrão (Brasília)
    if 'user_lon' not in st.session_state:
        st.session_state.user_lon = -47.882778 # Longitude padrão (Brasília)
    # A chave 'recomendar_page1' para o checkbox será criada automaticamente pelo widget st.checkbox

init_session_state()

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(layout="wide", page_title="Busca por Produtores Locais")

# ==================== FUNÇÕES AUXILIARES ====================
def criar_df_info_produtores(lista_de_objetos_produtor):
    """Cria um DataFrame Pandas com informações dos produtores."""
    dados = []
    if lista_de_objetos_produtor:
        for produtor in lista_de_objetos_produtor:
            dados.append({
                "nome": produtor.nome,
                "sigla": getattr(produtor, 'sigla', ""),
                "logradouro": getattr(produtor, 'logradouro', ""),
                "lat": produtor.lat,
                "lon": produtor.lon,
                "nota": round(produtor.nota, 1) if hasattr(produtor, 'nota') and produtor.nota is not None else 0,
            })
    if dados:
        df = pd.DataFrame(dados)
        df.sort_values(by="nota", ascending=False, inplace=True)
        return df
    return pd.DataFrame() # Retorna DataFrame vazio se não houver dados

def adicionar_marcador_mapa(mapa, lat, lon, nome, nota, sigla, cor_icone, tooltip_text, tipo_icone='fa-thumb-tack'):
    """Adiciona um marcador customizado ao mapa Folium."""
    popup_html = f"""
    <div style="width: 200px">
        <h4>{nome}</h4>
        <p><b>Nota:</b> {nota} ⭐</p>
    </div>
    """
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(popup_html, max_width=200),
        icon=folium.Icon(color=cor_icone, icon=tipo_icone, prefix='fa'),
        tooltip=tooltip_text, # Usar o texto fornecido para o tooltip
    ).add_to(mapa)

# ==================== PÁGINA 1: Filtros e Mapa de Produtores ====================
def pagina_filtros_e_mapa():
    st.header("🔎 Produtores Locais: Filtros e Mapa")
    
    # Checkbox para decidir se as recomendações devem ser geradas e mostradas nesta página
    recomendar_agora = st.checkbox("Gerar e exibir recomendações personalizadas no mapa e tabela abaixo?", value=False, key="recomendar_page1")

    # Layout de colunas para filtros e mapa/tabela
    col1, col2 = st.columns([1, 2]) # Coluna de filtros menor, coluna de resultados maior

    # ============== Coluna 1: Exibição dos filtros! ==============
    with col1:
        st.subheader("Aplicar Filtros")
        with st.container(border=True):
            st.markdown("##### Filtro por distância 📍")
            # Use st.session_state para persistir e acessar user_lat/lon
            user_lat_input = st.number_input("Sua latitude", value=st.session_state.user_lat, format="%.6f", key="user_lat_input_p1")
            user_lon_input = st.number_input("Sua longitude", value=st.session_state.user_lon, format="%.6f", key="user_lon_input_p1")
            raio = st.slider("Raio máximo (km)", 1, 100, 25, key="raio_p1") # Aumentei o raio máximo e o padrão

            # Atualizar session_state se os valores mudarem
            st.session_state.user_lat = user_lat_input
            st.session_state.user_lon = user_lon_input
        
        lista_produtos_disponiveis = get_produtos()
        with st.container(border=True):
            st.markdown("##### Filtro por preferência de produtos 🍎")
            produtos_selecionados = st.multiselect("Quais produtos você procura?", options=lista_produtos_disponiveis, key="produtos_p1")

        estacao_atual = get_estacao() # Obtém a estação atual
        with st.container(border=True):
            st.markdown("##### Filtrar por sazonalidade 🍂")
            st.caption(f"Estação atual: {estacao_atual}")
            usar_filtro_sazonalidade = st.checkbox("Mostrar apenas quem possui produtos da estação atual?", value=False, key="sazonalidade_p1")

    # ============== Aplicação dos filtros! ==============
    # Sempre começa com o filtro de distância
    produtores_base = filtro_distancia(st.session_state.user_lat, st.session_state.user_lon, raio)

    produtores_para_exibir = list(produtores_base) # Copia para manipulação

    if st.session_state.get('recomendar_page1', False): # Verifica o estado do checkbox
        # Gera ou obtém recomendações
        recomendacoes = recomendar_produtores() # Ajuste parâmetros conforme necessário
        st.session_state.recomendados_lista = recomendacoes

        if st.session_state.recomendados_lista:
            recomendacoes_ids = [prod.id for prod in st.session_state.recomendados_lista]
            # Remove recomendados da lista principal para evitar duplicidade no mapa se mostrados com cores diferentes
            produtores_para_exibir = [p for p in produtores_para_exibir if p.id not in recomendacoes_ids]
    else:
        # Se o checkbox não estiver marcado, limpa as recomendações da sessão (para esta página)
        # ou mantém as anteriores se essa for a lógica desejada para Page 2.
        # Para este exemplo, vamos assumir que Page 2 sempre busca as suas.
        pass # st.session_state.recomendados_lista permanece como estava ou é limpa se necessário

    if produtos_selecionados:
        produtores_preferencia = filtro_preferencia(produtos_selecionados)
        ids_preferencia = [p.id for p in produtores_preferencia]
        produtores_para_exibir = [p for p in produtores_para_exibir if p.id in ids_preferencia]

    if usar_filtro_sazonalidade:
        produtores_sazonalidade = filtro_sazonalidade()
        ids_sazonalidade = [p.id for p in produtores_sazonalidade]
        produtores_para_exibir = [p for p in produtores_para_exibir if p.id in ids_sazonalidade]

    st.session_state.produtores_filtrados = produtores_para_exibir
    st.session_state.filtros_aplicados = True

    # ============== Coluna 2: Exibição dos resultados (Mapa e Tabela) ==============
    with col2:
        st.subheader("Resultados da Busca")

        df_produtores_filtrados = criar_df_info_produtores(st.session_state.produtores_filtrados)
        df_recomendados_page1 = pd.DataFrame() # Inicializa DataFrame vazio
        if st.session_state.get('recomendar_page1', False) and st.session_state.recomendados_lista:
             df_recomendados_page1 = criar_df_info_produtores(st.session_state.recomendados_lista)

        # --- Mapa ---
        st.markdown("##### Mapa de Produtores")
        mapa_filtrados = folium.Map(location=[st.session_state.user_lat, st.session_state.user_lon], zoom_start=10)
        
        # Adiciona marcador do usuário
        folium.Marker(
            [st.session_state.user_lat, st.session_state.user_lon], 
            icon=folium.Icon(color='red', icon='user', prefix='fa'), 
            tooltip="Sua localização"
        ).add_to(mapa_filtrados)

        produtores_no_mapa_count = 0
        if not df_produtores_filtrados.empty:
            for _, produtor_row in df_produtores_filtrados.iterrows():
                adicionar_marcador_mapa(mapa_filtrados, produtor_row['lat'], produtor_row['lon'], 
                                        produtor_row['nome'], produtor_row['nota'], produtor_row['sigla'], 
                                        'blue', produtor_row['nome']) # Tooltip com nome para clareza
                produtores_no_mapa_count += 1
        
        recomendados_no_mapa_count = 0
        if not df_recomendados_page1.empty:
            for _, rec_row in df_recomendados_page1.iterrows():
                adicionar_marcador_mapa(mapa_filtrados, rec_row['lat'], rec_row['lon'], 
                                        rec_row['nome'], rec_row['nota'], rec_row['sigla'], 
                                        'green', f"Recomendado: {rec_row['nome']}") # Tooltip diferenciado
                recomendados_no_mapa_count +=1

        if produtores_no_mapa_count == 0 and recomendados_no_mapa_count == 0:
            if st.session_state.filtros_aplicados:
                st.warning("Nenhum produtor encontrado com os filtros atuais.")
            else:
                st.info("Utilize os filtros à esquerda para buscar produtores.")
        
        st_folium(mapa_filtrados, width=800, height=500, key="mapa_page1")
        st.caption(f"Mostrando {produtores_no_mapa_count} produtores filtrados (azul) e {recomendados_no_mapa_count} recomendados (verde).")

    # --- Tabela de Produtores Filtrados ---
    st.markdown("##### Tabela de Produtores Filtrados")
    if not df_produtores_filtrados.empty:
        st.dataframe(df_produtores_filtrados[["nome", "sigla", "logradouro", "nota"]], hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum produtor filtrado para exibir na tabela.")

    # --- Tabela de Produtores Recomendados (se houver) ---
    if st.session_state.get('recomendar_page1', False) and not df_recomendados_page1.empty:
        st.markdown("##### Tabela de Produtores Recomendados")
        st.caption("Estas recomendações são baseadas em diversos fatores, incluindo suas possíveis interações e avaliações de outros usuários.")
        st.dataframe(df_recomendados_page1[["nome", "sigla", "logradouro", "nota"]], hide_index=True, use_container_width=True)
    elif st.session_state.get('recomendar_page1', False) and df_recomendados_page1.empty:
            st.info("Nenhuma recomendação disponível no momento (baseado na sua seleção).")


# ==================== PÁGINA 2: Recomendações ====================
def pagina_recomendacoes():
    st.header("🌟 Recomendações Personalizadas para Você")
    st.markdown("Descubra produtores que podem ser do seu interesse com base no nosso sistema de recomendação.")

    # Botão para forçar a atualização das recomendações
    if st.button("Buscar/Atualizar Recomendações"):
        with st.spinner("Buscando recomendações..."):
            st.session_state.recomendados_lista = recomendar_produtores() # Parâmetros podem ser diferentes para esta página

    if not st.session_state.recomendados_lista:
        st.info("Clique em 'Buscar/Atualizar Recomendações' para ver sugestões ou verifique os filtros na Página 1 caso as recomendações dependam deles e você não os ativou.")
        return

    df_recomendados = criar_df_info_produtores(st.session_state.recomendados_lista)

    if df_recomendados.empty:
        st.warning("Nenhuma recomendação encontrada no momento.")
        return

    # ============== Exibição dos recomendados no mapa! ==============
    st.subheader(f"Mapa com {len(df_recomendados)} Produtores Recomendados:")
    
    # Usar a localização do usuário da Page 1 para centrar o mapa, se disponível, ou um default
    map_center_lat = st.session_state.get('user_lat', -15.793889)
    map_center_lon = st.session_state.get('user_lon', -47.882778)
    
    mapa_recomendacoes = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=9)

    # Adiciona marcador do usuário, se as coordenadas forem as do usuário
    if 'user_lat' in st.session_state and 'user_lon' in st.session_state:
        folium.Marker(
            [st.session_state.user_lat, st.session_state.user_lon],
            icon=folium.Icon(color='red', icon='user', prefix='fa'),
            tooltip="Sua localização (referência)"
        ).add_to(mapa_recomendacoes)

    for _, row in df_recomendados.iterrows():
        adicionar_marcador_mapa(mapa_recomendacoes, row['lat'], row['lon'], 
                                row['nome'], row['nota'], row['sigla'], 
                                'purple', f"Recomendado: {row['nome']}") # Cor diferente para destaque

    st_folium(mapa_recomendacoes, width=900, height=500, key="mapa_recomendacoes")

    # ============== Exibição dos recomendados em tabela ==============
    st.subheader("Detalhes dos Produtores Recomendados:")
    st.dataframe(df_recomendados[["nome", "sigla", "logradouro", "nota"]], hide_index=True, use_container_width=True)
    st.caption("Estas recomendações são baseadas em usuários com perfis e avaliações semelhantes (via algoritmo KNN).")


# ==================== PÁGINA 3: Buscar Produtores e Avaliações ====================
def pagina_busca_e_avaliacoes():
    st.header("📊 Informações e Avaliações de Produtores")

    # ============== Pesquisar produtores =====================
    st.subheader("Buscar Produtor Específico")
    lista_todos_produtores_nomes = get_produtores()
    
    if not lista_todos_produtores_nomes:
        st.warning("Não há produtores cadastrados para busca.")
        return

    nome_produtor_selecionado = st.selectbox(
        'Selecione um produtor para ver detalhes:', 
        options=lista_todos_produtores_nomes,
        index=None, # Nenhum selecionado por padrão
        placeholder="Digite ou selecione um produtor"
    )

    if nome_produtor_selecionado:
        st.markdown(f"### Detalhes de: {nome_produtor_selecionado}")
        
        # --- Avaliações do Produtor ---
        with st.container(border=True):
            st.markdown("##### Avaliações Recebidas")
            avaliacoes_produtor = get_avaliacoes_produtor(nome_produtor_selecionado)
            if avaliacoes_produtor:
                df_avaliacoes = pd.DataFrame(avaliacoes_produtor, columns=["Usuário", "Nota (⭐)"])
                st.dataframe(df_avaliacoes, hide_index=True, use_container_width=True)
            else:
                st.info("Este produtor ainda não possui avaliações.")

        # --- Produtos Ofertados ---
        with st.container(border=True):
            st.markdown("##### Produtos Ofertados")
            produtos_ofertados = get_produtor_produtos(nome_produtor_selecionado)
            if produtos_ofertados:
                dados_produtos = []
                for produto in produtos_ofertados:
                    dados_produtos.append({
                        "Nome": produto.nome,
                        "Descrição": getattr(produto, 'descricao', "-"),
                        "R$/100g": getattr(produto, 'preco_por_100g', "-"),
                        "Kcal/100g": getattr(produto, 'kcal_por_100g', "-"),
                        "Sazonalidade": getattr(produto, 'sazonalidade', "-")
                    })
                df_produtos = pd.DataFrame(dados_produtos)
                st.dataframe(df_produtos, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum produto encontrado para este produtor no momento.")
    else:
        st.info("Selecione um produtor acima para ver seus detalhes.")

    # ============== Suas Avaliações =============================
    st.divider()
    st.subheader(f"Minhas Avaliações ({st.session_state.usuario})")
    avaliacoes_do_usuario = get_avaliacoes_usuario()
    if avaliacoes_do_usuario:
        for produtor, nota in avaliacoes_do_usuario.items():
            st.write(f"**{produtor}**: {nota} ⭐")
    else:
        st.info("Você ainda não avaliou nenhum produtor.")


# ==================== LÓGICA PRINCIPAL DA APLICAÇÃO / ROTEAMENTO DE PÁGINA ====================
st.sidebar.title("Navegação Principal")

pagina_selecionada = st.sidebar.radio(
    "Escolha a seção que deseja acessar:",
    ["Filtros e Mapa de Produtores", "Recomendações Personalizadas", "Buscar Produtores e Avaliações"],
    key="page_selection"
)

# ==================== CABEÇALHO GLOBAL ====================
st.markdown(f"<h1 style='text-align: center;'>Busca de Produtores Locais!</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center;'>Olá, {st.session_state.usuario}!</h3>", unsafe_allow_html=True)
st.markdown("---") # Linha divisória

# ==================== RENDERIZAÇÃO DA PÁGINA SELECIONADA ====================
if pagina_selecionada == "Filtros e Mapa de Produtores":
    pagina_filtros_e_mapa()
elif pagina_selecionada == "Recomendações Personalizadas":
    pagina_recomendacoes()
elif pagina_selecionada == "Buscar Produtores e Avaliações":
    pagina_busca_e_avaliacoes()

# ==================== RODAPÉ ====================
st.sidebar.markdown("---")
st.sidebar.info("Projeto de Introdução à Inteligência Artificial\n\nRafael Dias Ghiorzi - 2025/1")