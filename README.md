📂 Renomeador Sequencial Avançado de Arquivos e Pastas
Autor: Diogo Centeno
Versão: 2.0 (2024-09-30)

Um utilitário desktop robusto e seguro, construído em Python com ttkbootstrap, projetado para automatizar a renomeação em massa de arquivos e/ou pastas. Ideal para organizar grandes volumes de documentos, o aplicativo combina um sistema de numeração sequencial inteligente com poderosos filtros e ferramentas de segurança.

<img width="849" height="798" alt="Captura de tela 2025-09-30 103436" src="https://github.com/user-attachments/assets/a808b605-bc09-4ebc-808f-56b6a561505e" />

✨ Destaques da Aplicação
💻 Instalação e Execução
Pré-requisitos
Você precisa ter o Python 3.x instalado no seu sistema.

1. Clonar o Repositório
2. Instalar Dependências
Este projeto utiliza a biblioteca ttkbootstrap para o visual moderno e Pillow para melhor compatibilidade de ícones/temas.

3. Executar o Aplicativo
Execute o arquivo principal para abrir a interface gráfica:

🚀 Guia de Uso Rápido
O aplicativo é dividido em abas e painéis numerados para facilitar o fluxo de trabalho.

Segurança (RECOMENDADO): No painel superior, utilize a opção "Fazer Backup da Pasta Selecionada Agora" e escolha um destino para o backup.

Passo 1: Seleção de Pasta: Clique em "Selecionar Pasta" e defina o diretório principal que contém os itens a serem renomeados.

Passo 2 a 6: Configuração: Defina os parâmetros:

Itens a Renomear: Arquivos, Pastas ou Ambos.

Modo Recursivo: Ative para incluir subpastas.

Nome Base: O novo nome principal (ex: Documento_001.pdf).

Sequência: Ajuste padding (Dígitos Sequenciais) e o início da contagem (Ponto de Partida).

Prévia: Clique em "Gerar Prévia no Log" (Aba 2) para simular as alterações. Verifique se a numeração e os nomes estão corretos.

Renomear: Se a prévia estiver satisfatória, clique no botão "Renomear Itens" (em verde). Uma confirmação final será solicitada, pois esta ação é irreversível sem o backup.

⚙️ Tecnologias Envolvidas
Linguagem: Python 3.x

GUI Framework: tkinter

Estilização: ttkbootstrap (Proporciona temas visuais modernos e responsividade).

Manipulação de Arquivos: os, shutil, pathlib.

Log: Utiliza o componente scrolledtext para um log detalhado de todas as operações e erros.

🤝 Contribuições
Contribuições são bem-vindas! Se você deseja adicionar um novo recurso (ex: renomeação por metadados de fotos) ou corrigir um erro, sinta-se à vontade para abrir uma Issue ou submeter um Pull Request seguindo o fluxo padrão do GitHub.

Faça um Fork do projeto.

Crie sua Branch (git checkout -b feature/nome-da-feature).

Faça o Commit das suas alterações.

Envie suas alterações para a Branch (git push origin feature/nome-da-feature).

Abra um Pull Request.

📄 Licença
Este projeto está licenciado sob a Licença MIT.
