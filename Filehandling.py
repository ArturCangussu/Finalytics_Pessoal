import pandas as pd
import numpy as np

df = pd.read_excel('Extrato_pix.xlsx')

df_regras = pd.read_excel('regras.xlsx')

# faz o df regras ser lido e transformado em dicionario
regras_de_categorizacao = dict(
    zip(df_regras['PalavraChave'], df_regras['Categoria']))

# faz passar apenas os efetivados pra tabela
df_filtrado = df[df['Situacao'] == 'EFETIVADA']

# define que o que não for efetivado será guardado em outro df
df_erro = df[df['Situacao'] != 'EFETIVADA']

# se o tipo de pix for enviado = despesa, se não, receita
df_filtrado['Tópico'] = np.where(
    df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')


# regras_de_categorizacao = {
#   'MARCOS VINICIUS DOS SANTOS BARRETO': 'Manutenção',
#  'KAIROS': 'Serviço administrativo',
# 'IVONETE VIANA DE SOUSA': 'Despesa Mensal',
# 'AGUINALDO DIAS DO CARMO': 'Despesa Mensal',
# 'FABIANA CARDOSO DOS SANTOS VAZ': 'Despesa Mensal'
# }

def categorizar_transacao(descricao):
    if not isinstance(descricao, str):
        return 'Descrição Inválida'
    for palavra_chave, categoria in regras_de_categorizacao.items():
        if palavra_chave.lower() in descricao.lower():
            return categoria
    return 'Não categorizado'


df_filtrado['Subtópico'] = df_filtrado['Remetente/Destinatario'].apply(
    categorizar_transacao)

df_receitas = df_filtrado[df_filtrado['Tópico'] == 'Receita']
df_despesas = df_filtrado[df_filtrado['Tópico'] == 'Despesa']

df_receitas['Valor'].sum()