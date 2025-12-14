import pandas as pd
import os
from datetime import datetime

class CaixinhaManager:
    def __init__(self):
        # Configuração dos arquivos
        self.files_map = {
            7: 'Caixinha 2025.2 (Atualizando).xlsx - Julho.csv',
            8: 'Caixinha 2025.2 (Atualizando).xlsx - Agosto.csv',
            9: 'Caixinha 2025.2 (Atualizando).xlsx - Setembro.csv',
            10: 'Caixinha 2025.2 (Atualizando).xlsx - Outubro.csv',
            11: 'Caixinha 2025.2 (Atualizando).xlsx - Novembro.csv',
            12: 'Caixinha 2025.2 (Atualizando).xlsx - Dezembro.csv'
        }
        self.controle_file = 'Caixinha 2025.2 (Atualizando).xlsx - Controle 2025.1.csv'
        self.solicitacoes_file = 'solicitacoes_compras.csv'
        
        # Carregar dados iniciais
        self.dataframes = {}
        self.carregar_dados()

    def carregar_dados(self):
        """Carrega os CSVs para a memória."""
        print("Carregando base de dados...")
        for mes_num, filepath in self.files_map.items():
            if os.path.exists(filepath):
                # Header=1 pois a linha 0 costuma ser vazia ou título nestes arquivos
                self.dataframes[mes_num] = pd.read_csv(filepath, header=1)
            else:
                # Cria estrutura vazia se o arquivo não existir
                self.dataframes[mes_num] = pd.DataFrame(columns=[
                    'Data', 'Entradas', 'Especificação', 'Unnamed: 3', 
                    'Data.1', 'Saídas', 'Especificação.1'
                ])

        # Carregar Solicitações (Novo Recurso)
        if os.path.exists(self.solicitacoes_file):
            self.solicitacoes = pd.read_csv(self.solicitacoes_file)
        else:
            self.solicitacoes = pd.DataFrame(columns=['Data', 'Solicitante', 'Item', 'Valor_Estimado', 'Justificativa', 'Status'])

    def salvar_dados(self):
        """Salva todas as alterações nos arquivos CSV."""
        for mes_num, df in self.dataframes.items():
            path = self.files_map[mes_num]
            # Preserva a estrutura original salvando header
            df.to_csv(path, index=False)
        
        self.solicitacoes.to_csv(self.solicitacoes_file, index=False)
        print("\n✅ Dados salvos com sucesso!")

    def adicionar_transacao(self):
        print("\n--- Adicionar Transação ---")
        tipo = input("Tipo (1-Entrada, 2-Saída): ").strip()
        data_str = input("Data (AAAA-MM-DD): ").strip()
        valor = float(input("Valor: R$ "))
        desc = input("Descrição/Especificação: ").strip()

        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
            mes = data_obj.month
        except ValueError:
            print("❌ Data inválida.")
            return

        if mes not in self.dataframes:
            print(f"❌ Mês {mes} não configurado no sistema (apenas Jul-Dez).")
            return

        df = self.dataframes[mes]
        
        # Cria uma nova linha vazia
        nova_linha = {col: None for col in df.columns}
        
        if tipo == '1': # Entrada
            nova_linha['Data'] = data_str
            nova_linha['Entradas'] = valor
            nova_linha['Especificação'] = desc
        elif tipo == '2': # Saída
            nova_linha['Data.1'] = data_str
            nova_linha['Saídas'] = valor
            nova_linha['Especificação.1'] = desc
        else:
            print("Opção inválida.")
            return

        # Adiciona ao dataframe usando concat (append foi depreciado)
        novo_df_linha = pd.DataFrame([nova_linha])
        self.dataframes[mes] = pd.concat([df, novo_df_linha], ignore_index=True)
        print(f"✅ Transação adicionada na planilha de Mês {mes}!")

    def gerenciar_devedores(self):
        print("\n--- Controle de Devedores ---")
        if not os.path.exists(self.controle_file):
            print("Arquivo de controle não encontrado.")
            return

        ctrl = pd.read_csv(self.controle_file, header=1)
        
        # Identificar coluna de dívida (assume que é a última coluna numérica de "Total")
        col_divida = [c for c in ctrl.columns if "Total devedor" in str(c) and "2025" in str(c)][-1]
        
        # Mostrar devedores
        devedores = ctrl[pd.to_numeric(ctrl[col_divida], errors='coerce') > 0]
        print(devedores[['Petiano', col_divida]].to_string(index=True))
        
        opt = input("\nDeseja dar baixa em alguém? (S/N): ").upper()
        if opt == 'S':
            idx = int(input("Digite o índice (número à esquerda) do Petiano: "))
            valor_pago = float(input("Valor pago: R$ "))
            
            # Atualiza o valor na memória
            valor_atual = float(ctrl.at[idx, col_divida])
            novo_valor = max(0, valor_atual - valor_pago)
            ctrl.at[idx, col_divida] = novo_valor
            
            # Salva o arquivo de controle
            ctrl.to_csv(self.controle_file, index=False)
            
            # Opcional: Adicionar como entrada no caixa automaticamente
            add_caixa = input("Adicionar esse valor como ENTRADA no caixa agora? (S/N): ").upper()
            if add_caixa == 'S':
                nome = ctrl.at[idx, 'Petiano']
                hoje = datetime.now().strftime("%Y-%m-%d")
                self.adicionar_transacao_automatica(valor_pago, f"Pagamento Dívida: {nome}", hoje)
            
            print(f"✅ Dívida atualizada. Novo saldo devedor: R$ {novo_valor:.2f}")

    def adicionar_transacao_automatica(self, valor, desc, data_str):
        """Função auxiliar para adicionar transação sem input do usuário."""
        mes = datetime.strptime(data_str, "%Y-%m-%d").month
        if mes in self.dataframes:
            df = self.dataframes[mes]
            nova = {col: None for col in df.columns}
            nova['Data'] = data_str
            nova['Entradas'] = valor
            nova['Especificação'] = desc
            self.dataframes[mes] = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)

    def formulario_compras(self):
        print("\n--- Formulário de Solicitação de Compras ---")
        item = input("Item a ser comprado: ")
        valor = float(input("Valor Estimado: R$ "))
        justificativa = input("Justificativa/Projeto: ")
        solicitante = input("Nome do Solicitante: ")
        data = datetime.now().strftime("%Y-%m-%d")
        
        nova_solicitacao = {
            'Data': data,
            'Solicitante': solicitante,
            'Item': item,
            'Valor_Estimado': valor,
            'Justificativa': justificativa,
            'Status': 'Pendente'
        }
        
        self.solicitacoes = pd.concat([self.solicitacoes, pd.DataFrame([nova_solicitacao])], ignore_index=True)
        print("✅ Solicitação registrada com sucesso!")

    def listar_solicitacoes(self):
        print("\n--- Solicitações Pendentes ---")
        if self.solicitacoes.empty:
            print("Nenhuma solicitação registrada.")
        else:
            print(self.solicitacoes.to_string(index=False))

    def menu(self):
        while True:
            print("\n" + "="*30)
            print(" SISTEMA CAIXINHA 2025.2 ")
            print("="*30)
            print("1. Adicionar Entrada/Saída")
            print("2. Gerenciar Devedores")
            print("3. Solicitar Compra (Formulário)")
            print("4. Ver Solicitações de Compra")
            print("5. Salvar e Sair")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == '1':
                self.adicionar_transacao()
            elif opcao == '2':
                self.gerenciar_devedores()
            elif opcao == '3':
                self.formulario_compras()
            elif opcao == '4':
                self.listar_solicitacoes()
            elif opcao == '5':
                self.salvar_dados()
                break
            else:
                print("Opção inválida!")

if __name__ == "__main__":
    app = CaixinhaManager()
    app.menu()