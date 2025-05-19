from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Produtor, Review, Produto
from .recomendar import *
from django.db.models import Avg

def home(request):
    produtores = Produtor.objects.all()
    filtro = request.GET.get('filtro', 'todos')
    
    if request.method == 'GET' and 'latitude' in request.GET:
        lat = float(request.GET['latitude'])
        lon = float(request.GET['longitude'])
        produtores = [p[0] for p in filtro_distancia(lat, lon)]
    elif filtro == 'sazonal':
        produtores = filtro_sazonal()
    elif filtro == 'top':
        produtores = filtro_colaborativo(request.user if request.user.is_authenticated else None)
    
    if 'produtos' in request.GET:
        produtos = request.GET.getlist('produtos')
        produtores = filtro_produtos(produtos)
    
    context = {
        'produtores': produtores,
        'produtos': Produto.objects.all(),
    }
    return render(request, 'listagem.html', context)

@login_required
def detalhes_produtor(request, id):
    produtor = get_object_or_404(Produtor, pk=id)
    
    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comentario = request.POST['comentario']
        Review.objects.create(
            usuario=request.user,
            produtor=produtor,
            rating=rating,
            comentario=comentario
        )
        return redirect('detalhes_produtor', id=id)
    
    reviews = Review.objects.filter(produtor=produtor)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'produtor': produtor,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'detalhes.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})