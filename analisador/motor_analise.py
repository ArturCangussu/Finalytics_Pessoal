import pandas as pd
import numpy as np
from .models import Regra, Transacao, Extrato

def processar_extrato(arquivo_extrato, usuario_logado, extrato_obj):
    
    # --- PARTE 1: LEITURA E PREPARAÇÃO ---
    df = pd.read_excel(arquivo_extrato)
    
    regras_do_usuario = Regra.objects.filter(usuario=usuario_logado)
    regras_de_categorizacao = {
        regra.palavra_chave: regra.categoria for regra in regras_do_usuario
    }

    # --- PARTE 2: FILTRAGEM ---
    df_filtrado = df[df['Situacao'] == 'EFETIVADA']
    df_filtrado = df_filtrado.copy()

    # --- PARTE 3: LIMPEZA E CATEGORIZAÇÃO ---
    
    # Garante que a coluna 'Valor' seja tratada como texto para limpeza
    df_filtrado['Valor'] = df_filtrado['Valor'].astype(str)
    
    # Limpeza robusta usando métodos de string do pandas (.str)
    df_filtrado['Valor'] = df_filtrado['Valor'].str.replace('R$', '', regex=False)
    df_filtrado['Valor'] = df_filtrado['Valor'].str.replace('.', '', regex=False)
    df_filtrado['Valor'] = df_filtrado['Valor'].str.replace(',', '.', regex=False)
    df_filtrado['Valor'] = df_filtrado['Valor'].str.strip()

    # Conversão final para tipo numérico, forçando erros a virarem Nulo (NaN)
    df_filtrado['Valor'] = pd.to_numeric(df_filtrado['Valor'], errors='coerce')
    df_filtrado['Valor'] = df_filtrado['Valor'].fillna(0) # Substitui Nulos por 0

    # Definição da função de categorização
    def categorizar_transacao(descricao):
        if not isinstance(descricao, str):
            return 'Descrição Inválida'
        for palavra_chave, categoria in regras_de_categorizacao.items():
            if palavra_chave.lower() in descricao.lower():
                return categoria
        return 'Não categorizado'

    # Aplicação das novas colunas
    df_filtrado['Tópico'] = np.where(
        df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')
    
    df_filtrado['Subtópico'] = df_filtrado['Remetente/Destinatario'].apply(
        categorizar_transacao)

    # --- PARTE 4: SALVANDO TRANSAÇÕES E FAZENDO CÁLCULOS FINAIS ---


    for index, linha in df_filtrado.iterrows():
        Transacao.objects.create(
            extrato=extrato_obj, 
            usuario=usuario_logado,
            data=linha.get('Data', ''),
            descricao=linha.get('Remetente/Destinatario', ''),
            valor=linha.get('Valor', 0.0),
            topico=linha.get('Tópico', ''),
            subtopico=linha.get('Subtópico', '')
        )
    
    df_receitas = df_filtrado[df_filtrado['Tópico'] == 'Receita']
    df_despesas = df_filtrado[df_filtrado['Tópico'] == 'Despesa']

    total_despesas = df_despesas['Valor'].sum()
    total_receitas = df_receitas['Valor'].sum()
    saldo_liquido = total_receitas - total_despesas

    resumo_despesas = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    resumo_receitas = df_receitas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)
    
    nao_categorizadas_bruto = df_filtrado[df_filtrado['Subtópico'] == 'Não categorizado']
    colunas_desejadas = ['Tipo de Pix', 'Situacao', 'Remetente/Destinatario', 'Valor']
    nao_categorizadas_limpo = nao_categorizadas_bruto[colunas_desejadas]

    # --- PARTE 5: RETORNO DOS DADOS ---
    return total_receitas, total_despesas, saldo_liquido, resumo_despesas, nao_categorizadas_limpo, resumo_receitas