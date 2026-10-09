NTW Gestão

Sistema Web de Gestão para Estética Automotiva

O NTW Gestão é uma aplicação web desenvolvida em Python com Flask, projetada para auxiliar empresas de estética automotiva no gerenciamento de suas operações.

O sistema centraliza o cadastro de clientes e veículos, a organização dos serviços, o controle financeiro, a gestão de funcionários e o acompanhamento de retornos.

Funcionalidades

Dashboard: visão geral das operações e indicadores financeiros.

Clientes: cadastro, consulta, pesquisa, edição e exclusão.

Veículos: gerenciamento de veículos vinculados aos clientes.

Serviços: registro de serviços, valores, responsáveis e status.

Agenda: acompanhamento de agendamentos e serviços em andamento.

Financeiro: controle de recebimentos, valores pendentes e despesas.

Funcionários: cadastro da equipe, comissões e pagamentos.

Retornos: identificação de clientes para novo contato, com integração por link do WhatsApp.

Usuários e permissões: autenticação e controle de acesso conforme o cargo.

Tecnologias utilizadas

Python: lógica de programação e regras de negócio.

Flask: desenvolvimento da aplicação web.

SQLite: armazenamento local das informações.

HTML5 e CSS3: estrutura e estilização da interface.

JavaScript: interações no navegador.

Git e GitHub: versionamento e gerenciamento do código.

Gunicorn: servidor WSGI para implantação.

Como executar localmente

Pré-requisito: Python instalado.

Clone o repositório:

git clone https://github.com/Gabrielsoaresb/NTW-Gestao.git
cd NTW-Gestao

No PowerShell, crie e ative o ambiente virtual:

py -m venv .venv
.\.venv\Scripts\Activate.ps1

Instale as dependências:

pip install -r requirements.txt

Configure as variáveis de ambiente:

$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:ADMIN_INITIAL_PASSWORD = Read-Host "Digite uma senha inicial para o administrador"

Inicie a aplicação:

python app_ntw_gestao.py

Acesse:

http://127.0.0.1:5000

O banco de dados SQLite é criado automaticamente na primeira execução.

Observação: a senha inicial é utilizada quando o primeiro administrador precisa ser criado. Não compartilhe senhas nem arquivos de banco de dados.

Implantação

O projeto possui uma configuração WSGI para implantação com Gunicorn.

Exemplo de comandos para uma hospedagem compatível:

Build Command

pip install -r requirements.txt

Start Command

gunicorn wsgi:app

Antes de disponibilizar a aplicação publicamente, é necessário validar as configurações de segurança, definir as variáveis de ambiente e utilizar uma estratégia de armazenamento persistente para os dados.

Segurança

A aplicação utiliza autenticação de usuários, armazenamento de senhas por hash, permissões baseadas em cargos e proteção CSRF para formulários.

O arquivo do banco de dados não deve ser publicado no repositório. O sistema deve passar por testes adicionais antes de ser utilizado com dados reais em produção.

Status do projeto

Em desenvolvimento e aprimoramento contínuo.

O projeto demonstra conhecimentos práticos em desenvolvimento web com Python, Flask, bancos de dados relacionais, autenticação, gerenciamento de rotas e controle de acesso.

Autor

Gabriel Soares Bento

Estudante de Engenharia de Software e desenvolvimento Full Stack Python.

LinkedIn | GitHub
