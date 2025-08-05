from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from .motor_analise import processar_extrato
from .models import Regra, Transacao, Extrato
import pandas as pd
from django.urls import reverse
from django.contrib import messages # Importa o sistema de mensagens do Django

@login_required
def pagina_inicial(request):
    contexto = {'active_page': 'home'}

    if request.method == 'POST':
        arquivo_extrato = request.FILES.get('arquivo_extrato')
        mes_referencia = request.POST.get('mes_referencia')

        if not arquivo_extrato or not mes_referencia:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'analisador/pagina_inicial.html', contexto)
        
        # --- VALIDAÇÃO DO TIPO DE ARQUIVO ---
        # Verifica se o nome do arquivo termina com .xlsx
        if not arquivo_extrato.name.endswith('.xlsx'):
            messages.error(request, 'Erro: O arquivo do extrato deve ser no formato .xlsx.')
            return render(request, 'analisador/pagina_inicial.html', contexto)
        # --- FIM DA VALIDAÇÃO ---

        novo_extrato = Extrato.objects.create(
            usuario=request.user,
            mes_referencia=mes_referencia
        )
        processar_extrato(arquivo_extrato, request.user, novo_extrato)
        
        return redirect('pagina_relatorio', extrato_id=novo_extrato.id)
    
    return render(request, 'analisador/pagina_inicial.html', contexto)


@login_required
def gerenciar_regras(request):
    extrato_id_origem = request.GET.get('from_report')

    if request.method == 'POST':
        nova_palavra = request.POST.get('palavra_chave')
        nova_categoria = request.POST.get('categoria')

        if nova_palavra and nova_categoria:
            Regra.objects.create(
                usuario=request.user,
                palavra_chave=nova_palavra,
                categoria=nova_categoria
            )
        
        if extrato_id_origem:
            return redirect(f"{reverse('gerenciar_regras')}?from_report={extrato_id_origem}")
        return redirect('gerenciar_regras')

    regras_do_usuario = Regra.objects.filter(usuario=request.user)
    contexto = {
        'regras': regras_do_usuario,
        'active_page': 'regras',
        'extrato_id_origem': extrato_id_origem
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
    # 1. Busca os dados base do banco de dados
    extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
    transacoes_qs = Transacao.objects.filter(extrato=extrato)

    # --- INÍCIO DA LÓGICA DE FILTRAGEM ---

    # 2. Pega os parâmetros de filtro da URL (ex: /?q=mercado)
    search_query = request.GET.get('q', '')
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')

    # 3. Converte o QuerySet para DataFrame para facilitar a manipulação
    df = pd.DataFrame(list(transacoes_qs.values('data', 'descricao', 'valor', 'topico', 'subtopico')))

    # Se o DataFrame estiver vazio, renderiza um relatório vazio
    if df.empty:
        contexto = {
            'extrato': extrato, 'total_receitas': '0,00', 'total_despesas': '0,00',
            'saldo_liquido': '0,00', 'resumo_despesas': None, 'resumo_receitas': None,
            'nao_categorizadas': pd.DataFrame(), 'labels_grafico': [], 'dados_grafico': [],
            'search_query': search_query, 'data_inicio': data_inicio_str, 'data_fim': data_fim_str,
        }
        return render(request, 'analisador/relatorio.html', contexto)

    # 4. Prepara a coluna de data para a filtragem
    df['data_dt'] = pd.to_datetime(df['data'])

    # 5. Aplica os filtros no DataFrame
    if search_query:
        df = df[df['descricao'].str.contains(search_query, case=False, na=False)]
    
    if data_inicio_str:
        df = df[df['data_dt'] >= pd.to_datetime(data_inicio_str)]

    if data_fim_str:
        df = df[df['data_dt'] <= pd.to_datetime(data_fim_str)]

    # --- FIM DA LÓGICA DE FILTRAGEM ---

    # O resto do código agora opera sobre o 'df' já filtrado
    df = df.rename(columns={
        'subtopico': 'Subtópico', 'valor': 'Valor', 'topico': 'Tópico',
        'descricao': 'Remetente/Destinatario', 'data': 'Data',
    })
    
    df['Data'] = df['data_dt'].dt.strftime('%d/%m/%Y')
    
    # ... (O resto dos seus cálculos de totais, resumos, etc. continua aqui) ...
    df_receitas = df[df['Tópico'] == 'Receita']
    df_despesas = df[df['Tópico'] == 'Despesa']
    total_r = df_receitas['Valor'].sum()
    total_d = df_despesas['Valor'].sum()
    saldo_l = total_r - total_d
    resumo_d_series = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    resumo_d = resumo_d_series.reset_index()
    resumo_r_series = df_receitas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    resumo_r = resumo_r_series.reset_index()
    nao_cat_df = df[df['Subtópico'] == 'Não categorizado'].copy()
    colunas_desejadas = ['Tópico', 'Data', 'Remetente/Destinatario', 'Valor']
    if nao_cat_df.empty:
        nao_cat = pd.DataFrame(columns=colunas_desejadas)
    else:
        nao_cat = nao_cat_df[colunas_desejadas].rename(columns={'Remetente/Destinatario': 'Remetente_Destinatario'})
    
    labels_grafico = list(resumo_d_series.index)
    dados_grafico = [float(valor) for valor in resumo_d_series.abs().values]
    
    # 6. Passa os valores dos filtros de volta para o template
    contexto = {
        'extrato': extrato,
        'total_receitas': f'{total_r:,.2f}',
        'total_despesas': f'{abs(total_d):,.2f}',
        'saldo_liquido': f'{saldo_l:,.2f}',
        'resumo_despesas': resumo_d,
        'resumo_receitas': resumo_r,
        'nao_categorizadas': nao_cat,
        'labels_grafico': labels_grafico,
        'dados_grafico': dados_grafico,
        'search_query': search_query,
        'data_inicio': data_inicio_str,
        'data_fim': data_fim_str,
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

@login_required
def reprocessar_relatorio(request, extrato_id):
    regras_do_usuario = Regra.objects.filter(usuario=request.user)
    regras_de_categorizacao = {
        regra.palavra_chave: regra.categoria for regra in regras_do_usuario
    }

    def categorizar_transacao(descricao):
        if not isinstance(descricao, str):
            return 'Descrição Inválida'
        for palavra_chave, categoria in regras_de_categorizacao.items():
            if palavra_chave.lower() in descricao.lower():
                return categoria
        return 'Não categorizado'

    transacoes_para_atualizar = Transacao.objects.filter(extrato_id=extrato_id, usuario=request.user)

    for transacao in transacoes_para_atualizar:
        transacao.subtopico = categorizar_transacao(transacao.descricao)
        transacao.save()

    return redirect('pagina_relatorio', extrato_id=extrato_id)

@login_required
def criar_regra_rapida(request):
    if request.method == 'POST':
        palavra_chave = request.POST.get('palavra_chave')
        categoria = request.POST.get('categoria')
        extrato_id = request.POST.get('extrato_id')

        if palavra_chave and categoria:
            Regra.objects.get_or_create(
                usuario=request.user,
                palavra_chave=palavra_chave,
                defaults={'categoria': categoria}
            )
        
        if extrato_id:
            return redirect('reprocessar_relatorio', extrato_id=extrato_id)

    return redirect('home')

@login_required
def apagar_extrato(request, extrato_id):
    if request.method == 'POST':
        extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
        extrato.delete()
    
    return redirect('historico')
