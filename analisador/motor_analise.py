# Dentro de analisador/motor_analise.py
import pandas as pd
import numpy as np
from decimal import Decimal

# Esta é a nossa única e principal função
def processar_extrato(arquivo_extrato, arquivo_regras):
    
    # 1. LER OS DADOS USANDO OS ARGUMENTOS DA FUNÇÃO
    df = pd.read_excel(arquivo_extrato)
    df_regras = pd.read_excel(arquivo_regras)

    # 2. LÓGICA DE PROCESSAMENTO (tudo o que você já construiu)
    
    regras_de_categorizacao = dict(
        zip(df_regras['PalavraChave'], df_regras['Categoria']))

    df_filtrado = df[df['Situacao'] == 'EFETIVADA']
    df_filtrado = df_filtrado.copy()

    # Funções de ajuda (podem ficar dentro da função principal)
    def limpar_valor(v):
        try:
            v = str(v)
            v = v.replace('R$', '').replace('\xa0', '').replace(',', '.').strip()
            return Decimal(v)
        except:
            return Decimal('0.00')

    def categorizar_transacao(descricao):
        if not isinstance(descricao, str):
            return 'Descrição Inválida'
        for palavra_chave, categoria in regras_de_categorizacao.items():
            if palavra_chave.lower() in descricao.lower():
                return categoria
        return 'Não categorizado'

    # Aplicando a limpeza e categorização
    df_filtrado['Valor'] = df_filtrado['Valor'].apply(limpar_valor)
    
    df_filtrado['Tópico'] = np.where(
        df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')
    
    df_filtrado['Subtópico'] = df_filtrado['Remetente/Destinatario'].apply(
        categorizar_transacao)

    # 3. CÁLCULOS FINAIS
    
    df_receitas = df_filtrado[df_filtrado['Tópico'] == 'Receita']
    df_despesas = df_filtrado[df_filtrado['Tópico'] == 'Despesa']

    total_despesas = df_despesas['Valor'].sum()
    total_receitas = df_receitas['Valor'].sum()
    saldo_liquido = total_receitas + total_despesas # Usando + porque despesas são negativas (ou - se forem positivas)

    resumo_despesas = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)

    # 4. DEVOLVER OS RESULTADOS (SEM PRINT)
    
    return total_receitas, total_despesas, saldo_liquido, resumo_despesas