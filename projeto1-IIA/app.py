# app.py (Simplificado)
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
    st.session_state.dataframes_carregados = True

# --- Estado da Sessão ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.page = "Login"
    st.session_state.map_key_counter = 0
    st.session_state.df_resultados_filtrados = st.session_state.df_produtores # Mostrar todos inicialmente

# --- Navegação ---
st.sidebar.title("Projeto 1 de IIA")

if st.session_state.logged_in:
    st.sidebar.write(f"Bem-vindo(a), {st.session_state.username}!")
    pagina_selecionada = st.sidebar.radio(
        "Menu",
        ["Visualizar Produtores", "Fazer Nova Avaliação", "Ver Avaliações", "Logout"], # Adicionado "Ver Avaliações"
        key="nav_logged_in"
    )
    if pagina_selecionada == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.rerun()
    else:
        st.session_state.page = pagina_selecionada
else:
    pagina_selecionada = st.sidebar.radio(
        "Menu",
        ["Login", "Visualizar Produtores"],
        key="nav_logged_out"
    )
    st.session_state.page = pagina_selecionada

# == PÁGINA DE LOGIN E CADASTRO ==
if st.session_state.page == "Login":
    st.title("Sistema de Recomendação de Produtores Rurais")
    login_tab, cadastro_tab = st.tabs(["Login", "Cadastro"])

    with login_tab:
        st.subheader("Login")
        with st.form("login_form_s"):
            username_login = st.text_input("Nome de Usuário", key="login_user_s")
            password_login = st.text_input("Senha", type="password", key="login_pass_s")
            submitted_login = st.form_submit_button("Entrar")

            if submitted_login:
                user_data = database.verificar_login(username_login, password_login)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_data[0]
                    st.session_state.username = user_data[1]
                    st.session_state.page = "Visualizar Produtores"
                    st.success("Login bem-sucedido!")
                    st.rerun()
                else:
                    st.error("Nome de usuário ou senha incorretos.")
    
    with cadastro_tab:
        st.subheader("Cadastro")
        with st.form("cadastro_form_s"):
            username_cadastro = st.text_input("Escolha um Nome de Usuário", key="reg_user_s")
            password_cadastro = st.text_input("Escolha uma Senha", type="password", key="reg_pass_s")
            # Não precisa de confirmação de senha para simplificar
            submitted_cadastro = st.form_submit_button("Registrar")

            if submitted_cadastro:
                success, message = database.registrar_usuario(username_cadastro, password_cadastro)
                if success:
                    st.success(message + " Agora você pode fazer login.")
                    # Recarregar DataFrame de usuários
                    st.session_state.df_usuarios = database.get_dataframe('usuarios')
                else:
                    st.error(message)

# == PÁGINA DE VISUALIZAR PRODUTORES E FILTROS ==
elif st.session_state.page in ["Visualizar Produtores", "Visualizar Produtores"]:
    st.title("Produtores Rurais Locais")

    st.sidebar.header("Filtros de Busca")
    
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

    # Filtro Colaborativo (se logado)
    if st.session_state.logged_in:
        with st.sidebar.expander("🌟 Mais Bem Avaliados", expanded=False):
            aplicar_colaborativo = st.button("aplicar filtro", key="btn_colab_s")
    
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
    elif st.session_state.logged_in and 'aplicar_colaborativo' in locals() and aplicar_colaborativo:
        df_para_exibir = filtros.filtro_colaborativo(st.session_state.df_avaliacoes, st.session_state.df_produtores)
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

# == PÁGINA DE FAZER NOVA AVALIAÇÃO ==
elif st.session_state.page == "Fazer Nova Avaliação" and st.session_state.logged_in:
    st.title("Fazer Nova Avaliação")
    produtores_opts = {nome: id_prod for id_prod, nome in zip(st.session_state.df_produtores['id'], st.session_state.df_produtores['nome'])}
    
    if not produtores_opts:
        st.warning("Nenhum produtor para avaliar.")
    else:
        prod_nome_sel = st.selectbox("Selecione o Produtor:", options=list(produtores_opts.keys()), key="sel_prod_aval_s")
        if prod_nome_sel:
            id_prod_sel = produtores_opts[prod_nome_sel]
            nota = st.slider("Nota (1-5):", 1, 5, 3, key="nota_aval_s")
            comentario = st.text_area("Comentário:", key="com_aval_s")
            if st.button("Enviar Avaliação", key="btn_submit_aval_s"):
                success, message = database.adicionar_avaliacao_db(st.session_state.user_id, id_prod_sel, nota, comentario)
                if success:
                    st.success(message)
                    # Recarregar DataFrame de avaliações
                    st.session_state.df_avaliacoes = database.get_dataframe('avaliacoes')
                else:
                    st.error(message)

# == PÁGINA VER AVALIAÇÕES ==
elif st.session_state.page == "Ver Avaliações": # Acessível a todos, mas mais útil se logado para suas avaliações
    st.title("Avaliações dos Produtores")
    
    if st.session_state.df_avaliacoes.empty:
        st.info("Ainda não há avaliações no sistema.")
    else:
        # Junta avaliações com nomes de produtores e usuários para exibição
        df_display_avaliacoes = st.session_state.df_avaliacoes.copy()
        df_display_avaliacoes = pd.merge(df_display_avaliacoes, st.session_state.df_produtores[['id', 'nome']],
                                         left_on='id_produtor', right_on='id', how='left').rename(columns={'nome': 'nome_produtor'})
        df_display_avaliacoes = pd.merge(df_display_avaliacoes, st.session_state.df_usuarios[['id', 'username']],
                                         left_on='id_usuario', right_on='id', how='left').rename(columns={'id_x':'id_avaliacao'})
        
        st.subheader("Todas as Avaliações")
        st.dataframe(df_display_avaliacoes[['timestamp', 'nome_produtor', 'username', 'nota', 'comentario']].sort_values(by='timestamp', ascending=False))

        if st.session_state.logged_in:
            st.subheader(f"Suas Avaliações ({st.session_state.username})")
            minhas_avaliacoes = df_display_avaliacoes[df_display_avaliacoes['id_usuario'] == st.session_state.user_id]
            if not minhas_avaliacoes.empty:
                st.dataframe(minhas_avaliacoes[['timestamp', 'nome_produtor', 'nota', 'comentario']].sort_values(by='timestamp', ascending=False))
            else:
                st.info("Você ainda não fez nenhuma avaliação.")


st.sidebar.info("IIA - Rafael Dias Ghiorzi - 2025")