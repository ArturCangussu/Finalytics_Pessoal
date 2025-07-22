from django.shortcuts import render
from .motor_analise import processar_extrato  # Importa nossa função!
from decimal import Decimal # Importamos para formatar os números

def pagina_inicial(request):
    # Verifica se o formulário foi enviado (método POST)
    if request.method == 'POST':
        # 1. Pega os arquivos que o usuário enviou
        arquivo_extrato = request.FILES.get('arquivo_extrato')
        arquivo_regras = request.FILES.get('arquivo_regras')

        # Se os arquivos não foram enviados, apenas recarrega a página de upload
        if not arquivo_extrato or not arquivo_regras:
            return render(request, 'analisador/pagina_inicial.html')

        # 2. Chama nossa função do motor_analise para processar os arquivos
        total_r, total_d, saldo_l, resumo_d = processar_extrato(arquivo_extrato, arquivo_regras)

        # 3. Formata o resumo para exibição na página
        resumo_formatado = resumo_d.abs().astype(float).to_string(
            header=False,
            float_format='R$ {:>10,.2f}'.format
        )
        
        # 4. Prepara o "contexto" com os resultados para enviar à página de relatório
        contexto = {
            'total_receitas': f'{total_r:,.2f}',
            'total_despesas': f'{abs(total_d):,.2f}',
            'saldo_liquido': f'{saldo_l:,.2f}',
            'resumo_despesas': resumo_formatado.replace('\n', '<br>')
        }

        # 5. Renderiza a PÁGINA DE RELATÓRIO com os resultados
        return render(request, 'analisador/relatorio.html', contexto)
    
    # Se não for POST, significa que o usuário está apenas visitando a página
    # Então, apenas mostramos o formulário de upload
    return render(request, 'analisador/pagina_inicial.html')