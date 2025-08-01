from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from .motor_analise import processar_extrato
from .models import Regra, Transacao, Extrato
import pandas as pd


@login_required
def pagina_inicial(request):
    # Prepara o contexto para a página ativa desde o início
    contexto = {'active_page': 'home'}

    if request.method == 'POST':
        arquivo_extrato = request.FILES.get('arquivo_extrato')
        mes_referencia = request.POST.get('mes_referencia')

        if not arquivo_extrato or not mes_referencia:
            # Se der erro, renderiza a página de novo, mas com o contexto
            return render(request, 'analisador/pagina_inicial.html', contexto)

        novo_extrato = Extrato.objects.create(
            usuario=request.user,
            mes_referencia=mes_referencia
        )
        processar_extrato(arquivo_extrato, request.user, novo_extrato)
        
        return redirect('pagina_relatorio', extrato_id=novo_extrato.id)
    
    # Se for GET, renderiza a página com o contexto
    return render(request, 'analisador/pagina_inicial.html', contexto)


@login_required
def gerenciar_regras(request):
    if request.method == 'POST':
        nova_palavra = request.POST.get('palavra_chave')
        nova_categoria = request.POST.get('categoria')

        if nova_palavra and nova_categoria:
            Regra.objects.create(
                usuario=request.user,
                palavra_chave=nova_palavra,
                categoria=nova_categoria
            )
        
        return redirect('gerenciar_regras')

    regras_do_usuario = Regra.objects.filter(usuario=request.user)
    contexto = {
        'regras': regras_do_usuario,
        'active_page': 'regras' # Garante que o valor correto é 'regras'
    }
    return render(request, 'analisador/gerenciar_regras.html', contexto)


@login_required
def detalhe_categoria(request, extrato_id, nome_categoria):
    extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
    transacoes = Transacao.objects.filter(
        extrato_id=extrato_id, 
        usuario=request.user, 
        subtopico=nome_categoria
    ).order_by('data')

    contexto = {
        'extrato': extrato,
        'nome_categoria': nome_categoria,
        'transacoes': transacoes
    }
    return render(request, 'analisador/detalhe_categoria.html', contexto)


@login_required
def historico_extratos(request):
    extratos = Extrato.objects.filter(usuario=request.user).order_by('-data_upload')
    contexto = {
        'extratos': extratos,
        'active_page': 'historico'
    }
    return render(request, 'analisador/historico.html', contexto)


@login_required
def pagina_relatorio(request, extrato_id):
    extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
    transacoes = Transacao.objects.filter(extrato=extrato)

    if not transacoes.exists():
        contexto = {
            'extrato': extrato, 'total_receitas': '0,00', 'total_despesas': '0,00',
            'saldo_liquido': '0,00', 'resumo_despesas': None, 'resumo_receitas': None,
            'nao_categorizadas': pd.DataFrame().to_html(), 'labels_grafico': [], 'dados_grafico': [],
        }
        return render(request, 'analisador/relatorio.html', contexto)

    df = pd.DataFrame(list(transacoes.values('data', 'descricao', 'valor', 'topico', 'subtopico')))
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df = df.rename(columns={
        'subtopico': 'Subtópico', 'valor': 'Valor', 'topico': 'Tópico',
        'descricao': 'Remetente/Destinatario', 'data': 'Data',
    })
    
    df_receitas = df[df['Tópico'] == 'Receita']
    df_despesas = df[df['Tópico'] == 'Despesa']

    total_r = df_receitas['Valor'].sum()
    total_d = df_despesas['Valor'].sum()
    saldo_l = total_r - total_d

    resumo_d_series = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    resumo_d = resumo_d_series.reset_index()
    
    resumo_r_series = df_receitas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    resumo_r = resumo_r_series.reset_index()
    
    nao_cat_df = df[df['Subtópico'] == 'Não categorizado']
    colunas_desejadas = ['Tópico', 'Data', 'Remetente/Destinatario', 'Valor']
    
    if nao_cat_df.empty:
        nao_cat = pd.DataFrame(columns=colunas_desejadas)
    else:
        nao_cat = nao_cat_df[colunas_desejadas]
    
    labels_grafico = list(resumo_d_series.index)
    dados_grafico = [float(valor) for valor in resumo_d_series.abs().values]
    
    contexto = {
        'extrato': extrato,
        'total_receitas': f'{total_r:,.2f}',
        'total_despesas': f'{abs(total_d):,.2f}',
        'saldo_liquido': f'{saldo_l:,.2f}',
        'resumo_despesas': resumo_d,
        'resumo_receitas': resumo_r,
        'nao_categorizadas': nao_cat.to_html(classes='table table-striped', index=False),
        'labels_grafico': labels_grafico,
        'dados_grafico': dados_grafico,
    }

    return render(request, 'analisador/relatorio.html', contexto)


@login_required
def comparar_extratos(request):
    if request.method == 'POST':
        ids_selecionados = request.POST.getlist('extratos_selecionados')
        
        if len(ids_selecionados) < 2:
            return redirect('comparar')

        transacoes_selecionadas = Transacao.objects.filter(extrato_id__in=ids_selecionados, usuario=request.user)
        df_transacoes = pd.DataFrame(list(transacoes_selecionadas.values('extrato__mes_referencia', 'subtopico', 'valor', 'topico')))
        
        df_transacoes = df_transacoes.rename(columns={'extrato__mes_referencia': 'mes_referencia'})
        df_despesas = df_transacoes[df_transacoes['topico'] == 'Despesa']

        if df_despesas.empty:
            tabela_comparativa = pd.DataFrame()
        else:
            tabela_comparativa = df_despesas.pivot_table(
                index='subtopico',
                columns='mes_referencia',
                values='valor',
                aggfunc='sum'
            ).fillna(0)
            tabela_comparativa = tabela_comparativa.rename_axis(index='Categoria', columns=None)
        
        tabela_html_formatada = tabela_comparativa.astype(float).to_html(
            classes='table table-striped',
            float_format=lambda x: f'R$ {x:,.2f}'
        )

        contexto = {
            'tabela_html': tabela_html_formatada
        }
        
        return render(request, 'analisador/relatorio_comparativo.html', contexto)

    extratos = Extrato.objects.filter(usuario=request.user).order_by('-data_upload')
    contexto = {
        'extratos': extratos,
        'active_page': 'comparar'
    }
    return render(request, 'analisador/comparar.html', contexto)