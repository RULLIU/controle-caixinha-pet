import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# --- 1. Configuração Inicial (DEVE ser a primeira linha de Streamlit) ---
st.set_page_config(page_title="Caixinha PET 2025.2", layout="wide")

# --- 2. Definição dos Arquivos ---
# Certifique-se de que os nomes dos arquivos no Replit correspondem EXATAMENTE a estes:
FILES_MAP = {
    7: 'Caixinha 2025.2 (Atualizando).xlsx - Julho.csv',
    8: 'Caixinha 2025.2 (Atualizando).xlsx - Agosto.csv',
    9: 'Caixinha 2025.2 (Atualizando).xlsx - Setembro.csv',
    10: 'Caixinha 2025.2 (Atualizando).xlsx - Outubro.csv',
    11: 'Caixinha 2025.2 (Atualizando).xlsx - Novembro.csv',
    12: 'Caixinha 2025.2 (Atualizando).xlsx - Dezembro.csv'
}
CONTROLE_FILE = 'Caixinha 2025.2 (Atualizando).xlsx - Controle 2025.1.csv'
SOLICITACOES_FILE = 'solicitacoes_compras.csv'

# Colunas padrão para garantir que o sistema não quebre se o arquivo for novo
COLUNAS_PADRAO = ['Data', 'Entradas', 'Especificação', 'Unnamed: 3', 'Data.1', 'Saídas', 'Especificação.1']

# --- 3. Funções de Carregamento (À PROVA DE ERROS) ---
def carregar_dados():
    dfs = {}
    for mes, path in FILES_MAP.items():
        if os.path.exists(path):
            try:
                # Tenta ler ignorando a primeira linha (padrão dos seus arquivos)
                df = pd.read_csv(path, header=1)
                
                # Verifica se as colunas essenciais existem, se não, assume vazio
                if 'Entradas' not in df.columns and 'Saídas' not in df.columns:
                     dfs[mes] = pd.DataFrame(columns=COLUNAS_PADRAO)
                else:
                    dfs[mes] = df
            except Exception:
                # Se der erro (arquivo vazio ou com formato ruim), cria uma tabela em branco
                dfs[mes] = pd.DataFrame(columns=COLUNAS_PADRAO)
        else:
            # Se o arquivo não existir, cria uma tabela em branco na memória
            dfs[mes] = pd.DataFrame(columns=COLUNAS_PADRAO)
    return dfs

def salvar_csv(df, mes):
    path = FILES_MAP[mes]
    df.to_csv(path, index=False)

def carregar_solicitacoes():
    if os.path.exists(SOLICITACOES_FILE):
        try:
            return pd.read_csv(SOLICITACOES_FILE)
        except:
            return pd.DataFrame(columns=['Data', 'Solicitante', 'Item', 'Valor_Estimado', 'Justificativa', 'Status'])
    return pd.DataFrame(columns=['Data', 'Solicitante', 'Item', 'Valor_Estimado', 'Justificativa', 'Status'])

def salvar_solicitacoes(df):
    df.to_csv(SOLICITACOES_FILE, index=False)

# --- 4. Interface Visual Principal ---
st.title("💰 Gestão Financeira - Caixinha 2025.2")

# Menu Lateral
menu = st.sidebar.radio("Navegação", ["Resumo Financeiro", "Nova Transação", "Devedores", "Solicitações de Compra"])

# Carrega os dados usando a função segura
dfs = carregar_dados()

# --- ABA 1: RESUMO FINANCEIRO ---
if menu == "Resumo Financeiro":
    st.header("Visão Geral do Semestre")
    
    dados_consolidados = []
    
    # Processa cada mês
    for mes, df in dfs.items():
        # Limpeza básica de dados para somar
        entradas = pd.to_numeric(df['Entradas'], errors='coerce').sum()
        saidas = pd.to_numeric(df['Saídas'], errors='coerce').sum()
        
        dados_consolidados.append({'Mês': mes, 'Tipo': 'Entrada', 'Valor': entradas})
        dados_consolidados.append({'Mês': mes, 'Tipo': 'Saída', 'Valor': saidas})
    
    df_grafico = pd.DataFrame(dados_consolidados)
    
    # Métricas do Topo
    col1, col2, col3 = st.columns(3)
    total_entradas = df_grafico[df_grafico['Tipo']=='Entrada']['Valor'].sum()
    total_saidas = df_grafico[df_grafico['Tipo']=='Saída']['Valor'].sum()
    saldo = total_entradas - total_saidas
    
    col1.metric("Total Entradas", f"R$ {total_entradas:.2f}")
    col2.metric("Total Saídas", f"R$ {total_saidas:.2f}")
    col3.metric("Saldo Calculado", f"R$ {saldo:.2f}", delta_color="normal")

    # Gráfico
    if not df_grafico.empty:
        fig = px.bar(df_grafico, x='Mês', y='Valor', color='Tipo', barmode='group', title="Fluxo de Caixa Mensal")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para gerar gráfico.")

    # Tabela detalhada
    mes_selecionado = st.selectbox("Ver detalhes do mês:", list(FILES_MAP.keys()))
    st.dataframe(dfs[mes_selecionado], use_container_width=True)

# --- ABA 2: NOVA TRANSAÇÃO ---
elif menu == "Nova Transação":
    st.header("Adicionar Movimentação")
    
    with st.form("form_transacao"):
        col1, col2 = st.columns(2)
        tipo = col1.selectbox("Tipo", ["Entrada", "Saída"])
        data = col2.date_input("Data", datetime.now())
        
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        descricao = st.text_input("Descrição / Especificação")
        
        submitted = st.form_submit_button("Salvar Transação")
        
        if submitted:
            mes = data.month
            if mes not in dfs:
                st.error("Mês fora do semestre configurado (Jul-Dez)!")
            else:
                df_atual = dfs[mes]
                
                # Prepara a nova linha com colunas vazias
                nova_linha = {c: None for c in df_atual.columns}
                
                # Preenche conforme o tipo
                data_formatada = data.strftime("%Y-%m-%d")
                if tipo == "Entrada":
                    nova_linha['Data'] = data_formatada
                    nova_linha['Entradas'] = valor
                    nova_linha['Especificação'] = descricao
                else:
                    nova_linha['Data.1'] = data_formatada
                    nova_linha['Saídas'] = valor
                    nova_linha['Especificação.1'] = descricao
                
                # Adiciona e Salva
                df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_csv(df_atual, mes)
                st.success(f"✅ Transação de R$ {valor} salva em {tipo} no mês {mes}!")

# --- ABA 3: DEVEDORES ---
elif menu == "Devedores":
    st.header("Controle de Dívidas")
    
    if os.path.exists(CONTROLE_FILE):
        try:
            df_control = pd.read_csv(CONTROLE_FILE, header=1)
            
            # Tenta encontrar a coluna de dívida dinamicamente
            cols_divida = [c for c in df_control.columns if "Total devedor" in str(c) and "2025" in str(c)]
            
            if cols_divida:
                col_divida = cols_divida[-1] # Pega a última encontrada
                
                # Filtra quem deve > 0
                devedores = df_control.copy()
                devedores[col_divida] = pd.to_numeric(devedores[col_divida], errors='coerce').fillna(0)
                devedores = devedores[devedores[col_divida] > 0]
                
                st.dataframe(devedores[['Petiano', col_divida]], use_container_width=True)
                
                st.divider()
                st.subheader("Dar Baixa em Pagamento")
                
                with st.form("baixa_pagamento"):
                    petiano_select = st.selectbox("Selecione o Petiano", devedores['Petiano'].unique())
                    valor_pagamento = st.number_input("Valor a Pagar", min_value=0.0)
                    btn_pagar = st.form_submit_button("Confirmar Pagamento")
                    
                    if btn_pagar:
                        # Localiza o índice no DataFrame original
                        idx = df_control[df_control['Petiano'] == petiano_select].index[0]
                        divida_atual = float(
