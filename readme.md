# Busca de Produtores Locais

Projeto desenvolvido para a disciplina de Introdução à Inteligência Artificial que usa um sistema de recomendação baseado em KNN (K-Nearest Neighbors) para sugerir produtores locais aos usuários.

## Descrição

Esta aplicação web permite aos usuários:
- Filtrar produtores locais por distância, produtos e sazonalidade
- Visualizar os produtores em um mapa interativo
- Receber recomendações personalizadas de produtores
- Consultar informações detalhadas e avaliações de produtores

## Pré-requisitos

- Python 3.8 ou superior
- Git (opcional, para clonar o repositório)

## Instalação

1. Clone o repositório ou faça o download do código:
```bash
git clone https://github.com/rafaelghiorzi/Projeto-1-IIA
cd IIA
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
   - No Windows:
   ```bash
   venv\Scripts\activate
   ```
   - No macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. Instale as dependências necessárias:
```bash
pip install streamlit pandas folium streamlit-folium sqlalchemy geopy scikit-learn
```

## Execução

1. Certifique-se de que o banco de dados (`db.db`) esteja na raiz do projeto. Caso não esteja, execute o arquivo db.py antes de iniciar a aplicação

2. Execute a aplicação Streamlit:
```bash
streamlit run app.py
```

3. A aplicação será aberta automaticamente no seu navegador padrão. Se isso não acontecer, acesse:
```
http://localhost:8501
```

## Utilizando a Aplicação

A aplicação está organizada em três páginas principais:

1. **Filtros e Mapa de Produtores**
   - Defina sua localização (latitude/longitude)
   - Ajuste o raio de busca
   - Selecione produtos desejados
   - Escolha filtrar por sazonalidade
   - Visualize os resultados em mapa e tabela

2. **Recomendações Personalizadas**
   - Clique em "Buscar/Atualizar Recomendações" para obter sugestões personalizadas
   - Visualize as recomendações no mapa e na tabela de detalhes

3. **Buscar Produtores e Avaliações**
   - Selecione um produtor específico para ver detalhes
   - Consulte avaliações e produtos ofertados
   - Veja suas próprias avaliações de produtores

## Estrutura do Projeto

- `app.py`: Interface do usuário construída com Streamlit
- `back.py`: Lógica de negócios, incluindo filtros e sistema de recomendação
- `db.py`: Definições e modelos do banco de dados
- `db.db`: Banco de dados SQLite

## Técnicas de IA Utilizadas

- **KNN (K-Nearest Neighbors)**: Algoritmo utilizado para recomendar produtores com base em padrões de avaliação semelhantes entre usuários.
- **Sistemas de Recomendação Colaborativa**: Recomendações baseadas nas preferências e comportamentos de usuários similares.
