from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='home'),
    path('regras/', views.gerenciar_regras, name='gerenciar_regras'),
]   