from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    sazonalidade = models.CharField(max_length=50)
    descricao = models.TextField()

class Produtor(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=200)
    lat = models.FloatField()
    lon = models.FloatField()
    produtos = models.ManyToManyField(Produto)

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)
    data_cadastro = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    produtor = models.ForeignKey(Produtor, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comentario = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

