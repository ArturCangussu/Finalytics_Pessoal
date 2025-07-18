from django.shortcuts import render

# Não precisamos mais do HttpResponse aqui, então podemos remover.

def pagina_inicial(request):
    # Trocamos HttpResponse por render.
    # O render precisa do 'request' e do caminho para o arquivo HTML.
    return render(request, 'analisador/pagina_inicial.html')