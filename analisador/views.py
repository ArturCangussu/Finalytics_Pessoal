from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from .motor_analise import processar_extrato
from decimal import Decimal
from .models import Regra, Transacao, Extrato
import pandas as pd


@login_required
def pagina_inicial(request):
    if request.method == 'POST':
        arquivo_extrato = request.FILES.get('arquivo_extrato')
        mes_referencia = request.POST.get('mes_referencia')

        if not arquivo_extrato or not mes_referencia:
            return render(request, 'analisador/pagina_inicial.html')

        # 1. Cria o objeto Extrato
        novo_extrato = Extrato.objects.create(
            usuario=request.user,
            mes_referencia=mes_referencia
        )

        # 2. Chama o motor para processar e SALVAR as transações
        processar_extrato(arquivo_extrato, request.user, novo_extrato)
        
        # 3. REDIRECIONA o usuário para a nova página de relatório
        return redirect('pagina_relatorio', extrato_id=novo_extrato.id)
    
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

@login_required
def detalhe_categoria(request, nome_categoria):
    # 1. Busca no BANCO DE DADOS as transações do usuário para a categoria específica
    transacoes = Transacao.objects.filter(
        usuario=request.user, 
        subtopico=nome_categoria
    ).order_by('data') # Ordena por data

    # 2. Prepara o contexto para enviar os dados para o template
    contexto = {
        'nome_categoria': nome_categoria,
        'transacoes': transacoes
    }

    # 3. Renderiza a nova página de detalhes
    return render(request, 'analisador/detalhe_categoria.html', contexto)

@login_required
def historico_extratos(request):
    # Busca no banco de dados todos os Extratos que pertencem ao usuário logado
    # e ordena pelos mais recentes primeiro
    extratos = Extrato.objects.filter(usuario=request.user).order_by('-data_upload')

    contexto = {
        'extratos': extratos
    }
    return render(request, 'analisador/historico.html', contexto)


# Adicione esta nova função em analisador/views.py

@login_required
def pagina_relatorio(request, extrato_id):
    # Busca o extrato específico, garantindo que ele pertence ao usuário logado
    extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
    
    # Busca todas as transações vinculadas a este extrato
    transacoes = Transacao.objects.filter(extrato=extrato)

    # Converte para DataFrame do Pandas para usar nossa lógica de cálculo
    df = pd.DataFrame(list(transacoes.values()))

    # --- Lógica de cálculo (similar à do seu motor) ---
    df_receitas = df[df['topico'] == 'Receita']
    df_despesas = df[df['topico'] == 'Despesa']

    total_r = df_receitas['valor'].sum()
    total_d = df_despesas['valor'].sum()
    saldo_l = total_r - total_d

    resumo_d = df_despesas.groupby('subtopico')['valor'].sum().sort_values(ascending=False)
    resumo_r = df_receitas.groupby('subtopico')['valor'].sum().sort_values(ascending=False)
    
    nao_cat_df = df[df['subtopico'] == 'Não categorizado']
    colunas_desejadas = ['topico', 'data', 'descricao', 'valor']
    nao_cat = nao_cat_df[colunas_desejadas]
    
    contexto = {
        'extrato': extrato,
        'total_receitas': f'{total_r:,.2f}',
        'total_despesas': f'{abs(total_d):,.2f}',
        'saldo_liquido': f'{saldo_l:,.2f}',
        'resumo_despesas': resumo_d,
        'resumo_receitas': resumo_r,
        'nao_categorizadas': nao_cat.to_html(classes='table table-striped', index=False),
    }

    return render(request, 'analisador/relatorio.html', contexto)