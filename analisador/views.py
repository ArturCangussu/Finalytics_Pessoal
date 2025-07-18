from django.http import HttpResponse

# Esta é a nossa primeira view.
# Toda view recebe um 'request' como primeiro argumento.
def pagina_inicial(request):
    # A view deve retornar uma 'HttpResponse'.
    # Aqui, estamos retornando um texto simples em HTML.
    return HttpResponse("<h1>Analisador Financeiro</h1><p>Bem-vindo à página inicial do seu projeto!</p>")