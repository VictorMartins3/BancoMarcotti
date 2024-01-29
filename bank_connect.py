import sqlite3
import random
import PySimpleGUI as sg
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sqlite3
from datetime import datetime, timedelta

class BaseBanco:
    def __init__(self): #Inicia a conexão com o banco de dados 
        self.connector = sqlite3.connect('dados_clientes.db')
        self.cursor = self.connector.cursor()

    def __del__(self): #Fecha a conexão com o banco de dados quando o programa é encerrado
        self.connector.close()

    def enviar_email(self, destinatario, assunto, mensagem):
        print(destinatario)
        smtp_server = 'smtp.gmail.com'
        smtp_port = 465
        smtp_user = 'martins.victor212004@gmail.com'
        smtp_password = 'hkvp womr mfyv wcro'

        # Criando a mensagem
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        # Enviando o e-mail
        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            print("E-mail enviado com sucesso!")
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            import traceback
            traceback.print_exc()

    def obter_ultimo_id(self) -> int: #Aqui é para obter o último ID criado para criar uma nova conta 
        self.cursor.execute("SELECT MAX(id) FROM usuarios")
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado[0] is not None else 0

    def verificar_dados(self, tipo: str, valor) -> int: #verifica se um cpf existe por ex 
        self.cursor.execute(f"SELECT COUNT(*) FROM usuarios WHERE {tipo} = ? ", (valor,))
        resultado = self.cursor.fetchone()[0]
        return resultado

    def verificar_login(self, cpf, senha): #Verifica cpf e senha 
        self.cursor.execute("SELECT COUNT(*) FROM usuarios WHERE cpf = ? AND senha = ?", (cpf, senha))
        resultado = self.cursor.fetchone()[0]
        return resultado > 0
    
    def valida_cpf(self, cpf):
        #Remove caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, cpf))

        #Verifica se o CPF tem 11 dígitos
        if len(cpf) != 11:
            return False

        #Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False

        #Calcula o primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        resto = soma % 11
        digito1 = 11 - resto if resto > 1 else 0

        #Verifica se o primeiro dígito verificador é igual ao do cpf 
        if digito1 != int(cpf[9]):
            return False

        #Calcula o segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        resto = soma % 11
        digito2 = 11 - resto if resto > 1 else 0

        #Verifica se o segundo dígito verificador é igual ao fornecido
        if digito2 != int(cpf[10]):
            return False

        #Se todas as verificações passaram, o CPF é válido
        return True

    def obter_saldo(self, usuario_id: int) -> float: #procura o saldo da conta pelo ID 
        self.cursor.execute("SELECT saldo FROM contas WHERE usuario_id = ?", (usuario_id,))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado is not None else 0.0

    def obter_dados_id(self, tipo: str, usuario_id: str):
        self.cursor.execute(f"SELECT {tipo} FROM usuarios WHERE id = ?", (usuario_id,))   
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado is not None else 0 
    
    def obter_dados_cpf(self, tipo: str, usuario_cpf: str): #Pega os dados pelo cpf, qualquer dado do usuario 
        self.cursor.execute(f"SELECT {tipo} FROM usuarios WHERE cpf = ?", (usuario_cpf,))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado is not None else 0
   
    def obter_dados_email(self, tipo: str, usuario_email: str):
        self.cursor.execute(f"SELECT {tipo} FROM usuarios WHERE email = ?", (usuario_email,))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado is not None else 0 
    
    def atualizar_saldo(self, usuario_id: int, novo_saldo: float) -> None: #Atualiza o saldo quando fizer um pix/deposito
        self.cursor.execute("UPDATE contas SET saldo = ? WHERE usuario_id = ?", (novo_saldo, usuario_id))
        self.connector.commit()

    def atualizar_senha(self, usuario_id: int, nova_senha: str) -> None:
        print(usuario_id)
        self.cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (nova_senha, usuario_id))
        self.connector.commit()

    def obter_transacoes(self, usuario_id: int) -> list: #Procura todas as transações de um ID de PIX 
        self.cursor.execute("SELECT * FROM transacoes WHERE conta_origem_id = ? OR conta_destino_id = ?", (usuario_id, usuario_id))
        return self.cursor.fetchall()

    def obter_depositos(self, usuario_id: int) -> list: #Procura todos os depósitos
        self.cursor.execute("SELECT * FROM depositos WHERE conta_id = ?", (usuario_id,))
        return self.cursor.fetchall()

    def deletar_conta(self, usuario_id: int) -> None: 
        self.cursor.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
        self.cursor.execute('DELETE FROM contas WHERE usuario_id = ?', (usuario_id,))
        self.cursor.execute('DELETE FROM depositos WHERE conta_id = ?', (usuario_id,))
        self.cursor.execute('UPDATE transacoes SET conta_origem_id = NULL WHERE conta_origem_id = ?', (usuario_id,))
        self.cursor.execute('UPDATE transacoes SET conta_destino_id = NULL WHERE conta_destino_id = ?', (usuario_id,))

        self.connector.commit()

class ContaBancaria(BaseBanco):
    def gerar_numero_conta(self) -> str: #gera um número aleatório para conta com random 
        quatro_digitos_iniciais = str(random.randint(1000, 9999))
        digito_final = str(random.randint(1, 9))
        numero_conta = f"{quatro_digitos_iniciais}-{digito_final}"

        while self.verificar_dados("numero_conta", numero_conta) > 0: #Verifica se esse número de conta já existe, senão ele retorna ele
            quatro_digitos_iniciais = str(random.randint(1000, 9999))
            digito_final = str(random.randint(1, 9))
            numero_conta = f"{quatro_digitos_iniciais}-{digito_final}"

        return numero_conta

    def abrir_conta(self, cpf: str, nome: str, senha: str, email: str) -> None: #Cadastra uma nova conta
        id = self.obter_ultimo_id() + 1 #Insere um novo ID 
        numero_conta = self.gerar_numero_conta() #Gera um númeor de conta 

        self.cursor.execute("INSERT INTO contas (usuario_id, saldo) VALUES (?, ?)", (id, 0.0)) #Cria uma conta zerada associada ao ID do usuario
        self.cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?, ?, ?)", (id, cpf, nome, numero_conta, senha, email)) #Cria um usuario 

        self.connector.commit() 
        print(f"\n✅ Conta aberta com sucesso! Número da conta: {numero_conta}\n")

class TelaTransacoes(BaseBanco):
    def __init__(self, cpf): #Chama o construtor init da BaseBanco para trazer a conexão com o banco de dados
        super().__init__()
        self.id = self.obter_dados_cpf('id', cpf) #Chama função para obter ID 
        self.cpf = cpf
        #Design do aplicativo 
        self.layout = [
            [sg.Text('Histórico de Transações', font=('Helvetica', 20), justification='center')],
            [sg.Text('', size=(30, 1))],
            [sg.Table(values=[], headings=['Data', 'Descrição', 'Valor'], auto_size_columns=False,
                      col_widths=[20, 15, 15], justification='right', display_row_numbers=False, num_rows=20, key='table')],
            [sg.Button('Fechar', size=(10, 2), font=('Helvetica', 12)),
             sg.Button('Análise Exploratória', size=(20, 2), font=('Helvetica', 12))]
        ]

        sg.set_options(font=('Helvetica', 12))
        self.window = sg.Window('Histórico de Transações', self.layout, finalize=True)
        self.atualizar_lista_transacoes() #Atualiza a tela 

    def atualizar_lista_transacoes(self): #Função para adicionar e atualizar os valores da tela 
        transacoes = self.obter_transacoes(self.id) #Obtem uma lista das transações
        depositos = self.obter_depositos(self.id) #Obtem uma lista dos depositos 

        data = [] #Onde será armazenado todos os dados transacoes e pix e depositos

        for transacao in transacoes: #faz a lista aqui 
            data.append([transacao[3], 'Pix', transacao[4]])

        for deposito in depositos:
            data.append([deposito[2], 'Depósito', deposito[3]])

        self.window['table'].update(values=data) #atualiza os valores 

    def plot_tendencia_saldo(self): #Grafico da tendencia 

        #Obtem transacoes e depositos 
        transacoes = self.obter_transacoes(self.id)
        depositos = self.obter_depositos(self.id)

        data_transacoes = {'Data': [], 'Saldo': []} #armazenamento dos depositos e das transacoes 
        saldo_atual = 0.0

        for transacao in transacoes: #vai passar por todos das transacoes 
            data_transacoes['Data'].append(transacao[3])
            saldo_atual -= transacao[4]
            data_transacoes['Saldo'].append(saldo_atual)

        for deposito in depositos: #vai passar por todos os depositos 
            data_transacoes['Data'].append(deposito[2])
            saldo_atual += deposito[3]
            data_transacoes['Saldo'].append(saldo_atual)

        df = pd.DataFrame(data_transacoes) #montando o dataframe com o framework pandas 
        df['Data'] = pd.to_datetime(df['Data']) #convertendo os dados de 'Data' para data em pandas

        plt.figure(figsize=(12, 6))
        sns.lineplot(x='Data', y='Saldo', data=df)
        plt.title('Tendência de Saldo ao Longo do Tempo')
        plt.xlabel('Data')
        plt.ylabel('Saldo')
        plt.show()

    def executar(self):
        while True:
            event, values = self.window.read() #espera intereção do usuario para capturar o evento 

            if event == sg.WINDOW_CLOSED or event == 'Fechar': #vai dar um break se fechar a janela ou clicar em fechar 
                self.window.close()
                tela_conta = TelaConta(self.cpf)
                tela_conta.executar()
                break
            elif event == 'Análise Exploratória': #Se clicar no botão da analise vai chamar a função para exibir o grafico 
                self.plot_tendencia_saldo()

            self.atualizar_lista_transacoes()

        self.window.close()

class TelaConta(BaseBanco):
    def __init__(self, cpf):
        super().__init__() #Chama o construtor init da BaseBanco para trazer a conexão com o banco de dados
        
        #secao para obter os dados usados nessa classe 
        self.id = self.obter_dados_cpf("id", cpf)
        self.numero_conta = self.obter_dados_cpf("numero_conta", cpf)
        self.nome = self.obter_dados_cpf("nome", cpf)
        self.saldo = self.obter_saldo(self.id)
        self.cpf = cpf 
        sg.theme('DarkGrey5')
        
        #Parte visual do programa
        self.layout = [
            [sg.Text('Conta Bancária', font=('Helvetica', 24), justification='center')],
            [sg.Text(f'Olá, {self.nome}!', font=('Helvetica', 16), justification='center')],
            [sg.Text(f'Número da Conta: {self.numero_conta}', font=('Helvetica', 16), justification='center')],
            [sg.Text(f'Saldo: R$ {self.saldo:.2f}', font=('Helvetica', 20), key='saldo', justification='center')],
            [
                sg.Button('Pix', size=(15, 2), font=('Helvetica', 16)), 
                sg.Button('Depositar', size=(15, 2), font=('Helvetica', 16)),
                sg.Button('Transacoes', size=(15, 2), font=('Helvetica', 16)),
                sg.Button('Configurações', size=(15, 2), font=('Helvetica', 16)),
                sg.Button('Sair', size=(15, 2), font=('Helvetica', 16))
            ]
        ]
        
        sg.set_options(font=('Helvetica', 16))
        
        self.window = sg.Window('Conta Bancária', self.layout)

    def executar(self): #Executar do programa
        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED or event == 'Sair': #Se apertar o botão sair vai dar um break e sair da tela 
                self.window.close()
                tela_login = TelaLogin()
                tela_login.executar()
                break
            elif event == 'Pix': #Botão do pix 
                cpf_destino = sg.popup_get_text('Digite o CPF do destinatário:') #Capturar cpf destinatário 
                
                if cpf_destino is not None and cpf_destino.strip() != "": #condição para o cpf não ser nulo 
                    cpf_destino = TelaLogin().formatar_cpf(cpf_destino) #Formata cpf no formato de cpf ***.***.***-**
                    
                    if self.verificar_dados("cpf", cpf_destino): #Verifica se o cpf do destinatário existe
                        valor_pix_str = sg.popup_get_text('Digite o valor para Pix:') #Armazena o valor do pix 

                        if valor_pix_str is not None and valor_pix_str.strip() != "": #Verifica se o valor do pix não é nulo 
                            valor_pix = float(valor_pix_str) #Transforma o valor do pix em float 

                            if valor_pix > 0 and valor_pix <= self.saldo: #condicao para pix ser maior que 0 e menor ou igual o saldo da conta
                                data = datetime.now() #Pega a data atual 
                                saldo_cpf_destino = self.obter_saldo(self.obter_dados_cpf("id", cpf_destino)) #chama funcoes para obter o saldo do destinatario
                                self.saldo -= valor_pix #Subtrai o saldo da conta original pelo valor feito do pix 
                                #Atualiza ambos saldos das contas 
                                self.atualizar_saldo(self.id, self.saldo) 
                                self.atualizar_saldo(self.obter_dados_cpf("id", cpf_destino), (saldo_cpf_destino + valor_pix))
                                #Adiciona a transacao no banco de dados 
                                self.cursor.execute("INSERT INTO transacoes (conta_origem_id, conta_destino_id, data_transferencia, valor_transferencia) VALUES (?, ?, ?, ?)", 
                                                    (self.id, self.obter_dados_cpf("id", cpf_destino), data, valor_pix))
                                self.connector.commit()
                                sg.popup(f'Pix de R$ {valor_pix:.2f} para CPF {cpf_destino} realizado com sucesso!')
                                self.window['saldo'].update(f'Saldo: R$ {self.saldo:.2f}')

                            else:
                                sg.popup('Valor de Pix inválido ou saldo insuficiente.')
                    else:
                        sg.popup('CPF inválido. Tente novamente.')

            elif event == 'Depositar': #chama funcao Depositar
                self.depositar()
                self.window['saldo'].update(f'Saldo: R$ {self.saldo:.2f}')
            elif event == 'Transacoes': #Chama tela transacoes
                self.window.close() 
                tela_transacoes = TelaTransacoes(self.cpf)
                tela_transacoes.executar()
                break
            elif event == "Configurações":
                self.window.close()
                tela_configuracoes = TelaConfiguracoes(self.cpf)
                tela_configuracoes.executar()
                break

        self.window.close()

    def depositar(self):
        valor_deposito = sg.popup_get_text('Digite o valor para Depósito:')
    
        if valor_deposito is not None and valor_deposito.strip() != "": #Verifica se o valor_deposito não é nulo 
            valor_deposito = float(valor_deposito) #converte o valor_deposito para float 
            if valor_deposito > 0: #verifica se esse valor é maior que 0 
                data = datetime.now() #pega a data atual e guarda numa variavel 
                #passa os dados do deposito para o banco de dados 
                self.cursor.execute("INSERT INTO depositos (conta_id, data_deposito, valor_deposito) VALUES (?, ?, ?)", (self.id, data, valor_deposito))
                self.saldo += valor_deposito
                self.atualizar_saldo(self.id, self.saldo) 
                sg.popup(f'Depósito de R$ {valor_deposito:.2f} realizado com sucesso!')
            else:
                sg.popup('Valor de depósito inválido.')

class TelaLogin(BaseBanco):
    def __init__(self):
        super().__init__()
        sg.theme('DarkGrey5')
        self.layout = [
            [sg.Text('Banco Marcotti', font=('Helvetica', 24), justification='center')],
            [sg.Text('CPF:', font=('Helvetica', 14), size=(10, 1)), 
             sg.InputText(key='cpf', size=(18, 1), justification='center')],
            [sg.Text('Senha:', font=('Helvetica', 14), size=(10, 1)), 
             sg.InputText(key='senha', size=(18, 1), password_char='*', justification='center')],
            [sg.Button('Login', size=(15, 2), font=('Helvetica', 12)), 
             sg.Button('Cadastro', size=(15, 2), font=('Helvetica', 12)),
             sg.Button('Esqueci Minha Senha', size=(20, 2), font=('Helvetica', 12), button_color=('white', '#0066cc'))]
        ]
        sg.set_options(font=('Helvetica', 12))
        self.window = sg.Window('Login - Cadastro', self.layout)

    def formatar_cpf(self, cpf):
        cpf = ''.join(char for char in cpf if char.isdigit())
        if len(cpf) > 11:
            cpf = cpf[:11]
        cpf_formatado = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
        return cpf_formatado

    def executar(self):
        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED:
                break
            elif event == 'Login':
                cpf = values['cpf']
                senha = values['senha']
                cpf_formatado = self.formatar_cpf(cpf)

                if self.valida_cpf(cpf_formatado):
                    if self.verificar_login(cpf_formatado, senha):
                        self.window.close()
                        tela_conta = TelaConta(cpf_formatado)
                        tela_conta.executar()
                        break
                    else:
                        sg.popup_error('CPF ou senha incorretos. Tente novamente.')
                else:
                    sg.popup_error('Digite um CPF válido!')
            elif event == 'Cadastro':
                self.window.close()
                tela_cadastro = TelaCadastro()
                tela_cadastro.executar()
                break
            elif event == 'Esqueci Minha Senha':
                self.window.close()
                tela_senha = TelaRecuperarSenha()
                tela_senha.executar()
                break

        self.window.close()

class TelaCadastro(BaseBanco):
    def __init__(self):
        super().__init__()
        sg.theme('DarkGrey5')
        self.layout = [
            [sg.Text('Cadastro de Nova Conta', font=('Helvetica', 20), justification='center')],
            [sg.Text('CPF:', font=('Helvetica', 14), size=(10, 1)), sg.InputText(key='cpf', size=(15, 1))],
            [sg.Text('Nome:', font=('Helvetica', 14), size=(10, 1)), sg.InputText(key='nome', size=(30, 1))],
            [sg.Text('Senha:', font=('Helvetica', 14), size=(10, 1)), sg.InputText(key='senha', size=(15, 1), password_char='*')],
            [sg.Text('E-mail:', font=('Helvetica', 14), size=(10, 1)), sg.InputText(key='email', size=(30, 1))],  # Adicionando campo de e-mail
            [sg.Button('Cadastrar', size=(15, 2), font=('Helvetica', 12)), 
             sg.Button('Cancelar', size=(15, 2), font=('Helvetica', 12))]
        ]
        sg.set_options(font=('Helvetica', 12))
        self.window = sg.Window('Cadastro de Nova Conta', self.layout)

    def executar(self):
        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED or event == 'Cancelar':
                self.window.close()
                tela_login = TelaLogin()
                tela_login.executar()
                break
            elif event == 'Cadastrar':
                cpf = TelaLogin().formatar_cpf(values['cpf'])
                nome = values['nome']
                senha = values['senha']
                email = values['email']  #Obtendo o valor do campo de e-mail

                if not cpf or not nome or not senha or not email:
                    sg.popup('Preencha todos os campos.', title='Erro no Cadastro')
                else:
                    if self.valida_cpf(cpf):
                        if self.verificar_dados('cpf', cpf) > 0 or self.verificar_dados('email', email) > 0:
                            sg.popup('CPF já cadastrado. Tente outro.', title='Erro no Cadastro')
                        else:
                            conta = ContaBancaria()
                            conta.abrir_conta(cpf, nome, senha, email)
                            sg.popup('Conta cadastrada com sucesso!', title='Cadastro Concluído')
                            self.window.close()
                    else:
                        sg.popup("Digite um cpf válido!")

        self.window.close()

class TelaRecuperarSenha(BaseBanco):
    def __init__(self):
        super().__init__()
        sg.theme('DarkGrey5')
        self.etapa_atual = 1  # Inicializa a etapa atual
        self.codigo_gerado = None  # Inicializa o código gerado

        # Layout inicial para a primeira etapa
        self.layout_etapa1 = [
            [sg.Text('Recuperar Senha', font=('Helvetica', 20), justification='center')],
            [sg.Text('Digite seu E-mail:', font=('Helvetica', 14), size=(15, 1)),
             sg.InputText(key='email', size=(30, 1))],
            [sg.Button('Recuperar Senha', size=(15, 2), font=('Helvetica', 12)),
             sg.Button('Cancelar', size=(15, 2), font=('Helvetica', 12))]
        ]

        # Layout para a segunda etapa (digitar código)
        self.layout_etapa2 = [
            [sg.Text('Recuperar Senha', font=('Helvetica', 20), justification='center')],
            [sg.Text('Digite o seu Código:', font=('Helvetica', 14), size=(15, 1)),
             sg.InputText(key='codigo', size=(10, 1))],
            [sg.Button('Verificar Código', size=(15, 2), font=('Helvetica', 12)),
            sg.Button('Cancelar', size=(15, 2), font=('Helvetica', 12))]
        ]

        # Configura a janela com o layout inicial
        self.window = sg.Window('Recuperar Senha', self.layout_etapa1)

    def executar(self):
        while True:
            event, values  = self.window.read()
            
            if event == sg.WINDOW_CLOSED or event == 'Cancelar':
                self.window.close()
                tela_login = TelaLogin()
                tela_login.executar()
                break
            elif event == 'Recuperar Senha':
                if self.etapa_atual == 1:
                    email = values['email']
                    if not email:
                        sg.popup("Digite um email!")
                    elif self.verificar_dados("email", email) == 0:
                        sg.popup("Email não existe na base dados")
                    else:
                        self.id = self.obter_dados_email("id", email)
                        self.nome = self.obter_dados_email("nome", email)
                        codigo = str(self.gerar_codigo())

                        self.enviar_email(email, "Codigo para recuperação de senha", f"Olá {self.nome},"
                        + "\n\nRecebemos uma solicitação para redefinir a senha da sua conta no Banco Marcotti. "
                        +"Por favor, utilize o código de verificação abaixo para concluir o processo de recuperação:"
                        + f"\nCódigo de Verificação: {codigo}"
                        + "\nSe você não solicitou essa recuperação, por favor, ignore este e-mail. Caso contrário, "
                        + "acesse a página de recuperação de senha e insira o código para redefinir sua senha."
                        + "\n\n\nAtenciosamente,"
                        + "\nEquipe de Suporte do Banco Marcotti")

                        sg.popup("Enviamos um código para seu email! O código é válido por 5min")

                        self.etapa_atual = 2
                        self.window.close()
                        self.window = sg.Window('Recuperar Senha', self.layout_etapa2)
            elif self.etapa_atual == 2:
                    # Executa a segunda etapa (verifica código)
                    codigo_digitado = values['codigo']
                    if codigo_digitado == self.codigo:
                        sg.popup("Código verificado com sucesso! Prossiga com a redefinição da senha.")
                        self.window.close()
                        tela_redefinir_senha = TelaRedefinicaoSenha(self.id, "TelaRecuperarSenha")
                        tela_redefinir_senha.executar()
                        break
                    else:
                        sg.popup("Código incorreto. Tente novamente.")

        self.window.close()
                    
    def gerar_codigo(self) -> None:
        self.codigo = str(random.randint(1000, 9999))
        self.cursor.execute("INSERT INTO codigos_temporarios (id_usuario, codigo) VALUES (?, ?)", (self.id, self.codigo))
        self.connector.commit()
        return self.codigo
    
class TelaRedefinicaoSenha(BaseBanco):
    def __init__(self, id, tela: str):
        super().__init__()
        self.cpf = self.obter_dados_id("cpf", id)
        self.tela = tela
        self.id = id 

        sg.theme('DarkGrey5')
        self.layout = self.criar_layout()

        # Configura a janela com o layout
        self.window = sg.Window('Redefinição de Senha', self.layout)

    def criar_layout(self):
        return [
            [sg.Text('Redefinir Senha', font=('Helvetica', 20), justification='center')],
            [sg.Text('Digite a Nova Senha:', font=('Helvetica', 14), size=(17, 1)),
             sg.InputText(key='nova_senha', size=(30, 1), password_char='*')],
            [sg.Text('Repita a Nova Senha:', font=('Helvetica', 14), size=(17, 1)),
             sg.InputText(key='repetir_nova_senha', size=(30, 1), password_char='*')],
            [sg.Button('Confirmar', size=(15, 2), font=('Helvetica', 12)),
             sg.Button('Cancelar', size=(15, 2), font=('Helvetica', 12))]
        ]

    def executar(self):
        while True:
            event, values  = self.window.read()

            if event == sg.WINDOW_CLOSED or event == 'Cancelar':
                if self.tela == 'TelaRecuperarSenha':
                    self.window.close()
                    tela_recuperar_senha = TelaRecuperarSenha()
                    tela_recuperar_senha.executar()
                    break
                elif self.tela == 'TelaConfiguracoes':
                    self.window.close()
                    tela_configuracoes = TelaConfiguracoes(self.cpf)
                    tela_configuracoes.executar()
                    break
                else:
                    print("Tela invalida")

            elif event == 'Confirmar':
                nova_senha = values['nova_senha']
                repetir_nova_senha = values['repetir_nova_senha']

                if len(nova_senha) < 6:
                    sg.popup("As senha deve ter mais de 5 caracteres!")

                elif nova_senha == repetir_nova_senha:
                    self.atualizar_senha(self.id, nova_senha)
                    sg.popup("Senha redefinida com sucesso!")
                    break
                else:
                    sg.popup("As senhas devem ser iguais!")

        self.window.close()

class TelaConfiguracoes(BaseBanco):
    def __init__(self, cpf):
        super().__init__()
        self.cpf = cpf 
        self.senha = self.obter_dados_cpf("senha", cpf)
        self.id = self.obter_dados_cpf("id", self.cpf)
        sg.theme('DarkGrey5')
        self.layout = [
            [sg.Text('Configurações', font=('Helvetica', 20), justification='center')],
            [sg.Button('Ajuda', size=(20, 2), font=('Helvetica', 12))],
            [sg.Button('Alterar Senha', size=(20, 2), font=('Helvetica', 12))],
            [sg.Button('Excluir Conta', size=(20, 2), font=('Helvetica', 12))],
            [sg.Button('Voltar', size=(20, 2), font=('Helvetica', 12))]
        ]
        sg.set_options(font=('Helvetica', 12))
        self.window = sg.Window('Configurações', self.layout)

    def executar(self):
        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED or event == 'Voltar':
                self.window.close()
                tela_conta = TelaConta(self.cpf)
                tela_conta.executar()
                break
            elif event == 'Ajuda':
                sg.popup('Texto de ajuda ou informações relevantes.')
            elif event == 'Alterar Senha':
                senha = sg.popup_get_text('Confirme a sua senha:')
                if senha == self.obter_dados_cpf("senha", self.cpf):
                    self.window.close()
                    tela_redefinir_senha = TelaRedefinicaoSenha(self.id,"TelaConfiguracoes")
                    tela_redefinir_senha.executar()
                    break
                elif senha is not None and senha.strip() != "":
                    sg.popup('Senha incorreta, tente novamente')
            elif event == 'Excluir Conta':
                confirmacao = sg.popup_yes_no('Tem certeza que deseja excluir sua conta?', title='Confirmação')
                if confirmacao == 'Yes':
                    senha = sg.popup_get_text("Digite a sua senha")
                    if senha == self.senha:
                        self.deletar_conta(self.id)
                        sg.popup("Conta deletada com sucesso!")
                        self.window.close()
                        tela_login = TelaLogin()
                        tela_login.executar()
                        break

        self.window.close()

if __name__ == "__main__":
    tela_inicial = TelaLogin()
    tela_inicial.executar()



