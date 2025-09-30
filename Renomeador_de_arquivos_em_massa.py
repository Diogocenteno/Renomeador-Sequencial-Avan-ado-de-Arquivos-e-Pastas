#%%
# -*- coding: utf-8 -*- 
"""
Renomeador de Arquivos em Massa 
Versão 2.0 - 2024-09-30
Autor: Mutante
Descrição:
Aplicação para renomear arquivos e/ou pastas de forma sequencial e segura.
Inclui  processo de Backup e a opção de salvar o Log.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import * 
from ttkbootstrap.scrolled import ScrolledFrame 
import re 
import pathlib 
from datetime import datetime 
import locale
import shutil 
from collections import defaultdict 
import time 

class RenomeadorArquivosApp:
    """
    Aplicação Tkinter para renomear arquivos e/ou pastas de forma sequencial e segura.
    Inclui barra de progresso funcional para o processo de Backup e a opção de salvar o Log.
    """
    def __init__(self, master):
        self.master = master
        
        # Configuração inicial da janela
        master.title("Renomeador Sequencial Avançado de Arquivos e Pastas")
        master.geometry("850x800") 
        master.resizable(True, True)

        # Variáveis de controle (mantidas)
        self.style = master.style
        self.caminho_da_pasta = tk.StringVar(value="Nenhuma pasta selecionada")
        self.nome_base_arquivo = tk.StringVar(value="")
        self.formato_selecionado = tk.StringVar(value="Todos os formatos") 
        self.tema_selecionado = tk.StringVar(value=self.style.theme.name)
        self.digitos_sequenciais = tk.IntVar(value=3) 
        self.tipo_renomeacao = tk.IntVar(value=3) 
        self.ponto_de_partida = tk.IntVar(value=1) 
        self.posicao_numero = tk.StringVar(value="Sufixo")
        self.conversao_caixa = tk.StringVar(value="Padrão") 
        self.texto_procurar = tk.StringVar(value="")
        self.texto_substituir = tk.StringVar(value="")
        self.remover_espacos = tk.BooleanVar(value=False)
        self.adicionar_data = tk.BooleanVar(value=False)
        self.adicionar_hora = tk.BooleanVar(value=False) 
        self.modo_recursivo = tk.BooleanVar(value=False) 
        self.criterio_ordenacao = tk.StringVar(value="Por Nome") 
        self.progressbar_value = tk.DoubleVar()
        
        # --- NOVO LAYOUT DE EMPACOTAMENTO COM NOTEBOOK ---
        
        # 1. FRAME DE BOTÕES INFERIOR (FIXO)
        self.frame_botoes = tb.Frame(master, padding=(10, 10)) 
        self.frame_botoes.pack(pady=10, fill=X, side=BOTTOM)

        # 2. NOTEBOOK (ABA) - EXPANSÍVEL NO ESPAÇO RESTANTE
        self.notebook = tb.Notebook(master, bootstyle="primary")
        self.notebook.pack(expand=YES, fill=BOTH, padx=10, pady=(10, 0))

        # --- CRIAÇÃO DAS ABAS ---
        self.tab_config = tb.Frame(self.notebook, padding=5)
        self.tab_logs = tb.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_config, text="1. Configurações de Renomeação")
        self.notebook.add(self.tab_logs, text="2. Log de Atividades")

        # 3. SCROLLEDFRAME DENTRO DA ABA DE CONFIGURAÇÃO
        self.scrolled_content_frame = ScrolledFrame(self.tab_config, autohide=True, bootstyle="primary")
        self.scrolled_content_frame.pack(expand=YES, fill=BOTH)
        
        content_frame = self.scrolled_content_frame 

        # --- DEFINIÇÃO E EMPACOTAMENTO DOS FRAMES DENTRO DO SCROLLEDFRAME ---
        
        # DEFINIÇÃO DOS FRAMES FIXOS (AGORA DENTRO do content_frame)
        self.frame_tema = tb.LabelFrame(content_frame, text="Seleção de Tema", bootstyle="info", padding=(10, 5))
        self.frame_backup = tb.LabelFrame(content_frame, text="Opção de Segurança", bootstyle="danger", padding=(10, 5))
        self.frame_selecao = tb.LabelFrame(content_frame, text="1. Seleção de Pasta", bootstyle="primary", padding=(10, 10))
        self.frame_tipo_item = tb.LabelFrame(content_frame, text="2. Seleção e Ordenação de Itens", bootstyle="primary", padding=(10, 10))
        self.frame_configuracao = tb.LabelFrame(content_frame, text="3. Configuração do Nome Base", bootstyle="info", padding=(10, 10))
        self.frame_sequencia = tb.LabelFrame(content_frame, text="4. Configuração da Sequência", bootstyle="info", padding=(10, 10))
        self.frame_limpeza_data = tb.LabelFrame(content_frame, text="5. Limpeza e Adição de Data/Hora", bootstyle="info", padding=(10, 10))
        self.frame_formato = tb.LabelFrame(content_frame, text="6. Filtro por Formato (Apenas para Arquivos)", bootstyle="info", padding=(10, 10))
        

        # Empacota os frames FIXOS dentro do ScrolledFrame (todos usam side=TOP por padrão)
        self.frame_tema.pack(pady=(10, 5), padx=10, fill=X, expand=False)
        self.frame_backup.pack(pady=5, padx=10, fill=X, expand=False)
        self.frame_selecao.pack(pady=5, padx=10, fill=X, expand=False)
        self.frame_tipo_item.pack(pady=5, padx=10, fill=X, expand=False)
        self.frame_configuracao.pack(pady=5, padx=10, fill=X, expand=False)
        self.frame_sequencia.pack(pady=5, padx=10, fill=X, expand=False)
        self.frame_limpeza_data.pack(pady=5, padx=10, fill=X, expand=False)
        self.frame_formato.pack(pady=5, padx=10, fill=X, expand=False)
        
        # --- Componentes restantes (mantidos) ---

        # --- Componentes do Frame de Seleção de Tema ---
        tb.Label(self.frame_tema, text="Tema:", bootstyle="info").pack(side=LEFT, padx=(0, 5))
        self.opcoes_temas = list(self.style.theme_names())
        self.combobox_tema = tb.Combobox(self.frame_tema, textvariable=self.tema_selecionado,
                                             values=self.opcoes_temas, state="readonly", font=('Arial', 9))
        self.combobox_tema.set(self.style.theme.name)
        self.combobox_tema.pack(side=LEFT, fill=X, expand=True)
        self.combobox_tema.bind("<<ComboboxSelected>>", self.aplicar_tema)
        
        # --- Componentes do Frame de Backup ---
        self.botao_backup = tb.Button(
            self.frame_backup, 
            text="Fazer Backup da Pasta Selecionada Agora (RECOMENDADO)", 
            command=self.fazer_backup, 
            bootstyle="danger"
        )
        self.botao_backup.pack(pady=5, fill=X, expand=True)


        # --- Componentes do Frame de Seleção de Pasta ---
        tb.Label(self.frame_selecao, text="Pasta Selecionada:", font=('Arial', 10, 'bold')).pack(anchor=W, pady=(0,5))
        self.label_caminho = tb.Label(self.frame_selecao, textvariable=self.caminho_da_pasta, 
                                        wraplength=700, justify=LEFT, relief=GROOVE, font=('Arial', 10)) 
        self.label_caminho.pack(fill=X, pady=5)
        tb.Button(self.frame_selecao, text="Selecionar Pasta", command=self.selecionar_pasta, bootstyle="primary").pack(pady=5)

        
        # --- Componentes do Frame de Seleção e Ordenação de Itens ---
        frame_tipo_recursivo = tb.Frame(self.frame_tipo_item)
        frame_tipo_recursivo.pack(fill=X, expand=True, pady=(0, 5))
        
        tb.Label(frame_tipo_recursivo, text="Itens a Renomear:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0,5))
        tb.Radiobutton(frame_tipo_recursivo, text="Arquivos", variable=self.tipo_renomeacao, value=1, command=self.atualizar_previa, bootstyle="primary-round-toggle").pack(side=LEFT, padx=5)
        tb.Radiobutton(frame_tipo_recursivo, text="Pastas", variable=self.tipo_renomeacao, value=2, command=self.atualizar_previa, bootstyle="primary-round-toggle").pack(side=LEFT, padx=5)
        tb.Radiobutton(frame_tipo_recursivo, text="Ambos", variable=self.tipo_renomeacao, value=3, command=self.atualizar_previa, bootstyle="primary-round-toggle").pack(side=LEFT, padx=5)

        tb.Checkbutton(frame_tipo_recursivo, text="Incluir Subpastas (Recursivo)", variable=self.modo_recursivo, 
                        command=self.atualizar_previa, bootstyle="danger-round-toggle").pack(side=RIGHT, padx=5)

        frame_criterio_ordenacao = tb.Frame(self.frame_tipo_item)
        frame_criterio_ordenacao.pack(fill=X, pady=(5, 0))
        
        tb.Label(frame_criterio_ordenacao, text="Critério de Ordenação da Sequência:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.opcoes_ordenacao = ["Por Nome", "Por Data de Modificação", "Por Data de Criação"]
        self.combo_ordenacao = tb.Combobox(frame_criterio_ordenacao, textvariable=self.criterio_ordenacao, 
                                             values=self.opcoes_ordenacao, state="readonly", font=('Arial', 10), width=25)
        self.combo_ordenacao.pack(side=LEFT, pady=5)
        self.combo_ordenacao.bind("<<ComboboxSelected>>", self.atualizar_previa)


        # --- Componentes do Frame de Configuração do Nome Base ---
        frame_nome_base = tb.Frame(self.frame_configuracao)
        frame_nome_base.pack(fill=X, pady=(0, 5))
        
        tb.Label(frame_nome_base, text="Nome Base (ex: 'Relatorio'):", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.entrada_nome_base = tb.Entry(frame_nome_base, textvariable=self.nome_base_arquivo, font=('Arial', 10))
        self.entrada_nome_base.pack(side=LEFT, pady=5, fill=X, expand=True)
        self.entrada_nome_base.bind("<KeyRelease>", self.atualizar_previa)

        frame_caixa = tb.Frame(self.frame_configuracao)
        frame_caixa.pack(fill=X, pady=(5, 0))
        tb.Label(frame_caixa, text="Conversão de Caixa (Nome Base):", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.opcoes_caixa = ["Padrão", "Minúsculas", "Maiúsculas"]
        self.combo_caixa = tb.Combobox(frame_caixa, textvariable=self.conversao_caixa, values=self.opcoes_caixa, 
                                             state="readonly", font=('Arial', 10), width=15)
        self.combo_caixa.pack(side=LEFT, pady=5)
        self.combo_caixa.bind("<<ComboboxSelected>>", self.atualizar_previa)


        # --- Componentes do Frame de Sequência Avançada ---
        frame_seq_linha1 = tb.Frame(self.frame_sequencia)
        frame_seq_linha1.pack(fill=X, pady=(5, 5))
        
        tb.Label(frame_seq_linha1, text="Dígitos Sequenciais (Padding, ex: 3 para 001):", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.spinbox_digitos = tb.Spinbox(frame_seq_linha1, from_=1, to=8, textvariable=self.digitos_sequenciais, font=('Arial', 10), width=5, command=self.atualizar_previa)
        self.spinbox_digitos.pack(side=LEFT, pady=5, padx=(0, 30))

        tb.Label(frame_seq_linha1, text="Ponto de Partida (Início da Contagem):", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.spinbox_partida = tb.Spinbox(frame_seq_linha1, from_=1, to=9999, textvariable=self.ponto_de_partida, font=('Arial', 10), width=5, command=self.atualizar_previa)
        self.spinbox_partida.pack(side=LEFT, pady=5)
        
        frame_seq_linha2 = tb.Frame(self.frame_sequencia)
        frame_seq_linha2.pack(fill=X, pady=(5, 0))
        
        tb.Label(frame_seq_linha2, text="Posição do Número Sequencial:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        tb.Radiobutton(frame_seq_linha2, text="Sufixo (NomeBase_001)", variable=self.posicao_numero, value="Sufixo", command=self.atualizar_previa, bootstyle="primary-round-toggle").pack(side=LEFT, padx=10)
        tb.Radiobutton(frame_seq_linha2, text="Prefixo (001_NomeBase)", variable=self.posicao_numero, value="Prefixo", command=self.atualizar_previa, bootstyle="primary-round-toggle").pack(side=LEFT, padx=10)


        # --- Componentes do Frame de Limpeza e Data ---
        frame_limp_linha1 = tb.Frame(self.frame_limpeza_data)
        frame_limp_linha1.pack(fill=X, pady=(5, 5))
        
        tb.Label(frame_limp_linha1, text="Procurar:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.entrada_procurar = tb.Entry(frame_limp_linha1, textvariable=self.texto_procurar, font=('Arial', 10), width=20)
        self.entrada_procurar.pack(side=LEFT, pady=5, padx=(0, 15))
        self.entrada_procurar.bind("<KeyRelease>", self.atualizar_previa)

        tb.Label(frame_limp_linha1, text="Substituir por:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.entrada_substituir = tb.Entry(frame_limp_linha1, textvariable=self.texto_substituir, font=('Arial', 10), width=20)
        self.entrada_substituir.pack(side=LEFT, pady=5)
        self.entrada_substituir.bind("<KeyRelease>", self.atualizar_previa)
        
        frame_limp_linha2 = tb.Frame(self.frame_limpeza_data)
        frame_limp_linha2.pack(fill=X, pady=(5, 0))
        
        tb.Label(frame_limp_linha2, text="Opções de Prefixo (Data de Modificação):", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        
        tb.Checkbutton(frame_limp_linha2, text="Adicionar Data (DD-MM-YYYY)", variable=self.adicionar_data, 
                        command=self.atualizar_previa, bootstyle="success-round-toggle").pack(side=LEFT, padx=5)
                        
        tb.Checkbutton(frame_limp_linha2, text="Adicionar Hora (HH-MM)", variable=self.adicionar_hora, 
                        command=self.atualizar_previa, bootstyle="success-round-toggle").pack(side=LEFT, padx=5)
                        
        tb.Checkbutton(frame_limp_linha2, text="Remover Espaços (Substitui ' ' por '_')", variable=self.remover_espacos, 
                        command=self.atualizar_previa, bootstyle="info-round-toggle").pack(side=LEFT, padx=15)


        # --- Componentes do Frame de Seleção de Formato ---
        tb.Label(self.frame_formato, text="Filtro de Arquivos (será ignorado para 'Apenas Pastas'):", font=('Arial', 10, 'bold')).pack(anchor=W, pady=(0,5))
        self.opcoes_formato = ["Todos os formatos", ".pdf", ".xlsx", ".docx", ".csv", ".txt", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".zip", ".rar", ".7z", ".pptx", ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".html", ".css", ".js", ".py"] 
        self.combobox_formato = tb.Combobox(self.frame_formato, textvariable=self.formato_selecionado, 
                                             values=self.opcoes_formato, state="readonly", font=('Arial', 10))
        self.combobox_formato.set("Todos os formatos") 
        self.combobox_formato.pack(pady=5, fill=X, expand=True)
        self.combobox_formato.bind("<<ComboboxSelected>>", self.atualizar_previa)

        # --- Componentes da ABA DE LOGS ---
        tb.Label(self.tab_logs, text="Log de Atividades:", font=('Arial', 10, 'bold')).pack(anchor=W, pady=(0,5))
        self.log_area = scrolledtext.ScrolledText(self.tab_logs, state='disabled', wrap=WORD, font=('Consolas', 9)) 
        self.log_area.pack(expand=True, fill=BOTH)

        # --- Componentes do Frame de Botões (e Progress Bar) ---
        self.progressbar = tb.Progressbar(self.frame_botoes, orient=HORIZONTAL, mode='determinate', 
                                             variable=self.progressbar_value, bootstyle="success")
        self.progressbar.pack(side=TOP, fill=X, pady=(0, 10))

        frame_botoes_acao = tb.Frame(self.frame_botoes)
        frame_botoes_acao.pack(fill=X, expand=False)

        tb.Button(frame_botoes_acao, text="Gerar Prévia no Log", command=self.gerar_previa_no_log, bootstyle="info").pack(side=LEFT, padx=5, fill=X, expand=True)
        tb.Button(frame_botoes_acao, text="Abrir Prévia em Janela", command=self.abrir_janela_previa, bootstyle="info-outline").pack(side=LEFT, padx=5, fill=X, expand=True)
        self.botao_renomear_ttk = tb.Button(frame_botoes_acao, text="Renomear Itens", command=self.renomear_arquivos, state='disabled', bootstyle="success")
        self.botao_renomear_ttk.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        # NOVO BOTÃO: Salvar Log
        tb.Button(frame_botoes_acao, text="Salvar Log", command=self.salvar_log, bootstyle="secondary-outline").pack(side=RIGHT, padx=5, fill=X, expand=True)
        tb.Button(frame_botoes_acao, text="Limpar Logs", command=self._limpar_logs, bootstyle="secondary").pack(side=RIGHT, padx=5, fill=X, expand=True)
        
    def _count_total_items(self, src):
        """Conta o número total de arquivos e diretórios na pasta de origem para o progresso."""
        count = 0
        for root, dirs, files in os.walk(src):
            count += len(dirs) + len(files)
        return count

    def copy_with_progress(self, src, dst, total_items):
        """Copia recursivamente, atualizando a barra de progresso."""
        copied_count = 0
        
        # Cria o diretório raiz de destino
        pathlib.Path(dst).mkdir(parents=True, exist_ok=True)
        
        for root, dirs, files in os.walk(src):
            # Obtém o caminho relativo do diretório atual em relação ao src
            relative_path = pathlib.Path(root).relative_to(src)
            current_dst_dir = pathlib.Path(dst) / relative_path

            # 1. Cria diretórios no destino e atualiza progresso
            for dir_name in dirs:
                # O copytree do shutil não copia symlinks se for usado o os.walk
                # Aqui, garantimos a criação de todos os diretórios.
                (current_dst_dir / dir_name).mkdir(parents=True, exist_ok=True)
                copied_count += 1
                progresso = (copied_count / total_items) * 100
                self.progressbar_value.set(progresso)
                self.master.update_idletasks()
            
            # 2. Copia arquivos e atualiza progresso
            for file_name in files:
                src_file = pathlib.Path(root) / file_name
                dst_file = current_dst_dir / file_name
                
                # shutils.copy2 preserva metadados (data de modificação, etc.)
                shutil.copy2(src_file, dst_file)
                
                copied_count += 1
                progresso = (copied_count / total_items) * 100
                self.progressbar_value.set(progresso)
                self.master.update_idletasks()
        
        self.progressbar_value.set(100)
        self.master.update_idletasks()


    def fazer_backup(self):
        """Copia a pasta selecionada para um destino de backup com barra de progresso."""
        pasta_origem_str = self.caminho_da_pasta.get()
        pasta_origem = pathlib.Path(pasta_origem_str)

        if not pasta_origem.is_dir():
            messagebox.showerror("Erro de Backup", "Nenhuma pasta válida foi selecionada para o backup.")
            return

        # 1. Selecionar o destino do backup
        destino_backup_base_str = filedialog.askdirectory(title=f"Selecione o Destino do Backup da Pasta '{pasta_origem.name}'")
        if not destino_backup_base_str:
            self._log_message("Backup cancelado pelo usuário.")
            self.progressbar_value.set(0)
            return

        # 2. Criar um nome de pasta de backup único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_backup = f"Backup_Renomear_{pasta_origem.name}_{timestamp}"
        pasta_destino_completa = pathlib.Path(destino_backup_base_str) / nome_backup

        # 3. Confirmação
        confirmacao = messagebox.askyesno(
            "Confirmar Backup",
            f"Você irá copiar a pasta:\n'{pasta_origem_str}'\n\nPara a pasta de destino:\n'{pasta_destino_completa}'\n\nConfirmar o início da cópia recursiva?"
        )
        if not confirmacao:
            self._log_message("Cópia de backup cancelada após a confirmação.")
            self.progressbar_value.set(0)
            return

        self._log_message(f"Iniciando backup recursivo de '{pasta_origem.name}' para '{pasta_destino_completa}'...")

        self.progressbar_value.set(0) # Inicia a barra de progresso

        try:
            total_items = self._count_total_items(pasta_origem)
            
            # NOVO: Chamada para a função de cópia com progresso
            self.copy_with_progress(pasta_origem, pasta_destino_completa, total_items)
            
            self._log_message("\n--- Backup Concluído ---")
            self._log_message(f"Cópia de backup realizada com sucesso para: {pasta_destino_completa}")
            messagebox.showinfo("Sucesso no Backup", f"A pasta de backup foi criada com sucesso em:\n{pasta_destino_completa}")

        except Exception as e:
            self._log_message(f"\nERRO INESPERADO: Falha no backup. Detalhes: {e}")
            messagebox.showerror("Erro de Backup", f"Ocorreu um erro inesperado durante o backup. Detalhes: {e}")
            self.progressbar_value.set(0)


    def aplicar_tema(self, event=None):
        """Aplica o tema selecionado à aplicação."""
        if self.master.winfo_exists():
            tema_escolhido = self.tema_selecionado.get()
            self.style.theme_use(tema_escolhido)
            self._log_message(f"Tema alterado para: {tema_escolhido}")

            # Atualiza bootstyle para os frames
            self.frame_tema.config(bootstyle="info")
            self.frame_backup.config(bootstyle="danger") 
            self.frame_selecao.config(bootstyle="primary")
            self.frame_tipo_item.config(bootstyle="primary")
            self.frame_configuracao.config(bootstyle="info")
            self.frame_sequencia.config(bootstyle="info")
            self.frame_limpeza_data.config(bootstyle="info")
            self.frame_formato.config(bootstyle="info")
            
            try:
                bg_color = self.style.lookup('TEntry', 'background')
            except:
                bg_color = self.master.cget('bg')
            self.log_area.config(bg=bg_color)

    def _sanitizar_nome_base(self, nome_base, caminho_completo_item=""):
        """
        Remove ou substitui caracteres inválidos, aplica limpeza de texto, conversão de caixa
        e adiciona prefixo de data/hora no padrão brasileiro, usando separadores legais.
        """
        
        # 1. Aplica limpeza de texto (Procurar/Substituir)
        texto_procurar = self.texto_procurar.get()
        texto_substituir = self.texto_substituir.get()
        if texto_procurar:
            try:
                # Usa re.sub para substituir todas as ocorrências
                nome_base = re.sub(re.escape(texto_procurar), texto_substituir, nome_base, flags=re.IGNORECASE)
            except Exception as e:
                pass

        # 2. Adiciona Prefixo de Data/Hora (se ativado)
        data_prefixo = ""
        if self.adicionar_data.get() or self.adicionar_hora.get():
            try:
                # Obtém a data de modificação (mtime) do item
                timestamp_mod = os.path.getmtime(caminho_completo_item)
                data_mod = datetime.fromtimestamp(timestamp_mod)
                
                # Usa formatos com separadores legais (hífen)
                data_parte = data_mod.strftime("%d-%m-%Y") if self.adicionar_data.get() else ""
                hora_parte = data_mod.strftime("%H-%M") if self.adicionar_hora.get() else ""
                
                # Monta a string do prefixo
                if data_parte and hora_parte:
                    data_prefixo = f"{data_parte}_{hora_parte}_"
                elif data_parte:
                    data_prefixo = f"{data_parte}_"
                elif hora_parte:
                    data_prefixo = f"{hora_parte}_"
                
            except Exception as e:
                data_prefixo = ""

        # 3. Aplica conversão de caixa (apenas no nome base)
        caixa = self.conversao_caixa.get()
        if caixa == "Minúsculas":
            nome_base = nome_base.lower()
        elif caixa == "Maiúsculas":
            nome_base = nome_base.upper()
        
        # 4. Remove espaços se o checkbox estiver marcado
        if self.remover_espacos.get():
            nome_base = nome_base.replace(' ', '_')
        
        # 5. Sanitiza caracteres inválidos
        caracteres_invalidos = r'[\\/:*?"<>|]'
        nome_sanitizado = re.sub(caracteres_invalidos, '_', nome_base).strip()
        
        return data_prefixo + nome_sanitizado

    def _log_message(self, message):
        """Adiciona uma mensagem à área de log."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def _limpar_logs(self):
        """Limpa a área de log."""
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self._log_message("Logs limpos.")

    def salvar_log(self):
        """Salva o conteúdo da área de log em um arquivo de texto."""
        log_content = self.log_area.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showinfo("Salvar Log", "O log de atividades está vazio.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_sugerido = f"Log_Renomeador_{timestamp}.txt"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=nome_sugerido,
            title="Salvar Log de Atividades",
            filetypes=[("Arquivos de Texto", "*.txt")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("--- Log de Atividades do Renomeador Sequencial Avançado ---\n")
                    f.write(log_content.strip())
                    f.write("\n---------------------------------------------------------------\n")
                messagebox.showinfo("Sucesso", f"Log salvo com sucesso em:\n{file_path}")
                self._log_message(f"Log salvo em: {file_path}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo de log. Erro: {e}")
                self._log_message(f"ERRO: Falha ao salvar o log. Detalhes: {e}")

    def selecionar_pasta(self):
        """Abre uma caixa de diálogo para o usuário selecionar uma pasta."""
        diretorio_selecionado = filedialog.askdirectory(title="Selecione a Pasta com os Arquivos e Pastas")
        if diretorio_selecionado:
            self.caminho_da_pasta.set(diretorio_selecionado)
            self._log_message(f"Pasta selecionada: {diretorio_selecionado}")
            self.botao_renomear_ttk.config(state='normal') 
            self.gerar_previa_no_log() 
        else:
            self.caminho_da_pasta.set("Nenhuma pasta selecionada")
            self._log_message("Seleção de pasta cancelada.")
            self.botao_renomear_ttk.config(state='disabled')
            self.progressbar_value.set(0)

    def atualizar_previa(self, event=None):
        """Chama a geração de prévia quando as configurações são alteradas."""
        self.gerar_previa_no_log()

    def _obter_novo_nome_unico(self, pasta, prefixo, extensao):
        """
        Gera um nome de arquivo ou pasta único, adicionando um sufixo numérico se necessário.
        """
        pasta_path = pathlib.Path(pasta) 
        
        contador_sufixo_duplicado = 0
        novo_nome_tentativa = f"{prefixo}{extensao}"
        caminho_tentativa = pasta_path / novo_nome_tentativa

        while caminho_tentativa.exists(): 
            contador_sufixo_duplicado += 1
            novo_nome_tentativa = f"{prefixo} ({contador_sufixo_duplicado}){extensao}"
            caminho_tentativa = pasta_path / novo_nome_tentativa
            
            if contador_sufixo_duplicado > 9999:
                raise Exception("Excesso de tentativas para criar nome único.")
            
        return novo_nome_tentativa

    def _obter_arquivos_filtrados_e_ordenados(self, pasta):
        """
        Método helper que obtém a lista de arquivos e pastas a serem processados.
        Retorna uma lista de tuplas (nome_original, é_pasta, extensão, caminho_completo).
        
        Implementa ordenação por profundidade (Bottom-Up) para renomeação recursiva.
        """
        tipo_selecionado = self.tipo_renomeacao.get() 
        formato_alvo = self.formato_selecionado.get()
        modo_recursivo = self.modo_recursivo.get()
        criterio_ordenacao = self.criterio_ordenacao.get()
        
        itens_a_processar = []
        pasta_path = pathlib.Path(pasta)
        
        if not pasta_path.is_dir():
             return []
        
        if modo_recursivo:
            for root, dirs, files in os.walk(pasta_path, topdown=False): # bottom-up no os.walk é melhor para renomear pastas
                caminho_atual = pathlib.Path(root)
                
                # 1. Processa Arquivos (para garantir que arquivos são renomeados antes de suas pastas)
                if tipo_selecionado == 1 or tipo_selecionado == 3:
                    for nome_arquivo in files:
                        caminho_completo = caminho_atual / nome_arquivo
                        extensao = caminho_completo.suffix
                        if formato_alvo == "Todos os formatos" or extensao.lower() == formato_alvo.lower():
                            itens_a_processar.append((nome_arquivo, False, extensao, caminho_completo))

                # 2. Processa Pastas
                if tipo_selecionado == 2 or tipo_selecionado == 3:
                    # Note: Para renomear a pasta, usamos o nome da pasta em 'dirs'
                    for nome_dir in dirs:
                         caminho_completo = caminho_atual / nome_dir
                         # Se a pasta é a raiz, não queremos processá-la aqui.
                         if caminho_completo != pasta_path:
                            itens_a_processar.append((nome_dir, True, "", caminho_completo))
        else:
            # Modo não recursivo (apenas pasta principal)
            for nome_item in os.listdir(pasta_path):
                caminho_completo_item = pasta_path / nome_item
                
                if caminho_completo_item.is_symlink():
                    continue

                é_pasta = caminho_completo_item.is_dir()
                é_arquivo = caminho_completo_item.is_file()
                
                if é_pasta:
                    if tipo_selecionado == 2 or tipo_selecionado == 3:
                        itens_a_processar.append((nome_item, True, "", caminho_completo_item)) 
                
                elif é_arquivo:
                    if tipo_selecionado == 1 or tipo_selecionado == 3:
                        extensao = caminho_completo_item.suffix
                        if formato_alvo == "Todos os formatos" or extensao.lower() == formato_alvo.lower():
                            itens_a_processar.append((nome_item, False, extensao, caminho_completo_item))

        # --- Lógica de Ordenação ATUALIZADA (Bottom-Up com agrupamento por pasta) ---
        def obter_chave_ordenacao(item):
            caminho_completo = item[3]
            
            # Profundidade do caminho: usada para garantir a ordem Bottom-Up (Decrescente)
            profundidade = len(caminho_completo.parts) 
            
            # Chave principal de agrupamento: Diretório Pai (Para resetar o contador)
            diretorio_pai = str(caminho_completo.parent)

            if criterio_ordenacao == "Por Nome":
                # Ordenação: 1. Profundidade (Decrescente), 2. Diretório Pai (Alfabético), 3. Tipo, 4. Nome
                return (-profundidade, diretorio_pai, not item[1], item[0].lower())
            
            elif criterio_ordenacao == "Por Data de Modificação":
                try:
                    # Ordenação: 1. Profundidade (Decrescente), 2. Diretório Pai, 3. Data de Modificação
                    return (-profundidade, diretorio_pai, os.path.getmtime(caminho_completo))
                except:
                    return (-profundidade, diretorio_pai, 0)
            
            elif criterio_ordenacao == "Por Data de Criação":
                try:
                    # Ordenação: 1. Profundidade (Decrescente), 2. Diretório Pai, 3. Data de Criação
                    return (-profundidade, diretorio_pai, os.path.getctime(caminho_completo))
                except:
                    return (-profundidade, diretorio_pai, 0)
            
            # Retorno padrão para garantir que a profundidade e o diretório pai sejam sempre chaves de agrupamento
            return (-profundidade, diretorio_pai, item[0].lower())
        
        itens_a_processar.sort(key=obter_chave_ordenacao) 
        
        return itens_a_processar

    def _gerar_lista_previa(self):
        """
        Gera a lista de strings da prévia da renomeação, aplicando a numeração resetada
        por pasta (para a prévia).
        """
        pasta = self.caminho_da_pasta.get()
        if not pathlib.Path(pasta).is_dir():
            return [f"Erro: Pasta inválida: '{pasta}'."]

        nome_base_digitado = self.nome_base_arquivo.get()
        digitos = self.digitos_sequenciais.get()
        ponto_partida = self.ponto_de_partida.get()
        posicao_numero = self.posicao_numero.get()
        
        mapa_tipo = {1: "Apenas Arquivos", 2: "Apenas Pastas", 3: "Arquivos e Pastas"}
        tipo_selecionado_str = mapa_tipo.get(self.tipo_renomeacao.get(), "Desconhecido")
        
        recursivo_str = " (RECURSIVO)" if self.modo_recursivo.get() else ""
        
        mensagens = [f"Gerando prévia para: {tipo_selecionado_str}{recursivo_str} | Ordenação: {self.criterio_ordenacao.get()} | Partida: {ponto_partida} | Padding: {digitos} dígitos | Posição: {posicao_numero} | **CONTADOR REINICIADO POR PASTA**",
                     f"Pasta Raiz: {pasta}"]
        
        itens_a_processar = self._obter_arquivos_filtrados_e_ordenados(pasta)
        
        if not itens_a_processar:
            mensagens.append(f"Nenhum item encontrado com o critério de seleção e filtro atuais.")
        else:
            mensagens.append("\n--- Prévia da Renomeação ---")
            
            # Dicionário para rastrear a contagem de cada pasta
            contadores_por_pasta = defaultdict(lambda: ponto_partida) 
            
            for nome_antigo, é_pasta, extensao, caminho_completo in itens_a_processar:
                
                # Chave é o caminho absoluto da pasta (diretório)
                pasta_chave = str(caminho_completo.parent)
                contador_atual = contadores_por_pasta[pasta_chave]
                
                numero_formatado = str(contador_atual).zfill(digitos) 
                tipo_item = "Pasta" if é_pasta else "Arquivo"
                
                nome_base_com_limpeza = self._sanitizar_nome_base(nome_base_digitado, caminho_completo)

                if nome_base_com_limpeza:
                    if posicao_numero == "Prefixo":
                        prefixo_base = f"{numero_formatado}_{nome_base_com_limpeza}"
                    else: # Sufixo
                        prefixo_base = f"{nome_base_com_limpeza}_{numero_formatado}"
                else:
                    prefixo_base = f"{numero_formatado}"

                novo_nome_previsto = f"{prefixo_base}{extensao}"
                
                try:
                    caminho_relativo = caminho_completo.parent.relative_to(pasta)
                    caminho_log = str(caminho_relativo)
                except ValueError:
                    caminho_log = str(caminho_completo.parent)

                if caminho_log == ".":
                    caminho_log = ""
                else:
                    caminho_log = f" ({caminho_log}/)"
                        
                mensagens.append(f"[{tipo_item}]{caminho_log} De: '{nome_antigo}' -> Para: '{novo_nome_previsto}'") 
                
                # Atualiza o contador APENAS para a pasta atual
                contadores_por_pasta[pasta_chave] += 1
                
            mensagens.append("---------------------------")
        
        return mensagens


    def gerar_previa_no_log(self):
        """Mostra uma prévia no log da janela principal e REATIVA/DESATIVA O BOTÃO DE RENOMEAR."""
        # Se a aba de logs não for a atual, troca para ela ao gerar a prévia.
        self.notebook.select(self.tab_logs)
        
        self._limpar_logs()
        pasta = self.caminho_da_pasta.get()

        if not pathlib.Path(pasta).is_dir():
            self.botao_renomear_ttk.config(state='disabled')
            self._log_message("Erro: Pasta inválida. Por favor, selecione uma pasta válida.")
            return
        
        mensagens = self._gerar_lista_previa()
        
        # Verifica a última linha da prévia. Se for a mensagem de "Nenhum item encontrado", desativa o botão.
        # Caso contrário, ativa.
        if len(mensagens) > 1 and "Nenhum item encontrado" in mensagens[-2]:
             self.botao_renomear_ttk.config(state='disabled')
        else:
             # Só ativa se o nome base não for vazio e houver itens. (A verificação de itens está no if acima)
             # A verificação de nome_base é importante para evitar renomeações acidentais, a menos que se queira apenas numerar.
             # Se nome_base_arquivo for vazio, o nome final será apenas o número. Permitir.
             self.botao_renomear_ttk.config(state='normal')

        for msg in mensagens:
            self._log_message(msg)


    def abrir_janela_previa(self):
        """Abre uma nova janela Toplevel para exibir a prévia."""
        mensagens_previa = self._gerar_lista_previa()
        
        if not mensagens_previa or "Erro: Pasta inválida" in mensagens_previa[0]:
            messagebox.showerror("Erro", "Pasta inválida ou não selecionada para gerar a prévia.")
            return
            
        janela_previa = tb.Toplevel(self.master)
        janela_previa.title("Prévia da Renomeação")
        janela_previa.geometry("600x600")

        frame_conteudo = tb.Frame(janela_previa, padding=10)
        frame_conteudo.pack(expand=True, fill=BOTH)

        tb.Label(frame_conteudo, text="Prévia Completa da Renomeação:", font=('Arial', 12, 'bold')).pack(anchor=W, pady=(0,5))
        
        try:
            bg_color = self.style.lookup('TEntry', 'background')
        except:
            bg_color = self.master.cget('bg')
            
        log_previa = scrolledtext.ScrolledText(frame_conteudo, state='disabled', wrap=WORD, bg=bg_color, font=('Consolas', 9))
        log_previa.pack(expand=True, fill=BOTH)

        log_previa.config(state='normal')
        for msg in mensagens_previa:
            log_previa.insert(tk.END, msg + "\n")
        log_previa.config(state='disabled')
        log_previa.see(tk.END)

    def renomear_arquivos(self):
        """
        Executa a renomeação dos arquivos e pastas na pasta selecionada.
        Implementa a numeração resetada por pasta e a ordenação.
        """
        pasta = self.caminho_da_pasta.get()
        pasta_path = pathlib.Path(pasta)
        if not pasta_path.is_dir():
            messagebox.showerror("Erro", "Pasta inválida ou não selecionada.")
            return

        nome_base_digitado = self.nome_base_arquivo.get()
        digitos = self.digitos_sequenciais.get()
        ponto_partida = self.ponto_de_partida.get()
        posicao_numero = self.posicao_numero.get()

        itens_a_processar = self._obter_arquivos_filtrados_e_ordenados(pasta)
        total_itens = len(itens_a_processar)

        if total_itens == 0:
            messagebox.showinfo("Aviso", "Nenhum item encontrado para renomear com o critério de seleção e filtro atuais.")
            self.progressbar_value.set(0)
            return
            
        mapa_tipo = {1: "Apenas Arquivos", 2: "Apenas Pastas", 3: "Arquivos e Pastas"}
        tipo_selecionado_str = mapa_tipo.get(self.tipo_renomeacao.get(), "Itens")
        recursivo_str = " (MODO RECURSIVO)" if self.modo_recursivo.get() else ""
        
        confirmacao = messagebox.askyesno(
            "Confirmação de Renomeação",
            f"Tem certeza que deseja renomear **{total_itens} item(s)** ({tipo_selecionado_str}){recursivo_str} em '{pasta}'?\n\n**A numeração será reiniciada em cada subpasta.**\n\n**ESTA AÇÃO É IRREVERSÍVEL! Recomendamos um backup.**" 
        )

        if not confirmacao:
            self._log_message("Renomeação cancelada pelo usuário.")
            self.progressbar_value.set(0) 
            return

        self._log_message(f"\nIniciando renomeação de {tipo_selecionado_str}{recursivo_str} | Partida: {ponto_partida} | Ordenação: {self.criterio_ordenacao.get()} | **CONTADOR REINICIADO POR PASTA**")
        
        arquivos_renomeados = 0
        erros_renomeacao = 0

        # Dicionário para rastrear a contagem de cada pasta
        contadores_por_pasta = defaultdict(lambda: ponto_partida) 
        
        for i, (nome_antigo, é_pasta, extensao, caminho_completo) in enumerate(itens_a_processar):
            
            # Chave é o caminho absoluto da pasta (diretório)
            pasta_chave = str(caminho_completo.parent)
            contador_atual = contadores_por_pasta[pasta_chave]
            
            numero_formatado = str(contador_atual).zfill(digitos) 
            tipo_item = "Pasta" if é_pasta else "Arquivo"
            
            nome_base_com_limpeza = self._sanitizar_nome_base(nome_base_digitado, caminho_completo)
            
            if nome_base_com_limpeza:
                if posicao_numero == "Prefixo":
                    prefixo_base = f"{numero_formatado}_{nome_base_com_limpeza}"
                else: # Sufixo
                    prefixo_base = f"{nome_base_com_limpeza}_{numero_formatado}"
            else:
                prefixo_base = f"{numero_formatado}"
            
            pasta_destino = caminho_completo.parent
            
            try:
                # O novo nome_final já inclui a lógica de unicidade (sufixo de duplicidade)
                novo_nome_final = self._obter_novo_nome_unico(pasta_destino, prefixo_base, extensao)
                caminho_novo = pasta_destino / novo_nome_final

                if nome_antigo != novo_nome_final:
                    os.rename(caminho_completo, caminho_novo) 
                    
                    try:
                        caminho_log = str(caminho_completo.parent.relative_to(pasta))
                    except ValueError:
                         caminho_log = str(caminho_completo.parent)

                    if caminho_log == ".":
                        caminho_log = ""
                    else:
                        caminho_log = f" ({caminho_log}/)"
                    
                    self._log_message(f"Renomeado [{tipo_item}]{caminho_log}: '{nome_antigo}' -> '{novo_nome_final}'")
                    arquivos_renomeados += 1
                else:
                    self._log_message(f"Ignorado [{tipo_item}]: '{nome_antigo}' - O nome final seria o mesmo que o original.")

                # Atualiza o contador APENAS para a pasta atual
                contadores_por_pasta[pasta_chave] += 1
                
            except PermissionError as e:
                self._log_message(f"Erro de permissão ao renomear o item '{nome_antigo}' em '{caminho_completo.parent}'. Verifique se está em uso. Erro: {e}")
                erros_renomeacao += 1
            except FileExistsError as e:
                # Este erro é evitado pela função _obter_novo_nome_unico, mas mantido para segurança.
                self._log_message(f"Erro: O destino '{novo_nome_final}' já existe de forma inesperada na pasta de destino. Erro: {e}")
                erros_renomeacao += 1
            except OSError as e:
                self._log_message(f"Erro do sistema operacional ao renomear '{nome_antigo}': {e}")
                erros_renomeacao += 1
            except Exception as e:
                self._log_message(f"Erro inesperado ao renomear '{nome_antigo}': {e}")
                erros_renomeacao += 1
            
            progresso = (i + 1) / total_itens * 100
            self.progressbar_value.set(progresso)
            self.master.update_idletasks() 

        self._log_message("\n--- Processo de Renomeação Concluído ---")
        self._log_message(f"Itens renomeados com sucesso: {arquivos_renomeados}")
        
        if erros_renomeacao > 0:
            self._log_message(f"Concluído com Erros: {erros_renomeacao} erro(s). Verifique os logs.")
            messagebox.showwarning("Concluído com Erros", f"O processo de renomeação foi concluído, mas houve {erros_renomeacao} erro(s). Verifique a área de logs para mais informações.")
        else:
            messagebox.showinfo("Sucesso", "Todos os itens foram renomeados com sucesso!")
        
        self.progressbar_value.set(100) 
        
        # Gera uma nova prévia (após renomeação)
        self.atualizar_previa() 


# --- Inicializa a aplicação Tkinter ---
if __name__ == "__main__":
    try:
        # Tenta configurar o locale para Português do Brasil para formatação de data (opcional)
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        except:
             pass
        
    root = tb.Window(themename="cosmo") 
    app = RenomeadorArquivosApp(root)
    root.mainloop()