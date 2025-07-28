from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from .motor_analise import processar_extrato
from decimal import Decimal
from .models import Regra
@login_required # <-- Página protegida!
def pagina_inicial(request):
    if request.method == 'POST':
        arquivo_extrato = request.FILES.get('arquivo_extrato')
        if not arquivo_extrato:
            return render(request, 'analisador/pagina_inicial.html')

        # Chama o motor de análise para pegar os 6 resultados
        total_r, total_d, saldo_l, resumo_d, nao_cat, resumo_r = processar_extrato(arquivo_extrato, request.user)

        # --- CORREÇÃO AQUI ---

        # 1. Formatando as DESPESAS
        resumo_d_formatado = resumo_d.abs().astype(float).to_string(
            header=False,
            float_format='R$ {:>10,.2f}'.format
        )

        # 2. Formatando as RECEITAS
        resumo_r_formatado = resumo_r.abs().astype(float).to_string(
            header=False,
            float_format='R$ {:>10,.2f}'.format
        )

        # 3. Montando o contexto com os NOMES CORRETOS
        contexto = {
            'total_receitas': f'{total_r:,.2f}',
            'total_despesas': f'{abs(total_d):,.2f}',
            'saldo_liquido': f'{saldo_l:,.2f}',
            'resumo_despesas': resumo_d_formatado.replace('\n', '<br>'),
            'resumo_receitas': resumo_r_formatado.replace('\n', '<br>'),
            'nao_categorizadas': nao_cat.to_html(classes='table table-striped', index=False),
        }

        # Renderiza a página de relatório com o contexto completo
        return render(request, 'analisador/relatorio.html', contexto)
    return render(request, 'analisador/pagina_inicial.html')


@login_required
def gerenciar_regras(request):
    # --- LÓGICA PARA ADICIONAR NOVA REGRA (POST) ---
    if request.method == 'POST':
        
        nova_palavra = request.POST.get('palavra_chave')
        nova_categoria = request.POST.get('categoria')

        # 3. Cria a nova regra no banco de dados, associada ao usuário logado
        if nova_palavra and nova_categoria: # Garante que os campos não estão vazios
            Regra.objects.create(
                usuario=request.user,
                palavra_chave=nova_palavra,
                categoria=nova_categoria
            )
        
        # 4. Redireciona para a mesma página (para mostrar a lista atualizada)
        return redirect('gerenciar_regras')

    regras_do_usuario = Regra.objects.filter(usuario=request.user)
    contexto = {
        'regras': regras_do_usuario
    }
    return render(request, 'analisador/gerenciar_regras.html', contexto)