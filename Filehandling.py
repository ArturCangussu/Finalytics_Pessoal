import pandas as pd
import numpy as np
from decimal import Decimal

df = pd.read_excel('Extrato_pix.xlsx')

df_regras = pd.read_excel('regras.xlsx')

# faz o df regras ser lido e transformado em dicionario
regras_de_categorizacao = dict(
    zip(df_regras['PalavraChave'], df_regras['Categoria']))

# faz passar apenas os efetivados pra tabela
df_filtrado = df[df['Situacao'] == 'EFETIVADA']

# define que o que não for efetivado será guardado em outro df
df_erro = df[df['Situacao'] != 'EFETIVADA']
# Garante que o df_filtrado seja uma cópia independente
df_filtrado = df_filtrado.copy()

# Converte a coluna 'Valor' de string com R$ e vírgula para Decimal com precisão
def limpar_valor(v):
    try:
        v = str(v)
        v = v.replace('R$', '').replace('\xa0', '').replace(',', '.').strip()
        return Decimal(v)
    except:
        return Decimal('0.00')  

df_filtrado['Valor'] = df_filtrado['Valor'].apply(limpar_valor)


# se o tipo de pix for enviado = despesa, se não, receita
df_filtrado['Tópico'] = np.where(
    df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')


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

total_despesas = df_despesas['Valor'].sum()
total_receitas = df_receitas['Valor'].sum()
saldo_liquido = total_receitas - total_despesas

#separando as despesas por topico
resumo_despesas = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values()

#deixando bonito pra printar
print("\n--- Detalhamento de Despesas por Categoria ---")
resumo_formatado = resumo_despesas.abs().astype(float).to_string(
    header=False,
    float_format='R$ {:>10,.2f}'.format
)

print(resumo_despesas)