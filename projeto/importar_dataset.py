import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')  # ajuste 'projeto' para o nome do seu projeto Django
django.setup()


import pandas as pd
from recomendacao.models import Produtor, Produto
from django.contrib.auth.models import User

def importar_produtores():
    df = pd.read_csv('D:/estudo - UnB/IIA/projeto/produtores.csv')
    
    for _, row in df.iterrows():       
        produtor = Produtor.objects.create(
            nome=row['nome'],
            sigla=row['sigla'],
            lat=row['lat'],
            lon=row['lon']
        )
        
        for produto_col in df.columns[5:]:  # Colunas de produtos
            if str(row[produto_col]).strip().lower() == "true":
                produto, _ = Produto.objects.get_or_create(nome=produto_col)
                produtor.produtos.add(produto)

def importar_produtos():
    df = pd.read_csv('D:/estudo - UnB/IIA/projeto/produtos.csv')
    
    for _, row in df.iterrows():
        Produto.objects.create(
            nome=row['nome'],
            sazonalidade=row['sazonalidade (estação do ano)'],
            descricao=row['descrição pequena']
        )

if __name__ == '__main__':
    importar_produtos()
    importar_produtores()