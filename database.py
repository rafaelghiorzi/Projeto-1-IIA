import sqlite3
import pandas as pd
import os

DATABASE_NAME = 'db.db'

def criar_conexao():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao SQLite DB: {e}")
    return conn

def criar_tabelas(conn):
    if conn is None: return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL -- Senha como texto simples
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                sazonalidade TEXT,
                descricao TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                sigla TEXT,
                logradouro TEXT,
                lat REAL,
                long REAL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtor_estoque (
                id_produtor INTEGER NOT NULL,
                id_produto INTEGER NOT NULL,
                FOREIGN KEY (id_produtor) REFERENCES produtores (id) ON DELETE CASCADE,
                FOREIGN KEY (id_produto) REFERENCES produtos (id) ON DELETE CASCADE,
                PRIMARY KEY (id_produtor, id_produto)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_produtor INTEGER NOT NULL,
                nota INTEGER CHECK (nota >= 1 AND nota <= 5),
                comentario TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES usuarios (id) ON DELETE CASCADE,
                FOREIGN KEY (id_produtor) REFERENCES produtores (id) ON DELETE CASCADE
            );
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar tabelas: {e}")

def popular_dados_iniciais(conn, caminho_csv_produtores, caminho_csv_produtos):
    if conn is None: return
    cursor = conn.cursor()
    try:
        df_produtos_csv = pd.read_csv(caminho_csv_produtos)
        produtos_inseridos = {}
        for _, row in df_produtos_csv.iterrows():
            try:
                cursor.execute("INSERT INTO produtos (nome, sazonalidade, descricao) VALUES (?, ?, ?)",
                               (row['nome'], row['sazonalidade'], row['descrição']))
                produtos_inseridos[row['nome'].upper()] = cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM produtos WHERE nome = ?", (row['nome'],))
                res = cursor.fetchone()
                if res: produtos_inseridos[row['nome'].upper()] = res[0]

        df_produtores_csv = pd.read_csv(caminho_csv_produtores)
        colunas_fixas_produtor = ['nome', 'sigla', 'logradouro', 'lat', 'lon']
        colunas_de_produtos_no_csv = [col for col in df_produtores_csv.columns if col.lower() not in map(str.lower, colunas_fixas_produtor)]

        for _, row in df_produtores_csv.iterrows():
            try:
                cursor.execute("INSERT INTO produtores (nome, sigla, logradouro, lat, long) VALUES (?, ?, ?, ?, ?)",
                               (row['nome'], row['sigla'], row['logradouro'], row['lat'], row['lon']))
                id_produtor = cursor.lastrowid
                for nome_produto_csv in colunas_de_produtos_no_csv:
                    if pd.notna(row[nome_produto_csv]) and (row[nome_produto_csv] == True or str(row[nome_produto_csv]).upper() == 'TRUE'):
                        nome_produto_upper = nome_produto_csv.upper()
                        if nome_produto_upper in produtos_inseridos:
                            id_produto_db = produtos_inseridos[nome_produto_upper]
                            cursor.execute("INSERT INTO produtor_estoque (id_produtor, id_produto) VALUES (?, ?)",
                                           (id_produtor, id_produto_db))
            except Exception as e_prod:
                print(f"Erro ao processar produtor {row.get('nome', 'Desconhecido')}: {e_prod}")
        conn.commit()
        print("Dados iniciais populados (ou já existentes).")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao popular dados: {e}")

def inicializar_banco():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_dados = os.path.join(diretorio_atual, 'data')
    caminho_csv_produtores = os.path.join(caminho_dados, 'produtores.csv')
    caminho_csv_produtos = os.path.join(caminho_dados, 'produtos.csv')

    if not (os.path.exists(caminho_csv_produtores) and os.path.exists(caminho_csv_produtos)):
        print(f"Erro, arquivos CSV não encontrados em {caminho_dados}.")
        return False

    conn_init = criar_conexao()
    if conn_init:
        criar_tabelas(conn_init)
        cursor = conn_init.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            print("Populando dados iniciais...")
            popular_dados_iniciais(conn_init, caminho_csv_produtores, caminho_csv_produtos)
        else:
            print("Banco de dados já parece estar populado.")
        conn_init.close()
        return True
    return False

def get_dataframe(nome_tabela):
    """Retorna um DataFrame completo de uma tabela específica."""
    conn_df = criar_conexao()
    if conn_df is None: return pd.DataFrame()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {nome_tabela}", conn_df)
        return df
    except Exception as e:
        print(f"Erro ao obter DataFrame para {nome_tabela}: {e}")
        return pd.DataFrame()
    finally:
        if conn_df:
            conn_df.close()

def registrar_usuario(username, password):
    conn_user = criar_conexao()
    if conn_user is None: return False, "Erro de conexão."
    cursor = conn_user.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, "Nome de usuário já existe."
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (username, password)) # Senha simples
        conn_user.commit()
        return True, "Usuário registrado com sucesso!"
    except sqlite3.Error as e:
        return False, f"Erro ao registrar: {e}"
    finally:
        if conn_user: conn_user.close()

def verificar_login(username, password):
    conn_user = criar_conexao()
    if conn_user is None: return None
    cursor = conn_user.cursor()
    try:
        cursor.execute("SELECT id, username FROM usuarios WHERE username = ? AND password = ?", (username, password)) # Senha simples
        user = cursor.fetchone()
        return user # Retorna (id, username) ou None
    except sqlite3.Error as e:
        print(f"Erro ao verificar login: {e}")
        return None
    finally:
        if conn_user: conn_user.close()

def adicionar_avaliacao_db(id_usuario, id_produtor, nota, comentario):
    conn_aval = criar_conexao()
    if conn_aval is None: return False, "Erro de conexão."
    cursor = conn_aval.cursor()
    try:
        cursor.execute("INSERT INTO avaliacoes (id_usuario, id_produtor, nota, comentario) VALUES (?, ?, ?, ?)",
                       (id_usuario, id_produtor, nota, comentario))
        conn_aval.commit()
        return True, "Avaliação adicionada com sucesso!"
    except sqlite3.Error as e:
        return False, f"Erro ao adicionar avaliação: {e}"
    finally:
        if conn_aval: conn_aval.close()

if __name__ == '__main__':
    print("Inicializando o banco de dados (versão simplificada)...")
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')):
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        print(f"Diretório 'data' criado. Adicione 'produtores.csv' e 'produtos.csv'.")
    inicializar_banco()
    print("Processo de inicialização concluído.")
