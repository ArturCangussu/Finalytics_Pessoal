# Finanalytics - Analisador Financeiro Pessoal

Aplicação web Django que automatiza a análise e categorização de extratos bancários para gestão de finanças pessoais.

---

### 📸 Screenshot

<p align="center">
  <img src="[COLE O LINK DA IMAGEM AQUI]" width="80%" alt="Dashboard do Finanalytics Pessoal">
</p>

---

### 🎯 Sobre o Projeto

A gestão de finanças pessoais muitas vezes começa com a tarefa tediosa de analisar um extrato bancário, uma planilha com centenas de linhas difíceis de interpretar. Entender para onde o dinheiro realmente foi, categorizar cada gasto e ter uma visão clara da saúde financeira é um processo manual, lento e que a maioria das pessoas abandona.

#### **Por que ele foi criado?**
O Finanalytics Pessoal nasceu como uma solução para este problema. Foi criado para ser uma ferramenta que transforma o caos de um extrato bancário bruto em um relatório financeiro claro e organizado, automatizando todo o processo de análise e categorização.

#### **Qual o objetivo?**
O objetivo principal é fornecer uma aplicação web simples e poderosa onde o usuário possa fazer o upload de seu extrato bancário em Excel (.xlsx). A partir daí, a plataforma assume a responsabilidade de:

* Ler e estruturar os dados do extrato, utilizando a biblioteca Pandas para a limpeza e manipulação.
* Categorizar cada transação (receita ou despesa) de forma inteligente, com base em um sistema de regras customizável criado pelo próprio usuário.
* Apresentar um dashboard interativo com relatórios visuais, mostrando:
    * ✅ **Resumo de Receitas e Despesas:** Totais do período.
    * 📊 **Gastos por Categoria:** Um gráfico que ilustra claramente para onde o dinheiro está indo.
    * 🏷️ **Transações Não Categorizadas:** Uma lista para que o usuário possa criar novas regras e aprimorar a precisão da análise.

Em resumo, o Finanalytics Pessoal transforma um extrato confuso em insights acionáveis, automatizando e simplificando a gestão financeira pessoal.

---

### ✨ Funcionalidades Principais

-   ✅ Upload de extratos bancários em formato Excel (.xlsx).
-   ✅ Sistema de regras customizável para categorização inteligente de transações.
-   ✅ Geração automática de relatórios de despesas e receitas por categoria.
-   ✅ Interface web para upload, gerenciamento de regras e visualização de dados.

---

### 🛠️ Tecnologias Utilizadas

-   **Backend:** Python, Django
-   **Análise de Dados:** Pandas
-   **Frontend:** HTML, CSS, JavaScript, Bootstrap, Chart.js
-   **Banco de Dados:** SQLite

---

### 🚀 Como Executar o Projeto

```bash
# Clone o repositório
$ git clone [https://github.com/Artur-Cangussu/FINALYTICS_PESSOAL.git](https://github.com/Artur-Cangussu/FINALYTICS_PESSOAL.git)

# Navegue até a pasta do projeto
$ cd FINALYTICS_PESSOAL

# Instale as dependências
$ pip install -r requirements.txt

# Execute as migrações do banco de dados
$ python manage.py migrate

# Inicie o servidor
$ python manage.py runserver
```
