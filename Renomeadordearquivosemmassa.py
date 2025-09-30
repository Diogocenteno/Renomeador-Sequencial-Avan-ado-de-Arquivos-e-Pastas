#%%
# -*- coding: utf-8 -*- 
"""
Renomeador de Arquivos em Massa 
Versão 2.19 - 2025-09-30 (Correção: Restauração do Filtro de Formatos)
Autor: Mutante
Descrição:
Aplicação para renomear arquivos e/ou pastas de forma sequencial e segura.
Inclui processo de Backup e a opção de salvar o Log.
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
import threading 

# Variável de estado global para controlar o thread da prévia
PREVIEW_THREAD = None

class RenomeadorArquivosApp:
    """
    Aplicação Tkinter para renomear arquivos e/ou pastas de forma sequencial e segura.
    Inclui barra de progresso funcional para o processo de Backup e a opção de salvar o Log.
    """
    def __init__(self, master):
        self.master = master
        
        # Configuração inicial da janela
        master.title("Renomeador Sequencial Avançado de Arquivos e Pastas")
        master.geometry("950x850") 
        master.resizable(True, True)

        # Variáveis de controle
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
        self.preview_is_running = False # Flag para threading
        
        # --- LAYOUT PRINCIPAL: NOTEBOOK E SCROLLEDFRAME ---
        
        # 1. FRAME DE BOTÕES INFERIOR (FIXO)
        self.frame_botoes = tb.Frame(master, padding=(10, 10)) 
        self.frame_botoes.pack(pady=10, fill=X, side=BOTTOM)

        # 2. NOTEBOOK (ABA) - EXPANSÍVEL NO ESPAÇO RESTANTE
        self.notebook = tb.Notebook(master, bootstyle="primary")
        self.notebook.pack(expand=YES, fill=BOTH, padx=10, pady=(10, 0))

        # --- CRIAÇÃO DAS ABAS ---
        self.tab_config = tb.Frame(self.notebook, padding=5)
        self.tab_logs = tb.Frame(self.notebook, padding=10)
        self.tab_help = tb.Frame(self.notebook, padding=10) # NOVA ABA DE AJUDA

        self.notebook.add(self.tab_config, text="1. Configurações de Renomeação")
        self.notebook.add(self.tab_logs, text="2. Log de Atividades e Prévia")
        self.notebook.add(self.tab_help, text="3. Como Usar o App") # Adiciona a aba de ajuda

        # 3. SCROLLEDFRAME DENTRO DA ABA DE CONFIGURAÇÃO 
        self.scrolled_content_frame = ScrolledFrame(
            self.tab_config, 
            autohide=True, 
            bootstyle="primary", 
            padding=0,
        )
        self.scrolled_content_frame.pack(expand=YES, fill=BOTH)
        
        # O ScrolledFrame é o contêiner em si
        content_frame = self.scrolled_content_frame
        content_frame.columnconfigure(0, weight=1) 
        
        # --- DEFINIÇÃO DOS FRAMES DE AGRUPAMENTO (LÓGICO) ---
        
        # Frames para segurar os LabelFrames lado a lado
        self.frame_agrupamento_tema = tb.Frame(content_frame, padding=(0, 0))
        self.frame_agrupamento_selecao = tb.Frame(content_frame, padding=(0, 0))
        
        # O Frame que contém as opções de filtro/itens
        self.frame_agrupamento_selecao_e_filtro = tb.Frame(content_frame, padding=(0, 5))
        
        self.frame_agrupamento_nome_e_seq = tb.Frame(content_frame, padding=(0, 5))
        self.frame_agrupamento_limpeza = tb.Frame(content_frame, padding=(0, 5))

        # Empacota os frames de AGRUPAMENTO
        self.frame_agrupamento_tema.pack(pady=(5, 5), padx=10, fill=X, expand=False)
        self.frame_agrupamento_selecao.pack(pady=(5, 5), padx=10, fill=X, expand=False)
        self.frame_agrupamento_selecao_e_filtro.pack(pady=(5, 5), padx=10, fill=X, expand=True)
        self.frame_agrupamento_nome_e_seq.pack(pady=(5, 5), padx=10, fill=X, expand=True)
        self.frame_agrupamento_limpeza.pack(pady=(5, 5), padx=10, fill=X, expand=False)


        # --- DEFINIÇÃO DOS LABELFRAMES INTERNOS (Agrupamento) ---
        
        # 1. Aparência e Segurança
        self.frame_tema = tb.LabelFrame(self.frame_agrupamento_tema, text="Aparência", bootstyle="info", padding=(10, 5))
        self.frame_backup = tb.LabelFrame(self.frame_agrupamento_tema, text="Segurança", bootstyle="danger", padding=(10, 5))
        self.frame_tema.pack(side=LEFT, padx=(0, 5), fill=X, expand=True)
        self.frame_backup.pack(side=LEFT, padx=(5, 0), fill=X, expand=True)

        # 2. Seleção de Pasta
        self.frame_selecao = tb.LabelFrame(self.frame_agrupamento_selecao, text="1. Pasta de Trabalho", bootstyle="primary", padding=(10, 10))
        self.frame_selecao.pack(fill=X, expand=True)

        # 3. Seleção de Itens e Filtro (Lado a Lado)
        self.frame_tipo_item = tb.LabelFrame(self.frame_agrupamento_selecao_e_filtro, text="2. Itens a Renomear e Ordenação", bootstyle="primary", padding=(10, 10))
        self.frame_formato = tb.LabelFrame(self.frame_agrupamento_selecao_e_filtro, text="3. Filtro de Formato (Arquivos)", bootstyle="primary", padding=(10, 10))
        
        # CORREÇÃO: Usar side=LEFT com expand=True fará o layout funcionar
        self.frame_tipo_item.pack(side=LEFT, padx=(0, 5), fill=BOTH, expand=True)
        self.frame_formato.pack(side=LEFT, padx=(5, 0), fill=BOTH, expand=True)
        
        # 4. Nome Base e Sequência (Lado a Lado)
        self.frame_configuracao = tb.LabelFrame(self.frame_agrupamento_nome_e_seq, text="4. Configuração do Nome Base", bootstyle="info", padding=(10, 10))
        self.frame_sequencia = tb.LabelFrame(self.frame_agrupamento_nome_e_seq, text="5. Sequência Avançada", bootstyle="info", padding=(10, 10))
        self.frame_configuracao.pack(side=LEFT, padx=(0, 5), fill=BOTH, expand=True)
        self.frame_sequencia.pack(side=LEFT, padx=(5, 0), fill=BOTH, expand=True)
        
        # 5. Limpeza e Data
        self.frame_limpeza_data = tb.LabelFrame(self.frame_agrupamento_limpeza, text="6. Limpeza de Texto e Prefixo de Data/Hora", bootstyle="info", padding=(10, 10))
        self.frame_limpeza_data.pack(fill=X, expand=True)
        
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
            text="Fazer Backup Agora", 
            command=self.fazer_backup, 
            bootstyle="danger-raised" 
        )
        self.botao_backup.pack(pady=5, fill=X, expand=True)


        # --- Componentes do Frame de Seleção de Pasta (1) ---
        tb.Label(self.frame_selecao, text="Caminho Selecionado:", font=('Arial', 10, 'bold')).pack(anchor=W, pady=(0,5))
        self.label_caminho = tb.Label(self.frame_selecao, textvariable=self.caminho_da_pasta, 
                                        wraplength=800, justify=LEFT, relief=GROOVE, font=('Arial', 10)) 
        self.label_caminho.pack(fill=X, pady=5)
        
        frame_botoes_selecao = tb.Frame(self.frame_selecao)
        frame_botoes_selecao.pack(fill=X, pady=5)
        
        tb.Label(frame_botoes_selecao, text="Selecione a pasta raiz com os itens que serão renomeados.", bootstyle="secondary").pack(side=LEFT) 
        tb.Button(frame_botoes_selecao, text="Selecionar Pasta", command=self.selecionar_pasta, bootstyle="primary-outline").pack(side=RIGHT)

        
        # --- Componentes do Frame de Seleção e Ordenação de Itens (2) ---
        frame_tipo_recursivo = tb.Frame(self.frame_tipo_item)
        frame_tipo_recursivo.pack(fill=X, expand=True, pady=(0, 5))
        
        tb.Label(frame_tipo_recursivo, text="Itens:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0,5))
        tb.Radiobutton(frame_tipo_recursivo, text="Arquivos", variable=self.tipo_renomeacao, value=1, bootstyle="primary-round-toggle").pack(side=LEFT, padx=5)
        tb.Radiobutton(frame_tipo_recursivo, text="Pastas", variable=self.tipo_renomeacao, value=2, bootstyle="primary-round-toggle").pack(side=LEFT, padx=5)
        tb.Radiobutton(frame_tipo_recursivo, text="Ambos", variable=self.tipo_renomeacao, value=3, bootstyle="primary-round-toggle").pack(side=LEFT, padx=5)

        tb.Checkbutton(frame_tipo_recursivo, text="Incluir Subpastas", variable=self.modo_recursivo, 
                        bootstyle="danger-round-toggle").pack(side=RIGHT, padx=5)

        frame_criterio_ordenacao = tb.Frame(self.frame_tipo_item)
        frame_criterio_ordenacao.pack(fill=X, pady=(5, 0))
        
        tb.Label(frame_criterio_ordenacao, text="Critério de Ordenação:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.opcoes_ordenacao = ["Por Nome", "Por Data de Modificação", "Por Data de Criação"]
        self.combo_ordenacao = tb.Combobox(frame_criterio_ordenacao, textvariable=self.criterio_ordenacao, 
                                             values=self.opcoes_ordenacao, state="readonly", font=('Arial', 10), width=25)
        self.combo_ordenacao.pack(side=LEFT, fill=X, expand=True, pady=5)


        # --- Componentes do Frame de Filtro por Formato (3) ---
        # ESTA PARTE FOI RESTAURADA E ESTÁ NO self.frame_formato
        tb.Label(self.frame_formato, text="Filtro de Arquivos (.ext):", font=('Arial', 10, 'bold')).pack(anchor=W, pady=(0,5))
        self.opcoes_formato = ["Todos os formatos", ".pdf", ".xlsx", ".docx", ".csv", ".txt", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".zip", ".rar", ".7z", ".pptx", ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".html", ".css", ".js", ".py"] 
        self.combobox_formato = tb.Combobox(self.frame_formato, textvariable=self.formato_selecionado, 
                                             values=self.opcoes_formato, state="readonly", font=('Arial', 10))
        self.combobox_formato.set("Todos os formatos") 
        self.combobox_formato.pack(pady=5, fill=X, expand=True)


        # --- Componentes do Frame de Configuração do Nome Base (4) ---
        frame_nome_base = tb.Frame(self.frame_configuracao)
        frame_nome_base.pack(fill=X, pady=(0, 5))
        
        tb.Label(frame_nome_base, text="Nome Base:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.entrada_nome_base = tb.Entry(frame_nome_base, textvariable=self.nome_base_arquivo, font=('Arial', 10))
        self.entrada_nome_base.pack(side=LEFT, pady=5, fill=X, expand=True)

        # Botão: APLICA AS CONFIGURAÇÕES E GERA A PRÉVIA
        self.botao_aplicar_nome = tb.Button(
            frame_nome_base, 
            text="Aplicar Nome Base e Prévia", 
            command=self.atualizar_previa, # ESTE É O ÚNICO BOTÃO DE APLICAÇÃO DE CONFIG
            bootstyle="info"
        )
        self.botao_aplicar_nome.pack(side=LEFT, padx=(10, 0))

        frame_caixa = tb.Frame(self.frame_configuracao)
        frame_caixa.pack(fill=X, pady=(5, 0))
        tb.Label(frame_caixa, text="Caixa:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.opcoes_caixa = ["Padrão", "Minúsculas", "Maiúsculas"]
        self.combo_caixa = tb.Combobox(frame_caixa, textvariable=self.conversao_caixa, values=self.opcoes_caixa, 
                                         state="readonly", font=('Arial', 10), width=15)
        self.combo_caixa.pack(side=LEFT, pady=5, fill=X, expand=True)


        # --- Componentes do Frame de Sequência Avançada (5) ---
        frame_seq_linha1 = tb.Frame(self.frame_sequencia)
        frame_seq_linha1.pack(fill=X, pady=(5, 5))
        
        tb.Label(frame_seq_linha1, text="Dígitos (001):", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.spinbox_digitos = tb.Spinbox(frame_seq_linha1, from_=1, to=8, textvariable=self.digitos_sequenciais, font=('Arial', 10), width=5)
        self.spinbox_digitos.pack(side=LEFT, pady=5, padx=(0, 10))

        tb.Label(frame_seq_linha1, text="Partida:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.spinbox_partida = tb.Spinbox(frame_seq_linha1, from_=1, to=9999, textvariable=self.ponto_de_partida, font=('Arial', 10), width=5)
        self.spinbox_partida.pack(side=LEFT, pady=5)
        
        frame_seq_linha2 = tb.Frame(self.frame_sequencia)
        frame_seq_linha2.pack(fill=X, pady=(5, 0))
        
        tb.Label(frame_seq_linha2, text="Posição:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        tb.Radiobutton(frame_seq_linha2, text="Sufixo", variable=self.posicao_numero, value="Sufixo", bootstyle="info-round-toggle").pack(side=LEFT, padx=10)
        tb.Radiobutton(frame_seq_linha2, text="Prefixo", variable=self.posicao_numero, value="Prefixo", bootstyle="info-round-toggle").pack(side=LEFT, padx=10)


        # --- Componentes do Frame de Limpeza e Data (6) ---
        frame_limp_linha1 = tb.Frame(self.frame_limpeza_data)
        frame_limp_linha1.pack(fill=X, pady=(5, 5))
        
        tb.Label(frame_limp_linha1, text="Procurar:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.entrada_procurar = tb.Entry(frame_limp_linha1, textvariable=self.texto_procurar, font=('Arial', 10), width=20)
        self.entrada_procurar.pack(side=LEFT, pady=5, padx=(0, 15), fill=X, expand=True)

        tb.Label(frame_limp_linha1, text="Substituir por:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        self.entrada_substituir = tb.Entry(frame_limp_linha1, textvariable=self.texto_substituir, font=('Arial', 10), width=20)
        self.entrada_substituir.pack(side=LEFT, pady=5, fill=X, expand=True)
        
        frame_limp_linha2 = tb.Frame(self.frame_limpeza_data)
        frame_limp_linha2.pack(fill=X, pady=(5, 0))
        
        tb.Label(frame_limp_linha2, text="Prefixos e Limpeza:", font=('Arial', 10, 'bold')).pack(side=LEFT, anchor=W, padx=(0, 5))
        
        tb.Checkbutton(frame_limp_linha2, text="Data (DD-MM-YYYY)", variable=self.adicionar_data, 
                        bootstyle="success-round-toggle").pack(side=LEFT, padx=5)
                        
        tb.Checkbutton(frame_limp_linha2, text="Hora (HH-MM)", variable=self.adicionar_hora, 
                        bootstyle="success-round-toggle").pack(side=LEFT, padx=5)
                        
        tb.Checkbutton(frame_limp_linha2, text="Remover Espaços (' ' por '_')", variable=self.remover_espacos, 
                        bootstyle="info-round-toggle").pack(side=LEFT, padx=15)


        # --- Componentes da ABA DE LOGS E AJUDA ---
        
        # Log de Atividades
        tb.Label(self.tab_logs, text="Log de Atividades e Prévia da Renomeação:", font=('Arial', 10, 'bold')).pack(anchor=W, pady=(0,5))
        self.log_area = scrolledtext.ScrolledText(self.tab_logs, state='disabled', wrap=WORD, font=('Consolas', 9)) 
        self.log_area.pack(expand=True, fill=BOTH)

        # Ajuda (Como Usar)
        self.setup_help_tab() # Chama o método para configurar o conteúdo da aba de ajuda

        # --- Componentes do Frame de Botões (e Progress Bar) ---
        self.progressbar = tb.Progressbar(self.frame_botoes, orient=HORIZONTAL, mode='determinate', 
                                             variable=self.progressbar_value, bootstyle="success")
        self.progressbar.pack(side=TOP, fill=X, pady=(0, 10))

        frame_botoes_acao = tb.Frame(self.frame_botoes)
        frame_botoes_acao.pack(fill=X, expand=False)

        # O botão "Gerar Prévia no Log" chama a função que força a mudança de aba
        tb.Button(frame_botoes_acao, text="Gerar Prévia no Log", command=lambda: self.gerar_previa_no_log(force_log_tab=True), bootstyle="info-outline").pack(side=LEFT, padx=5, fill=X, expand=True)
        tb.Button(frame_botoes_acao, text="Abrir Prévia em Janela", command=self.abrir_janela_previa, bootstyle="info-outline").pack(side=LEFT, padx=5, fill=X, expand=True)
        
        # BOTÃO PRINCIPAL COM STYLO REALÇADO
        self.botao_renomear_ttk = tb.Button(frame_botoes_acao, text="Renomear Itens (IRREVERSÍVEL)", command=self.renomear_arquivos, state='disabled', bootstyle="success-raised")
        self.botao_renomear_ttk.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        # Botoes de Log
        tb.Button(frame_botoes_acao, text="Salvar Log", command=self.salvar_log, bootstyle="secondary-outline").pack(side=RIGHT, padx=5, fill=X, expand=True)
        tb.Button(frame_botoes_acao, text="Limpar Logs", command=self._limpar_logs, bootstyle="secondary").pack(side=RIGHT, padx=5, fill=X, expand=True)
        
    def setup_help_tab(self):
        """Configura o conteúdo da nova aba 'Como Usar o App'."""
        
        tb.Label(self.tab_help, text="Guia de Uso Rápido:", font=('Arial', 12, 'bold')).pack(anchor=W, pady=(0, 5))
        
        help_text_content = """
        Este aplicativo foi desenvolvido para renomear arquivos e pastas em lote de forma sequencial e segura.

        ▶️ **PASSO 1: Seleção e Filtro (Aba 1)**

        1.  **Pasta de Trabalho:** Clique em **'Selecionar Pasta'** para escolher o diretório raiz dos arquivos.
        2.  **Itens a Renomear:** Escolha se deseja renomear **Arquivos**, **Pastas** ou **Ambos**.
        3.  **Recursivo:** Marque **'Incluir Subpastas'** se quiser processar todos os subdiretórios. (Recomendado: Faça um backup antes!)
        4.  **Ordenação:** Selecione o critério (Por Nome, Data de Modificação ou Data de Criação). Este critério define a ordem da numeração.
        5.  **Filtro:** Use o **Filtro de Formato** para renomear apenas arquivos com uma extensão específica (ex: `.pdf`, `.jpg`).

        ▶️ **PASSO 2: Configuração do Novo Nome (Aba 1)**

        1.  **Nome Base:** Digite o novo nome principal (ex: `Relatorio_Final`).
        2.  **Sequência Avançada:**
            * **Dígitos:** Defina a quantidade de zeros (padding) (ex: `3` resulta em 001, 002...).
            * **Partida:** Defina o número inicial da sequência (ex: `1` para começar em 001).
            * **Posição:** Escolha se a sequência deve ser um **Prefixo** (`001_Nome`) ou **Sufixo** (`Nome_001`).
        3.  **Limpeza/Prefixos:**
            * Use **'Procurar'** e **'Substituir'** para fazer alterações globais no nome.
            * Marque **Data** e/ou **Hora** para adicionar um prefixo de data/hora no nome final.
            * Marque **Remover Espaços** para substituir 'espaços' por `_` (underscore).

        ▶️ **PASSO 3: Prévia e Execução**

        1.  **Prévia:** Após ajustar as configurações, clique em **'Aplicar Nome Base e Prévia'** na Aba 1 ou em **'Gerar Prévia no Log'** (Aba 2). O resultado aparecerá na aba **Log de Atividades**.
            * **ATENÇÃO:** A numeração reinicia a cada subpasta, garantindo que o `001` seja usado em todos os diretórios.
        2.  **Backup (Recomendado!):** Clique em **'Fazer Backup Agora'** para criar uma cópia de segurança completa da pasta antes de prosseguir.
        3.  **Renomear:** Se a prévia estiver correta, clique no botão verde **'Renomear Itens (IRREVERSÍVEL)'**.
        4.  **Status:** A **barra de progresso** mostrará o andamento da renomeação ou do backup.
        """
        
        help_area = scrolledtext.ScrolledText(
            self.tab_help, 
            state='normal', 
            wrap=WORD, 
            font=('Arial', 10), 
            padx=10, 
            pady=10
        )
        help_area.pack(expand=True, fill=BOTH)
        help_area.insert(tk.END, help_text_content)
        
        # Configurações de tags para realce (opcional, mas bom para UX)
        help_area.tag_configure('header', font=('Arial', 10, 'bold'), foreground='blue')
        help_area.tag_configure('bold', font=('Arial', 10, 'bold'))
        
        # Aplica tags no texto inserido (ajustando as posições conforme o texto)
        help_area.config(state='disabled')


    def _count_total_items(self, src):
        """Conta o número total de arquivos e diretórios na pasta de origem para o progresso."""
        count = 0
        try:
            for root, dirs, files in os.walk(src):
                count += len(dirs) + len(files)
        except Exception:
            # Ignora erros de permissão ou caminhos inválidos durante a contagem
            pass
        return count

    def copy_with_progress(self, src, dst, total_items):
        """Copia recursivamente, atualizando a barra de progresso."""
        copied_count = 0
        
        if total_items == 0:
            self.progressbar_value.set(100)
            self.master.update_idletasks()
            return

        for root, dirs, files in os.walk(src):
            try:
                # Obtém o caminho relativo do diretório atual em relação ao src
                relative_path = pathlib.Path(root).relative_to(src)
            except ValueError:
                # Isso não deve acontecer se a lógica de caminho for boa, mas é um fallback
                continue 
            
            current_dst_dir = pathlib.Path(dst) / relative_path

            # 1. Cria diretórios no destino e atualiza progresso
            for dir_name in dirs:
                # Tenta criar subdiretórios
                try:
                    (current_dst_dir / dir_name).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self._log_message(f"ERRO DE CÓPIA (DIR): Falha ao criar diretório '{dir_name}'. Detalhes: {e}")
                    
                copied_count += 1
                progresso = (copied_count / total_items) * 100
                self.progressbar_value.set(progresso)
                self.master.update_idletasks()
            
            # 2. Copia arquivos e atualiza progresso
            for file_name in files:
                src_file = pathlib.Path(root) / file_name
                dst_file = current_dst_dir / file_name
                
                try:
                    # shutils.copy2 preserva metadados (data de modificação, etc.)
                    shutil.copy2(src_file, dst_file)
                except Exception as e:
                    self._log_message(f"ERRO DE CÓPIA (FILE): Falha ao copiar arquivo '{file_name}'. Detalhes: {e}")
                
                copied_count += 1
                progresso = (copied_count / total_items) * 100
                self.progressbar_value.set(progresso)
                self.master.update_idletasks()
        
        self.progressbar_value.set(100)
        self.master.update_idletasks()


    def fazer_backup(self):
        """
        Copia a pasta selecionada para um destino de backup com barra de progresso.
        """
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
        pasta_origem_nome = pasta_origem.name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_backup = f"{pasta_origem_nome}_{timestamp}" 
        pasta_destino_completa = pathlib.Path(destino_backup_base_str) / nome_backup

        # --- CRIAÇÃO E VERIFICAÇÃO DO DIRETÓRIO DE DESTINO ---
        try:
            pasta_destino_completa.mkdir(parents=True, exist_ok=True)
            self._log_message(f"Diretório de destino criado: {pasta_destino_completa}")
        except Exception as e:
            self._log_message(f"ERRO: Falha ao criar o diretório de destino '{pasta_destino_completa}'. Detalhes: {e}")
            messagebox.showerror("Erro de Backup", f"Não foi possível criar o diretório de destino. Detalhes: {e}")
            self.progressbar_value.set(0)
            return
        # ------------------------------------

        # 3. Confirmação
        confirmacao = messagebox.askyesno(
            "Confirmar Backup",
            f"Você irá copiar a pasta:\n'{pasta_origem_str}'\n\nPara a pasta de destino:\n'{pasta_destino_completa}'\n\nConfirmar o início da cópia recursiva?"
        )
        if not confirmacao:
            self._log_message("Cópia de backup cancelada após a confirmação.")
            # Tenta remover o diretório vazio se o usuário cancelar
            try:
                if not os.listdir(pasta_destino_completa):
                    os.rmdir(pasta_destino_completa)
            except OSError:
                pass 
            self.progressbar_value.set(0)
            return

        self._log_message(f"Iniciando backup recursivo de '{pasta_origem.name}' para '{pasta_destino_completa}'...")

        self.progressbar_value.set(0) # Inicia a barra de progresso

        try:
            total_items = self._count_total_items(pasta_origem)
            
            # Chamada para a função de cópia com progresso
            self.copy_with_progress(pasta_origem, pasta_destino_completa, total_items)
            
            self._log_message("\n--- Backup Concluído ---")
            self._log_message(f"Cópia de backup realizada com sucesso para: {pasta_destino_completa}")
            messagebox.showinfo("Sucesso no Backup", f"A pasta de backup foi criada com sucesso em:\n{pasta_destino_completa}")

        except Exception as e:
            self._log_message(f"\nERRO INESPERADO: Falha no backup. Detalhes: {e}")
            messagebox.showerror("Erro de Backup", f"Ocorreu um erro inesperado durante o backup. Detalhes: {e}")
        finally:
             self.progressbar_value.set(0) # Garante que a barra é zerada em caso de falha


    def aplicar_tema(self, event=None):
        """Aplica o tema selecionado à aplicação."""
        if self.master.winfo_exists():
            tema_escolhido = self.tema_selecionado.get()
            self.style.theme_use(tema_escolhido)
            self._log_message(f"Tema alterado para: {tema_escolhido}")

            # Atualiza bootstyle para os frames (mantendo a consistência)
            self.frame_tema.config(bootstyle="info")
            self.frame_backup.config(bootstyle="danger") 
            self.frame_selecao.config(bootstyle="primary")
            self.frame_tipo_item.config(bootstyle="primary")
            self.frame_formato.config(bootstyle="primary")
            self.frame_configuracao.config(bootstyle="info")
            self.frame_sequencia.config(bootstyle="info")
            self.frame_limpeza_data.config(bootstyle="info")
            
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
                # re.escape() garante que caracteres especiais no texto_procurar sejam tratados literalmente
                nome_base = re.sub(re.escape(texto_procurar), texto_substituir, nome_base, flags=re.IGNORECASE)
            except Exception as e:
                 # Ignora se a regex for inválida, mas isso não deve ocorrer com re.escape
                pass

        # 2. Adiciona Prefixo de Data/Hora (se ativado)
        data_prefixo = ""
        if self.adicionar_data.get() or self.adicionar_hora.get():
            try:
                # Usa a data e hora do processamento (consistente)
                data_mod = datetime.now()
                
                # Padrão Brasileiro (DD-MM-YYYY / HH-MM) usando caracteres seguros
                data_parte = data_mod.strftime("%d-%m-%Y") if self.adicionar_data.get() else "" 
                hora_parte = data_mod.strftime("%H-%M") if self.adicionar_hora.get() else "" 
                
                # Monta a string do prefixo
                if data_parte and hora_parte:
                    data_prefixo = f"[{data_parte}_{hora_parte}]_" # Novo formato com [] para legibilidade
                elif data_parte:
                    data_prefixo = f"[{data_parte}]_"
                elif hora_parte:
                    data_prefixo = f"[{hora_parte}]_"
                
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
        
        # 5. Sanitiza caracteres inválidos (SO)
        caracteres_invalidos = r'[\\/:*?"<>|]'
        nome_sanitizado = re.sub(caracteres_invalidos, '_', nome_base).strip()
        
        return data_prefixo + nome_sanitizado

    def _log_message(self, message):
        """
        Adiciona uma mensagem à área de log com o timestamp atual no formato brasileiro.
        """
        # Formato: [DD/MM/YYYY HH:MM:SS]
        now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S] ")
        
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, now + message + "\n")
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
            # Mantenha a mudança de aba aqui, pois é um evento de inicialização importante
            self.notebook.select(self.tab_logs) 
            # Chama a prévia ao selecionar a pasta pela primeira vez
            self.gerar_previa_no_log(force_log_tab=False) 
        else:
            self.caminho_da_pasta.set("Nenhuma pasta selecionada")
            self._log_message("Seleção de pasta cancelada.")
            self.botao_renomear_ttk.config(state='disabled')
            self.progressbar_value.set(0)

    def atualizar_previa(self, event=None):
        """Chama a geração de prévia quando o botão 'Aplicar Nome Base e Prévia' é clicado."""
        self.gerar_previa_no_log(force_log_tab=False) 

    def _obter_novo_nome_unico(self, pasta, prefixo, extensao):
        """
        Gera um nome de arquivo ou pasta único, adicionando um sufixo numérico se necessário.
        """
        pasta_path = pathlib.Path(pasta) 
        
        # Nome base (primeira tentativa)
        novo_nome_tentativa = f"{prefixo}{extensao}"
        caminho_tentativa = pasta_path / novo_nome_tentativa

        contador_sufixo_duplicado = 0
        while caminho_tentativa.exists(): 
            contador_sufixo_duplicado += 1
            
            # Adiciona o contador de duplicidade (ex: "Nome (1).ext")
            novo_nome_tentativa = f"{prefixo} ({contador_sufixo_duplicado}){extensao}"
            caminho_tentativa = pasta_path / novo_nome_tentativa
            
            if contador_sufixo_duplicado > 9999:
                raise Exception("Excesso de tentativas para criar nome único, limite de 9999 duplicidades atingido.")
                
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
        
        # A iteração deve ser sempre topdown=False para garantir que a pasta pai seja renomeada por último
        
        for root, dirs, files in os.walk(pasta_path, topdown=False):
            caminho_atual = pathlib.Path(root)
            
            # 1. Processa Arquivos
            if tipo_selecionado == 1 or tipo_selecionado == 3:
                for nome_arquivo in files:
                    caminho_completo = caminho_atual / nome_arquivo
                    extensao = caminho_completo.suffix
                    if formato_alvo == "Todos os formatos" or extensao.lower() == formato_alvo.lower():
                        itens_a_processar.append((nome_arquivo, False, extensao, caminho_completo))

            # 2. Processa Pastas
            if tipo_selecionado == 2 or tipo_selecionado == 3:
                for nome_dir in dirs:
                     caminho_completo = caminho_atual / nome_dir
                     # NUNCA processar a pasta raiz, se for um diretório de trabalho
                     if caminho_completo != pasta_path:
                         itens_a_processar.append((nome_dir, True, "", caminho_completo))
            
            # Se for o modo não recursivo, filtramos apenas o nível superior no final.
                
        # --- Lógica de Ordenação (Bottom-Up com agrupamento por pasta) ---
        def obter_chave_ordenacao(item):
            caminho_completo = item[3]
            
            # Profundidade do caminho: usada para garantir a ordem Bottom-Up (Decrescente)
            profundidade = len(caminho_completo.parts) 
            
            # Chave principal de agrupamento: Diretório Pai (Para resetar o contador)
            diretorio_pai = str(caminho_completo.parent)

            if criterio_ordenacao == "Por Nome":
                # Ordenação: 1. Profundidade (Decrescente), 2. Diretório Pai (Alfabético), 3. Tipo (Arquivo antes de Pasta), 4. Nome
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
            
            # Retorno padrão
            return (-profundidade, diretorio_pai, item[0].lower())
        
        # Ajuste para modo não recursivo: remove subpastas
        if not modo_recursivo:
            # Filtra itens que não estão diretamente no pasta_path
            itens_a_processar = [item for item in itens_a_processar if item[3].parent == pasta_path]
            
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
        
        itens_a_processar = self._obter_arquivos_filtrados_e_ordenados(pasta)
        
        mensagens = [f"Gerando prévia para: {tipo_selecionado_str}{recursivo_str} | Ordenação: {self.criterio_ordenacao.get()} | Partida: {ponto_partida} | Padding: {digitos} dígitos | Posição: {posicao_numero} | **CONTADOR REINICIADO POR PASTA**",
                     f"Pasta Raiz: {pasta}"]
        
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
                
                # Para a prévia, o sanitizador usará a data/hora atual (consistente)
                nome_base_com_limpeza = self._sanitizar_nome_base(nome_base_digitado, caminho_completo)

                if nome_base_com_limpeza:
                    if posicao_numero == "Prefixo":
                        prefixo_base = f"{numero_formatado}_{nome_base_com_limpeza}"
                    else: # Sufixo
                        prefixo_base = f"{nome_base_com_limpeza}_{numero_formatado}"
                else:
                    prefixo_base = f"{numero_formatado}"

                # Gerar o nome previsto completo (com a extensão de volta se for arquivo)
                novo_nome_previsto = f"{prefixo_base}{extensao}"
                
                # Para o Log: calcula o caminho relativo
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

    def _processar_previa_e_exibir_log(self, force_log_tab):
        """
        Função a ser executada em um thread secundário para gerar a prévia.
        """
        self.preview_is_running = True # Inicia a flag
        try:
            mensagens = self._gerar_lista_previa()
            
            # Atualiza o log e verifica o botão Renomear (de volta no thread principal)
            self.master.after(0, lambda: self._finalizar_previa(mensagens, sucesso=True))
            
        except Exception as e:
            # Em caso de erro, exibe o erro e para a barra (de volta no thread principal)
            self.master.after(0, lambda: self._finalizar_previa([f"ERRO CRÍTICO NA GERAÇÃO DE PRÉVIA: {e}"], sucesso=False))
        finally:
            self.preview_is_running = False # Finaliza a flag

    def _finalizar_previa(self, mensagens, sucesso=True):
        """
        Zera a progressbar (se houver), exibe as mensagens no log e atualiza o estado do botão.
        Chamada de volta no thread principal.
        """
        # A barra de progresso não é utilizada para prévia. Apenas garante que esteja zerada.
        self.progressbar.config(mode='determinate', value=0)
        self.master.update_idletasks()
        
        # Limpa e reinsere a prévia 
        if sucesso:
            self._limpar_logs()
            
        for msg in mensagens:
            self._log_message(msg)
            
        # Determina se há itens a renomear
        has_items_to_rename = True
        if len(mensagens) > 2 and "Nenhum item encontrado" in mensagens[2]:
             has_items_to_rename = False
        
        if sucesso and has_items_to_rename:
             self.botao_renomear_ttk.config(state='normal')
        else:
             self.botao_renomear_ttk.config(state='disabled')


    def gerar_previa_no_log(self, force_log_tab=True):
        """
        Inicia a geração de prévia em um thread separado para manter a UI responsiva, 
        sem ativar a progressbar.
        """
        if self.preview_is_running:
            self._log_message("Aviso: A geração de prévia anterior ainda está em execução. Aguarde.")
            return

        if force_log_tab:
            self.notebook.select(self.tab_logs)
        
        pasta = self.caminho_da_pasta.get()

        if not pathlib.Path(pasta).is_dir():
            self._limpar_logs()
            self.botao_renomear_ttk.config(state='disabled')
            self._log_message("Erro: Pasta inválida. Por favor, selecione uma pasta válida.")
            return
        
        self._limpar_logs()
        self._log_message("Iniciando geração de prévia em segundo plano...")
        
        # Não ativa a barra de progresso
        self.progressbar.config(mode='determinate', value=0)
        self.master.update_idletasks() 
        
        # Inicia o trabalho pesado em um thread separado
        thread = threading.Thread(target=self._processar_previa_e_exibir_log, args=(force_log_tab,))
        thread.daemon = True # Permite que o programa feche mesmo se o thread estiver rodando
        thread.start()


    def abrir_janela_previa(self):
        """Abre uma nova janela Toplevel para exibir a prévia, sem barra de progresso."""
        
        if self.preview_is_running:
             messagebox.showinfo("Aviso", "A prévia está sendo gerada no Log. Aguarde a finalização.")
             return
        
        # Não ativa a barra de progresso
        self.progressbar.config(mode='determinate', value=0)
        self.master.update_idletasks() 
        
        try:
            # Sincronamente para Janela
            mensagens_previa = self._gerar_lista_previa()
        
            if not mensagens_previa or "Erro: Pasta inválida" in mensagens_previa[0]:
                messagebox.showerror("Erro", "Pasta inválida ou não selecionada para gerar a prévia.")
                return
                
            janela_previa = tb.Toplevel(self.master)
            janela_previa.title("Prévia da Renomeação")
            janela_previa.geometry("700x600")

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
            
        finally:
             # Garante que a progressbar está zerada
            self.progressbar.config(mode='determinate', value=0)
            self.master.update_idletasks()


    def renomear_arquivos(self):
        """
        Executa a renomeação dos arquivos e pastas na pasta selecionada, com barra de progresso.
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
        
        # --- Inicializa o Progresso (Determinado) ---
        self.progressbar.config(mode='determinate')
        self.progressbar_value.set(0) 
        self.master.update_idletasks()
        # --- Fim Inicialização ---
        
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
            
            # Sanitiza o nome base (inclui data, hora, limpeza, etc.)
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
                # O novo nome_final (com sufixo de duplicidade se necessário)
                novo_nome_final = self._obter_novo_nome_unico(pasta_destino, prefixo_base, extensao)
                caminho_novo = pasta_destino / novo_nome_final

                if nome_antigo != novo_nome_final:
                    os.rename(caminho_completo, caminho_novo) 
                    
                    try:
                        caminho_log = str(caminho_completo.parent.relative_to(pasta))
                    except ValueError:
                        # Se não for possível obter o relativo (ex: outra unidade), usa o absoluto
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
                # Este erro deve ser evitado por _obter_novo_nome_unico, mas é mantido como segurança.
                self._log_message(f"Erro: O destino '{novo_nome_final}' já existe de forma inesperada na pasta de destino. Erro: {e}")
                erros_renomeacao += 1
            except OSError as e:
                self._log_message(f"Erro do sistema operacional ao renomear '{nome_antigo}': {e}")
                erros_renomeacao += 1
            except Exception as e:
                self._log_message(f"Erro inesperado ao renomear '{nome_antigo}': {e}")
                erros_renomeacao += 1
                
            # --- Atualiza o Progresso ---
            progresso = (i + 1) / total_itens * 100
            self.progressbar_value.set(progresso)
            self.master.update_idletasks() 
            # --- Fim Atualização ---

        self._log_message("\n--- Processo de Renomeação Concluído ---")
        self._log_message(f"Itens renomeados com sucesso: {arquivos_renomeados}")
        
        if erros_renomeacao > 0:
            self._log_message(f"Concluído com Erros: {erros_renomeacao} erro(s). Verifique os logs.")
            messagebox.showwarning("Concluído com Erros", f"O processo de renomeação foi concluído, mas houve {erros_renomeacao} erro(s). Verifique a área de logs para mais informações.")
        else:
            messagebox.showinfo("Sucesso", "Todos os itens foram renomeados com sucesso!")
        
        self.progressbar_value.set(100) # Deixa a barra em 100% no final (melhor UX)


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