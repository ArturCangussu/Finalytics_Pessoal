from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='home'),
    path('regras/', views.gerenciar_regras, name='gerenciar_regras'),
    path('historico/', views.historico_extratos, name='historico'),
    path('comparar/', views.comparar_extratos, name='comparar'),
    path('relatorio/<int:extrato_id>/', views.pagina_relatorio, name='pagina_relatorio'),
    path('relatorio/<int:extrato_id>/reprocessar/', views.reprocessar_relatorio, name='reprocessar_relatorio'),
    path('relatorio/<int:extrato_id>/categoria/<str:nome_categoria>/', views.detalhe_categoria, name='detalhe_categoria'),
    path('regras/criar-rapido/', views.criar_regra_rapida, name='criar_regra_rapida'),
    path('historico/apagar/<int:extrato_id>/', views.apagar_extrato, name='apagar_extrato'),
]
