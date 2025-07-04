import pandas as pd
import numpy as np

df = pd.read_excel('Extrato_pix.xlsx')

df_filtrado = df[df['Situacao'] == 'EFETIVADA']

df_erro = df[df['Situacao'] != 'EFETIVADA']

df_filtrado['Topico'] = np.where(df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')


regras_de_categorizacao = {
    ''
}
print(df_filtrado)