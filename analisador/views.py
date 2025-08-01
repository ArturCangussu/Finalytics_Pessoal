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

# Dentro de analisador/views.py

@login_required
def pagina_relatorio(request, extrato_id):
    # 1. Busca os dados do banco de dados
    extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
    transacoes = Transacao.objects.filter(extrato=extrato)

    # Se não houver transações para este extrato, renderiza o relatório com dados vazios
    if not transacoes.exists():
        contexto = {
            'extrato': extrato,
            'total_receitas': '0,00',
            'total_despesas': '0,00',
            'saldo_liquido': '0,00',
            'resumo_despesas': None,
            'resumo_receitas': None,
            'nao_categorizadas': pd.DataFrame().to_html(),
            'labels_grafico': [],
            'dados_grafico': [],
        }
        return render(request, 'analisador/relatorio.html', contexto)

    # 2. Converte para DataFrame do Pandas
    df = pd.DataFrame(list(transacoes.values('data', 'descricao', 'valor', 'topico', 'subtopico')))

    # --- CORREÇÃO PRINCIPAL AQUI ---
    # O banco de dados retorna nomes de coluna em minúsculo ('subtopico', 'valor').
    # O resto do nosso código espera os nomes com letra maiúscula ('Subtópico', 'Valor').
    # Esta linha padroniza os nomes para o formato que o resto do código precisa.
    df = df.rename(columns={
        'subtopico': 'Subtópico',
        'valor': 'Valor',
        'topico': 'Tópico',
        'descricao': 'Remetente/Destinatario',
        'data': 'Data',
    })
    # --- FIM DA CORREÇÃO ---
    
    # 3. Lógica de cálculo (agora funciona, pois os nomes das colunas estão corretos)
    df_receitas = df[df['Tópico'] == 'Receita']
    df_despesas = df[df['Tópico'] == 'Despesa']

    total_r = df_receitas['Valor'].sum()
    total_d = df_despesas['Valor'].sum()
    saldo_l = total_r - total_d

    resumo_d = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    resumo_r = df_receitas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    
    nao_cat_df = df[df['Subtópico'] == 'Não categorizado']
    colunas_desejadas = ['Tópico', 'Data', 'Remetente/Destinatario', 'Valor']
    
    # Garante que nao_cat não dê erro se estiver vazio
    if nao_cat_df.empty:
        nao_cat = pd.DataFrame(columns=colunas_desejadas)
    else:
        nao_cat = nao_cat_df[colunas_desejadas]
    
    # 4. Preparação de dados para o gráfico
    labels_grafico = list(resumo_d.index)
    dados_grafico = [float(valor) for valor in resumo_d.abs().values]
    
    print("--- DADOS PARA O GRÁFICO ---")
    print("Labels:", labels_grafico)
    print("Dados:", dados_grafico)
    print("Tipo do primeiro item de dados:", type(dados_grafico[0]) if dados_grafico else "Lista de dados vazia")
    print("----------------------------")
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

    # 6. Renderização da página
    return render(request, 'analisador/relatorio.html', contexto)

@login_required
def comparar_extratos(request):
    # Lógica para quando o usuário envia o formulário (POST)
    if request.method == 'POST':
        ids_selecionados = request.POST.getlist('extratos_selecionados')
        
        # Garante que pelo menos 2 extratos foram selecionados
        if len(ids_selecionados) < 2:
            # (No futuro, podemos adicionar uma mensagem de erro aqui)
            return redirect('comparar')

        transacoes_selecionadas = Transacao.objects.filter(extrato_id__in=ids_selecionados, usuario=request.user)
        df_transacoes = pd.DataFrame(list(transacoes_selecionadas.values('extrato__mes_referencia', 'subtopico', 'valor', 'topico')))
        
        df_transacoes = df_transacoes.rename(columns={'extrato__mes_referencia': 'mes_referencia'})
        
        # Apenas despesas
        df_despesas = df_transacoes[df_transacoes['topico'] == 'Despesa']

        # Se não houver despesas, cria uma tabela vazia para evitar erros
        if df_despesas.empty:
            tabela_comparativa = pd.DataFrame()
        else:
            tabela_comparativa = df_despesas.pivot_table(
                index='subtopico',
                columns='mes_referencia',
                values='valor',
                aggfunc='sum'
            ).fillna(0)

            # Renomeia os eixos da tabela
            tabela_comparativa = tabela_comparativa.rename_axis(index='Categoria', columns=None)

# Converte para float e DEPOIS formata para HTML
        tabela_html_formatada = tabela_comparativa.astype(float).to_html(
            classes='table table-striped',
            float_format=lambda x: f'R$ {x:,.2f}'
        )

        contexto = {
            'tabela_html': tabela_html_formatada
        }
        
        return render(request, 'analisador/relatorio_comparativo.html', contexto)

    # Lógica para quando o usuário apenas visita a página (GET)
    extratos = Extrato.objects.filter(usuario=request.user).order_by('-data_upload')
    contexto = {
        'extratos': extratos
    }
    return render(request, 'analisador/comparar.html', contexto)
