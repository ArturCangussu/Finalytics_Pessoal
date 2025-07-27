# Dentro de analisador/motor_analise.py
import pandas as pd
import numpy as np
from decimal import Decimal
from .models import Regra

def processar_extrato(arquivo_extrato, usuario_logado):
    
    # --- PARTE 1: LEITURA E PREPARAÇÃO ---
    df = pd.read_excel(arquivo_extrato)
    
    regras_do_usuario = Regra.objects.filter(usuario=usuario_logado)
    regras_de_categorizacao = {
        regra.palavra_chave: regra.categoria for regra in regras_do_usuario
    }

    # --- PARTE 2: FILTRAGEM (A PARTE QUE FALTAVA) ---
    df_filtrado = df[df['Situacao'] == 'EFETIVADA']
    df_filtrado = df_filtrado.copy() # Garante que estamos trabalhando com uma cópia

    # --- PARTE 3: LIMPEZA E CATEGORIZAÇÃO ---
    
    # Funções de ajuda
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

    # Aplicando as funções
    df_filtrado['Valor'] = df_filtrado['Valor'].apply(limpar_valor)
    
    df_filtrado['Tópico'] = np.where(
        df_filtrado['Tipo de Pix'] == 'Enviado', 'Despesa', 'Receita')
    
    df_filtrado['Subtópico'] = df_filtrado['Remetente/Destinatario'].apply(
        categorizar_transacao)

    # --- PARTE 4: CÁLCULOS FINAIS ---
    
    df_receitas = df_filtrado[df_filtrado['Tópico'] == 'Receita']
    df_despesas = df_filtrado[df_filtrado['Tópico'] == 'Despesa']

    total_despesas = df_despesas['Valor'].sum()
    total_receitas = df_receitas['Valor'].sum()
    saldo_liquido = total_receitas - total_despesas # Corrigido para sua lógica de despesas positivas

    resumo_despesas = df_despesas.groupby('Subtópico')['Valor'].sum().sort_values(ascending=False)

    # --- PARTE 5: RETORNO DOS DADOS ---


# Filtra o DataFrame para pegar apenas as linhas onde o Subtópico é 'Não categorizado'
    nao_categorizadas = df_filtrado[df_filtrado['Subtópico'] == 'Não categorizado']
    return total_receitas, total_despesas, saldo_liquido, resumo_despesas, nao_categorizadas
