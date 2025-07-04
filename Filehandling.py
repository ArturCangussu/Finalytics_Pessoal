import pandas as pd
import numpy as np

df = pd.read_excel('Extrato_pix.xlsx')

df_filtrado = df[df['Situacao'] == 'EFETIVADA']

df_erro = df[df['Situacao'] != 'EFETIVADA']

df_filtrado['Topico'] = np.where(df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')


regras_de_categorizacao = {
    'MARCOS VINICIUS DOS SANTOS BARRETO': 'Manutencao',
    'KAIROS': 'Servico administrativo',
    'IVONETE VIANA DE SOUSA': 'Despesa Mensal',
    'AGUINALDO DIAS DO CARMO': 'Despesa Mensal',
    'FABIANA CARDOSO DOS SANTOS VAZ': 'Despesa Mensal'
}

def categorizar_transacao(descricao):
    if not isinstance(descricao, str):
        return 'Descrição Inválida'
    for palavra_chave, categoria in regras_de_categorizacao.items():
        if palavra_chave.lower() in descricao.lower():
            return categoria
    return 'Nao categorizado'

df_filtrado['Subtopico'] = df_filtrado['Remetente/Destinatario'].apply(categorizar_transacao)