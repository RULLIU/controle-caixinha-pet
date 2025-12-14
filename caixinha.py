import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(page_title="CAIXINHA - PET", layout="wide", page_icon="💰")

# --- SENHA DE ACESSO ---
SENHA_ADMIN = "pet2025"

# --- Arquivos ---
FILE_FINANCEIRO = "financeiro.csv"
FILE_DEVEDORES = "devedores.csv"
FILE_COMPRAS = "compras.csv"

# --- Lista de Origens (Essa mantemos fixa pois ajuda na conciliação) ---
LISTA_ORIGEM = ["Conta (Banco)", "Dinheiro Físico"]

# --- Inicialização ---
def inicializar_sistema():
    # Adicionamos a coluna "Origem"
    if not os.path.exists(FILE_FINANCEIRO):
        pd.DataFrame(columns=["Data", "Tipo", "Projeto", "Descrição", "Valor", "Origem"]).to_csv(FILE_FINANCEIRO, index=False)
    
    if not os.path.exists(FILE_DEVEDORES):
        pd.DataFrame(columns=["Nome", "Valor_Devido", "Ultima_Atualizacao"]).to_csv(FILE_DEVEDORES, index=False)
        
    if not os.path.exists(FILE_COMPRAS):
        pd.DataFrame(columns=["Data", "Solicitante", "Item", "Valor", "Status"]).to_csv(FILE_COMPRAS, index=False)

def carregar_dados(arquivo):
    df = pd.read_csv(arquivo)
    
    # --- AUTO-CORREÇÃO PARA ARQUIVOS ANTIGOS ---
    if arquivo == FILE_FINANCEIRO:
        if "Origem" not in df.columns:
            df["Origem"] = "Conta (Banco)" # Assume padrão para antigos
        if "Categoria" in df.columns:
            df.rename(columns={"Categoria": "Projeto"}, inplace=True)
            
    return df

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

inicializar_sistema()

# --- Navegação ---
st.sidebar.title("🔐 Menu")
modo_acesso = st.sidebar.radio("Selecione o perfil:", ["Visão Pública (Membros)", "Acesso do Caixinha"])

# ==============================================================================
#  ÁREA PÚBLICA
# ==============================================================================
if modo_acesso == "Visão Pública (Membros)":
    st.title("📢 Portal da Transparência - CAIXINHA PET")
    
    tab1, tab2, tab3 = st.tabs(["📊 Resumo Financeiro", "🛒 Solicitar Compra", "📋 Lista de Cotinhas"])
    
    # --- TAB 1: RESUMO ---
    with tab1:
        df_fin = carregar_dados(FILE_FINANCEIRO)
        if not df_fin.empty:
            # Cálculos Gerais
            entradas = df_fin[df_fin['Tipo'] == 'Entrada']['Valor'].sum()
            saidas = df_fin[df_fin['Tipo'] == 'Saída']['Valor'].sum()
            saldo_total = entradas - saidas
            
            # Cálculos por Origem
            conta_in = df_fin[(df_fin['Tipo']=='Entrada') & (df_fin['Origem']=='Conta (Banco)')]['Valor'].sum()
            conta_out = df_fin[(df_fin['Tipo']=='Saída') & (df_fin['Origem']=='Conta (Banco)')]['Valor'].sum()
            saldo_conta = conta_in - conta_out
            
            fisico_in = df_fin[(df_fin['Tipo']=='Entrada') & (df_fin['Origem']=='Dinheiro Físico')]['Valor'].sum()
            fisico_out = df_fin[(df_fin['Tipo']=='Saída') & (df_fin['Origem']=='Dinheiro Físico')]['Valor'].sum()
            saldo_fisico = fisico_in - fisico_out
            
            # Exibição
            st.subheader("Balanço Geral")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Arrecadado", f"R$ {entradas:.2f}")
            col2.metric("Total Gasto", f"R$ {saidas:.2f}")
            col3.metric("SALDO TOTAL", f"R$ {saldo_total:.2f}", delta_color="normal")
            
            st.divider()
            st.subheader("Onde está o dinheiro?")
            c_bank, c_cash = st.columns(2)
            c_bank.info(f"🏦 **No Banco:** R$ {saldo_conta:.2f}")
            c_cash.success(f"💵 **Dinheiro Físico:** R$ {saldo_fisico:.2f}")
            
            # Gráfico de Projetos (Dinâmico)
            if not df_fin[df_fin['Tipo']=='Saída'].empty:
                st.divider()
                fig_proj = px.pie(df_fin[df_fin['Tipo']=='Saída'], values='Valor', names='Projeto', title="Distribuição de Gastos por Projeto")
                st.plotly_chart(fig_proj, use_container_width=True)
            
            st.divider()
            st.write("Últimas Movimentações:")
            st.dataframe(df_fin.sort_values(by="Data", ascending=False).head(8), use_container_width=True)
        else:
            st.info("O caixa ainda não foi aberto (Sem dados).")

    # --- TAB 2: SOLICITAÇÃO ---
    with tab2:
        st.header("Solicitação de Compras")
        df_comp = carregar_dados(FILE_COMPRAS)
        
        with st.form("form_solicita_publica"):
            col_a, col_b = st.columns(2)
            nome = col_a.text_input("Seu Nome")
            item = col_b.text_input("Item / Serviço")
            valor = st.number_input("Valor Estimado (R$)", min_value=0.0)
            
            if st.form_submit_button("Enviar Solicitação"):
                novo = {
                    "Data": datetime.now().strftime("%Y-%m-%d"),
                    "Solicitante": nome,
                    "Item": item,
                    "Valor": valor,
                    "Status": "Pendente"
                }
                df_comp = pd.concat([df_comp, pd.DataFrame([novo])], ignore_index=True)
                salvar_dados(df_comp, FILE_COMPRAS)
                st.success("Enviado para análise!")
                st.rerun()
        
        st.dataframe(df_comp[['Data', 'Solicitante', 'Item', 'Status']], use_container_width=True)

    # --- TAB 3: DEVEDORES ---
    with tab3:
        st.header("Situação das Cotinhas")
        df_dev = carregar_dados(FILE_DEVEDORES)
        if not df_dev.empty:
            st.dataframe(df_dev[['Nome', 'Valor_Devido']].sort_values(by='Valor_Devido', ascending=False), use_container_width=True)
        else:
            st.info("Nenhuma pendência.")

# ==============================================================================
#  ACESSO DO CAIXINHA (ADMIN)
# ==============================================================================
elif modo_acesso == "Acesso do Caixinha":
    st.sidebar.divider()
    senha_input = st.sidebar.text_input("Senha de Acesso", type="password")
    
    if senha_input == SENHA_ADMIN:
        st.title("🔐 Painel de Controle - CAIXINHA")
        
        menu_admin = st.sidebar.radio("Gerenciar:", ["Fluxo de Caixa", "Cotinhas", "Aprovar Compras"])
        
        # --- 1. FLUXO DE CAIXA ---
        if menu_admin == "Fluxo de Caixa":
            tab_lanc, tab_edit = st.tabs(["➕ Novo Lançamento", "✏️ Editar Tabela"])
            
            with tab_lanc:
                st.subheader("Registrar Movimentação")
                with st.form("admin_financeiro"):
                    c1, c2, c3 = st.columns(3)
                    tipo = c1.selectbox("Tipo", ["Entrada", "Saída"])
                    data = c2.date_input("Data", datetime.now())
                    valor = c3.number_input("Valor (R$)", min_value=0.01)
                    
                    c4, c5 = st.columns(2)
                    
                    # --- MUDANÇA AQUI: Campo de Texto Livre ---
                    projeto = c4.text_input("Projeto / Classificação", placeholder="Digite o nome do projeto...")
                    
                    origem = c5.selectbox("Onde entrou/saiu o dinheiro?", LISTA_ORIGEM)
                    
                    descricao = st.text_input("Descrição")
                    
                    if st.form_submit_button("Salvar Lançamento"):
                        # Validação simples para não salvar projeto vazio
                        proj_final = projeto if projeto.strip() != "" else "Geral"
                        
                        df = carregar_dados(FILE_FINANCEIRO)
                        novo = {
                            "Data": data, "Tipo": tipo, "Projeto": proj_final, 
                            "Descrição": descricao, "Valor": valor, "Origem": origem
                        }
                        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
                        salvar_dados(df, FILE_FINANCEIRO)
                        st.success("Salvo com sucesso!")
                        st.rerun()

            with tab_edit:
                st.subheader("Editor Completo")
                df_atual = carregar_dados(FILE_FINANCEIRO)
                df_editado = st.data_editor(df_atual, num_rows="dynamic", use_container_width=True, key="editor_financeiro")
                
                if st.button("💾 Salvar Alterações"):
                    salvar_dados(df_editado, FILE_FINANCEIRO)
                    st.success("Atualizado!")
                    st.rerun()

        # --- 2. COTINHAS ---
        elif menu_admin == "Cotinhas":
            st.header("Gestão de Cotinhas")
            
            tab_pag, tab_edit_dev = st.tabs(["💰 Receber Pagamento", "✏️ Editar Membros"])
            
            with tab_pag:
                df_dev = carregar_dados(FILE_DEVEDORES)
                if not df_dev.empty:
                    quem_deve = df_dev[df_dev['Valor_Devido'] > 0]['Nome'].unique()
                    if len(quem_deve) > 0:
                        with st.form("form_baixa_cotinha"):
                            c1, c2 = st.columns(2)
                            pagador = c1.selectbox("Quem pagou?", quem_deve)
                            valor_pago = c2.number_input("Valor (R$)", min_value=0.01)
                            
                            origem_pag = st.selectbox("Recebido em:", LISTA_ORIGEM)
                            
                            if st.form_submit_button("Confirmar Baixa"):
                                idx = df_dev[df_dev['Nome'] == pagador].index[0]
                                df_dev.at[idx, 'Valor_Devido'] = max(0, df_dev.at[idx, 'Valor_Devido'] - valor_pago)
                                salvar_dados(df_dev, FILE_DEVEDORES)
                                
                                # Lança entrada no caixa
                                df_fin = carregar_dados(FILE_FINANCEIRO)
                                novo_fin = {
                                    "Data": datetime.now().strftime("%Y-%m-%d"),
                                    "Tipo": "Entrada", "Projeto": "Mensalidade",
                                    "Descrição": f"Cotinha: {pagador}", "Valor": valor_pago,
                                    "Origem": origem_pag
                                }
                                df_fin = pd.concat([df_fin, pd.DataFrame([novo_fin])], ignore_index=True)
                                salvar_dados(df_fin, FILE_FINANCEIRO)
                                
                                st.success(f"Baixa efetuada para {pagador}!")
                                st.rerun()
                    else:
                        st.info("Ninguém devendo.")
            
            with tab_edit_dev:
                st.subheader("Correção Manual")
                df_dev_atual = carregar_dados(FILE_DEVEDORES)
                df_dev_editado = st.data_editor(df_dev_atual, num_rows="dynamic", use_container_width=True, key="editor_devedores")
                
                if st.button("💾 Salvar Alterações Devedores"):
                    salvar_dados(df_dev_editado, FILE_DEVEDORES)
                    st.success("Lista atualizada!")
                    st.rerun()

        # --- 3. APROVAR COMPRAS ---
        elif menu_admin == "Aprovar Compras":
            st.header("Pedidos Pendentes")
            df_comp = carregar_dados(FILE_COMPRAS)
            pendentes = df_comp[df_comp['Status'] == 'Pendente']
            
            if not pendentes.empty:
                for i, row in pendentes.iterrows():
                    with st.expander(f"{row['Item']} - R$ {row['Valor']} ({row['Solicitante']})"):
                        c1, c2 = st.columns(2)
                        if c1.button("Aprovar", key=f"ok_{i}"):
                            df_comp.at[i, 'Status'] = 'Aprovado'
                            salvar_dados(df_comp, FILE_COMPRAS)
                            st.rerun()
                        if c2.button("Recusar", key=f"no_{i}"):
                            df_comp.at[i, 'Status'] = 'Recusado'
                            salvar_dados(df_comp, FILE_COMPRAS)
                            st.rerun()
            else:
                st.info("Nenhum pedido pendente.")
                
            st.divider()
            st.subheader("Histórico (Editável)")
            df_comp_editado = st.data_editor(df_comp, num_rows="dynamic", key="editor_compras")
            if st.button("Salvar Correções Histórico"):
                salvar_dados(df_comp_editado, FILE_COMPRAS)
                st.rerun()

    else:
        st.warning("⚠️ Insira a senha na barra lateral para acessar o painel.")
