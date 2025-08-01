from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='home'),
    path('regras/', views.gerenciar_regras, name='gerenciar_regras'),
    path('relatorio/<int:extrato_id>/categoria/<str:nome_categoria>/', views.detalhe_categoria, name='detalhe_categoria'),
    path('historico/', views.historico_extratos, name='historico'),
    path('relatorio/<int:extrato_id>/', views.pagina_relatorio, name='pagina_relatorio'),
    path('comparar/', views.comparar_extratos, name='comparar'),    
]   