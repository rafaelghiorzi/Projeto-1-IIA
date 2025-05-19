from geopy.distance import geodesic
from datetime import datetime
from .models import Produtor, Produto

# Filtro por Distância
def filtro_distancia(lat_user, lon_user, raio_km=10):
    produtores = []
    for p in Produtor.objects.all():
        distancia = geodesic((lat_user, lon_user), (p.lat, p.lon)).km
        if distancia <= raio_km:
            produtores.append((p, distancia))
    return sorted(produtores, key=lambda x: x[1])

# Filtro por Produtos
def filtro_produtos(produtos_desejados):
    return Produtor.objects.filter(produtos__nome__in=produtos_desejados).distinct()

# Filtro Colaborativo (Simples)
def filtro_colaborativo(usuario):
    # Implementação básica baseada em avaliações
    return Produtor.objects.filter(review__rating__gte=4).distinct()

# Filtro Sazonal
def filtro_sazonal():
    estacoes = {
        1: 'Verão', 2: 'Verão', 3: 'Outono',
        4: 'Outono', 5: 'Outono', 6: 'Inverno',
        7: 'Inverno', 8: 'Inverno', 9: 'Primavera',
        10: 'Primavera', 11: 'Primavera', 12: 'Verão'
    }
    estacao_atual = estacoes[datetime.now().month]
    produtos = Produto.objects.filter(sazonalidade=estacao_atual)
    return Produtor.objects.filter(produtos__in=produtos).distinct()