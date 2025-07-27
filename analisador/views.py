from django.shortcuts import render
from django.contrib.auth.decorators import login_required # O segurança que adicionamos
from .motor_analise import processar_extrato
from decimal import Decimal

@login_required # <-- Página protegida!
def pagina_inicial(request):
    if request.method == 'POST':
        arquivo_extrato = request.FILES.get('arquivo_extrato')

        if not arquivo_extrato:
            return render(request, 'analisador/pagina_inicial.html')

        # --- MUDANÇA PRINCIPAL AQUI ---
        # Não pedimos mais o arquivo de regras.
        # Passamos o usuário logado (request.user) para a função.
        total_r, total_d, saldo_l, resumo_d, nao_cat = processar_extrato(arquivo_extrato, request.user)


        # O resto do código continua igual...
        resumo_formatado = resumo_d.abs().astype(float).to_string(
            header=False,
            float_format='R$ {:>10,.2f}'.format
        )
        
        contexto = {
            'total_receitas': f'{total_r:,.2f}',
            'total_despesas': f'{abs(total_d):,.2f}',
            'saldo_liquido': f'{saldo_l:,.2f}',
            'resumo_despesas': resumo_formatado.replace('\n', '<br>'),
            'nao_categorizadas': nao_cat.to_html(classes='table table-striped', index=False)
        }

        return render(request, 'analisador/relatorio.html', contexto)
    
    return render(request, 'analisador/pagina_inicial.html')