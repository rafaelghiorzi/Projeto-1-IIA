from django.contrib import admin
from django.urls import path
from recomendacao import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('produtor/<int:id>/', views.detalhes_produtor, name='detalhes_produtor'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]