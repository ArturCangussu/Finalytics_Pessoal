from django.urls import path
from . import views

urlpatterns = [
    # Quando o usuário visitar o endereço "raiz" do nosso app,
    # execute a view 'pagina_inicial' que criamos.
    path('', views.pagina_inicial, name='home'),
]   