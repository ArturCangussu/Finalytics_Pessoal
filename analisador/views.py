from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from .motor_analise import processar_extrato
from .models import Regra, Transacao, Extrato
import pandas as pd
from django.urls import reverse
from django.contrib import messages # Importa o sistema de mensagens do Django
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404 


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

    # Lógica para ADICIONAR uma nova regra (quando o formulário é enviado via POST)
    if request.method == 'POST':
        nova_palavra = request.POST.get('palavra_chave')
        nova_categoria = request.POST.get('categoria')

        if nova_palavra and nova_categoria:
            # Assumimos que regras criadas manualmente aqui são para Despesas por padrão.
            # Você pode mudar isso ou adicionar um campo de seleção no formulário se precisar.
            Regra.objects.get_or_create(
                usuario=request.user,
                palavra_chave=nova_palavra,
                tipo_transacao='Despesa',
                defaults={'categoria': nova_categoria}
            )
        
        # Redireciona para a mesma página para evitar reenvio do formulário
        if extrato_id_origem:
            return redirect(f"{reverse('gerenciar_regras')}?from_report={extrato_id_origem}")
        return redirect('gerenciar_regras')

    # Lógica para EXIBIR as regras (quando a página é carregada via GET)
    
    # 1. Busca todas as categorias únicas que o usuário já criou para usar no filtro
    todas_as_categorias = list(
        Regra.objects.filter(usuario=request.user)
        .values_list('categoria', flat=True)
        .distinct()
        .order_by('categoria')
    )

    # 2. Verifica se o usuário selecionou uma categoria no filtro
    categoria_selecionada = request.GET.get('categoria_filtro')

    # 3. Começa com todas as regras do usuário
    regras_do_usuario = Regra.objects.filter(usuario=request.user)

    # 4. Se uma categoria foi selecionada, aplica o filtro na consulta
    if categoria_selecionada:
        regras_do_usuario = regras_do_usuario.filter(categoria=categoria_selecionada)

    contexto = {
        'regras': regras_do_usuario.order_by('palavra_chave'),
        'todas_as_categorias': todas_as_categorias,
        'categoria_selecionada': categoria_selecionada,
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


# Em analisador/views.py

@login_required
def pagina_relatorio(request, extrato_id):
    extrato = Extrato.objects.get(id=extrato_id, usuario=request.user)
    transacoes = Transacao.objects.filter(extrato=extrato)

    if not transacoes.exists():
        # ... (seu código para relatório vazio continua igual) ...
        # Adaptei o contexto vazio para já incluir as novas variáveis
        contexto = {
            'extrato': extrato, 'total_receitas': '0,00', 'total_despesas': '0,00', 'saldo_liquido': '0,00',
            'resumo_despesas': pd.DataFrame(), 'resumo_receitas': pd.DataFrame(), 'nao_categorizadas': pd.DataFrame(),
            'valor_total_despesas_detalhe': 0, 'valor_total_receitas_detalhe': 0,
            'labels_grafico': [], 'dados_grafico': [],
            'labels_grafico_receitas': [], 'dados_grafico_receitas': [] # (NOVO)
        }
        return render(request, 'analisador/relatorio.html', contexto)

    categorias_existentes = list(Regra.objects.filter(
        usuario=request.user
    ).values_list('categoria', flat=True).distinct().order_by('categoria'))

    df = pd.DataFrame(list(transacoes.values('data', 'descricao', 'valor', 'topico', 'subtopico')))
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # --- LÓGICA DE LIMPEZA (igual a sua) ---
    def _limpar_descricao_inteligente(descricao):
        if pd.isna(descricao) or not str(descricao).strip():
            return str(descricao)
        descricao_str = str(descricao)
        try:
            parts = descricao_str.split(' - ')
            if len(parts) > 1:
                for part in parts[1:]:
                    if not any(char.isdigit() for char in part[:4]):
                        return part.strip()
                return parts[1].strip()
        except:
            pass
        return descricao_str
    df['DescricaoLimpa'] = df['descricao'].apply(_limpar_descricao_inteligente)
    # --- FIM DA LÓGICA DE LIMPEZA ---

    df = df.rename(columns={
        'subtopico': 'Subtópico', 'valor': 'Valor', 'topico': 'Tópico',
        'descricao': 'Remetente/Destinatario', 'data': 'Data',
    })
    
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    
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
    nao_cat_df = nao_cat_df.rename(columns={'DescricaoLimpa': 'Remetente_Destinatario'})
    colunas_desejadas = ['Tópico', 'Data', 'Remetente_Destinatario', 'Valor']
    
    if nao_cat_df.empty:
        nao_cat = pd.DataFrame(columns=colunas_desejadas)
    else:
        nao_cat = nao_cat_df[colunas_desejadas]
    
    # Dados para o gráfico de Despesas (existente)
    labels_grafico = list(resumo_d_series.index)
    dados_grafico = [float(valor) for valor in resumo_d_series.abs().values]

    # Dados para o gráfico de Receitas (NOVO)
    labels_grafico_receitas = list(resumo_r_series.index)
    dados_grafico_receitas = [float(valor) for valor in resumo_r_series.abs().values]
    
    contexto = {
        'extrato': extrato,
        'total_receitas': f'{total_r:,.2f}',
        'total_despesas': f'{abs(total_d):,.2f}',
        'saldo_liquido': f'{saldo_l:,.2f}',
        'resumo_despesas': resumo_d,
        'resumo_receitas': resumo_r,
        'nao_categorizadas': nao_cat,
        'valor_total_despesas_detalhe': total_d,
        'valor_total_receitas_detalhe': total_r,
        'labels_grafico': labels_grafico,
        'dados_grafico': dados_grafico,
        'labels_grafico_receitas': labels_grafico_receitas,
        'dados_grafico_receitas': dados_grafico_receitas,
        'categorias_existentes': categorias_existentes,
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
    """
    Reprocessa as transações de um extrato, aplicando as regras mais recentes
    de forma inteligente (considerando palavra-chave E tipo de transação).
    """
    # Pega as regras do usuário como uma lista de dicionários para performance
    regras_do_usuario = list(Regra.objects.filter(usuario=request.user).values())

    def categorizar_transacao_inteligente(descricao, topico):
        """Função interna que busca a melhor regra para uma transação."""
        if not isinstance(descricao, str):
            return 'Não categorizado'
        
        # Procura por uma regra que combine a palavra-chave E o tipo
        for regra in regras_do_usuario:
            if regra['palavra_chave'].lower() in descricao.lower() and regra['tipo_transacao'] == topico:
                return regra['categoria']
            
        return 'Não categorizado'

    # Busca todas as transações do extrato que não foram travadas manualmente
    transacoes_para_atualizar = Transacao.objects.filter(
        extrato_id=extrato_id, 
        usuario=request.user,
        categorizacao_manual=False
    )

    # Itera sobre cada transação para reavaliar sua categoria
    for transacao in transacoes_para_atualizar:
        # Chama a função de categorização passando a descrição E o tópico
        transacao.subtopico = categorizar_transacao_inteligente(transacao.descricao, transacao.topico)
        transacao.save()

    messages.success(request, "O relatório foi reprocessado com sucesso usando as regras atualizadas!")
    return redirect('pagina_relatorio', extrato_id=extrato_id)




@login_required
def criar_regra_rapida(request):
    if request.method == 'POST':
        palavra_chave = request.POST.get('palavra_chave')
        categoria = request.POST.get('categoria')
        extrato_id = request.POST.get('extrato_id')
        tipo_transacao = request.POST.get('tipo_transacao') # NOVO

        if palavra_chave and categoria and tipo_transacao:
            # get_or_create agora também verifica o tipo_transacao
            Regra.objects.get_or_create(
                usuario=request.user,
                palavra_chave=palavra_chave,
                tipo_transacao=tipo_transacao, # NOVO
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


@login_required
def editar_regra(request, regra_id):
    # Busca a regra específica, garantindo que pertence ao usuário
    regra = Regra.objects.get(id=regra_id, usuario=request.user)

    if request.method == 'POST':
        # Pega os novos dados do formulário
        regra.palavra_chave = request.POST.get('palavra_chave')
        regra.categoria = request.POST.get('categoria')
        regra.save() # Salva as alterações
        return redirect('gerenciar_regras')

    contexto = {
        'regra': regra,
        'active_page': 'regras'
    }
    return render(request, 'analisador/editar_regra.html', contexto)


@login_required
def apagar_regra(request, regra_id):
    if request.method == 'POST':
        regra = Regra.objects.get(id=regra_id, usuario=request.user)
        regra.delete()
    return redirect('gerenciar_regras')



@login_required
def editar_transacao(request, transacao_id):
    # Usamos get_object_or_404 para mais segurança. Se a transação não existe, dá erro 404.
    transacao = get_object_or_404(Transacao, id=transacao_id, usuario=request.user)

    if request.method == 'POST':
        novo_subtopico = request.POST.get('subtopico')
        
        if novo_subtopico:
            # --- Passo 1: Atualiza a transação individual (como já fazia) ---
            transacao.subtopico = novo_subtopico
            transacao.categorizacao_manual = True # Continua travando para garantir
            transacao.save()
            
            # --- Passo 2 (LÓGICA NOVA): Atualiza ou cria a regra correspondente ---
            
            # Usamos a propriedade 'descricao_limpa' do modelo para pegar a palavra-chave ideal
            palavra_chave = transacao.descricao_limpa
            
            # Usamos update_or_create:
            # Ele tenta encontrar uma Regra com essa palavra_chave e tipo.
            # Se encontrar, atualiza a 'categoria'.
            # Se não encontrar, cria uma nova regra com esses dados.
            Regra.objects.update_or_create(
                usuario=request.user,
                palavra_chave=palavra_chave,
                tipo_transacao=transacao.topico,
                defaults={'categoria': novo_subtopico}
            )
            
            messages.success(request, f"Transação atualizada! A regra para '{palavra_chave}' agora aponta para '{novo_subtopico}'.")
        
        # Redireciona de volta para o relatório original para ver o resultado
        return redirect('pagina_relatorio', extrato_id=transacao.extrato.id)

    # A lógica para GET (mostrar o formulário) continua a mesma
    contexto = {
        'transacao': transacao,
        # Adiciona categorias existentes para sugestão também na página de edição
        'categorias_existentes': list(Regra.objects.filter(usuario=request.user).values_list('categoria', flat=True).distinct().order_by('categoria'))
    }
    return render(request, 'analisador/editar_transacao.html', contexto)





def cadastro_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario) # Loga o usuário automaticamente após o cadastro
            return redirect('home') # Redireciona para a página inicial
    else:
        form = UserCreationForm()
    
    contexto = {
        'form': form
    }
    return render(request, 'analisador/cadastro.html', contexto)



@login_required
def criar_regras_em_lote(request):
    if request.method == 'POST':
        # Cada item agora é "palavra|tipo"
        palavras_chave_com_tipo = request.POST.getlist('palavras_chave_selecionadas') 
        nova_categoria = request.POST.get('categoria_em_lote')
        extrato_id = request.POST.get('extrato_id')

        if palavras_chave_com_tipo and nova_categoria and extrato_id:
            regras_criadas = 0
            for item in palavras_chave_com_tipo:
                try:
                    # Separa a palavra_chave do tipo
                    palavra, tipo = item.split('|')
                    
                    Regra.objects.get_or_create(
                        usuario=request.user,
                        palavra_chave=palavra,
                        tipo_transacao=tipo, # NOVO
                        defaults={'categoria': nova_categoria}
                    )
                    regras_criadas += 1
                except ValueError:
                    # Ignora itens mal formatados, se houver
                    continue
            
            messages.success(request, f'{regras_criadas} regras foram criadas/atualizadas com a categoria "{nova_categoria}".')
            return redirect('reprocessar_relatorio', extrato_id=extrato_id)

    messages.error(request, 'Ocorreu um erro ao processar a solicitação em lote.')
    return redirect('home')