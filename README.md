# 🚗 NTW Gestão

### Sistema Web de Gestão para Estética Automotiva

O **NTW Gestão** é um sistema web desenvolvido em **Python e Flask**, criado para auxiliar empresas de estética automotiva no gerenciamento de suas atividades.

A aplicação centraliza o cadastro de clientes e veículos, agendamentos, serviços, controle financeiro, gestão de funcionários e acompanhamento de retornos.

O projeto foi desenvolvido para aplicar conhecimentos de programação, desenvolvimento web, banco de dados e organização de sistemas empresariais.

---

## 📋 Funcionalidades

- **Dashboard:** painel com indicadores operacionais e financeiros.
- **Gestão de clientes:** cadastro, consulta, pesquisa, edição e exclusão.
- **Gestão de veículos:** cadastro de veículos vinculados aos clientes.
- **Controle de serviços:** registro de serviços, valores, responsáveis e status.
- **Agenda:** acompanhamento de agendamentos e serviços em andamento.
- **Financeiro:** controle de recebimentos, valores pendentes e despesas.
- **Gestão de funcionários:** cadastro da equipe, comissões e pagamentos.
- **Retornos pelo WhatsApp:** identificação de clientes que precisam de novo contato, com links para envio de mensagens.
- **Controle de usuários:** autenticação e permissões de acesso por cargo.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Utilização |
|---|---|
| Python | Lógica de programação e regras de negócio |
| Flask | Desenvolvimento da aplicação web |
| SQLite | Banco de dados relacional |
| HTML5 | Estrutura das páginas |
| CSS3 | Estilização e responsividade |
| JavaScript | Interatividade no navegador |
| Git e GitHub | Versionamento do projeto |
| Gunicorn | Servidor WSGI para hospedagem |

---

## 📂 Estrutura do projeto

```text
NTW-Gestao/
├── app_ntw_gestao.py
├── wsgi.py
├── requirements.txt
├── README.md
└── .gitignore
```

**Descrição dos arquivos:**

- `app_ntw_gestao.py`: arquivo principal da aplicação Flask.
- `wsgi.py`: entrada da aplicação para servidores WSGI.
- `requirements.txt`: dependências necessárias para executar o projeto.
- `README.md`: documentação do projeto.
- `.gitignore`: define os arquivos que não devem ser versionados.

O banco `estetica.db` é criado localmente e não deve ser enviado ao GitHub.

---

## 💻 Como executar o projeto

### 1. Pré-requisitos

É necessário ter o Python e o Git instalados no computador.

### 2. Clonar o repositório

Abra o terminal e execute:

```bash
git clone https://github.com/Gabrielsoaresb/NTW-Gestao.git
cd NTW-Gestao
```

### 3. Criar o ambiente virtual

No Windows, utilizando o PowerShell:

```powershell
py -m venv .venv
```

### 4. Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Instalar as dependências

```powershell
pip install -r requirements.txt
```

### 6. Configurar as variáveis de ambiente

Configure uma chave de segurança para o Flask:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

Configure uma senha inicial para o administrador:

```powershell
$env:ADMIN_INITIAL_PASSWORD = Read-Host "Digite uma senha inicial para o administrador"
```

As variáveis precisam estar configuradas no terminal utilizado para iniciar a aplicação.

### 7. Executar o sistema

```powershell
python app_ntw_gestao.py
```

Depois, acesse no navegador:

**http://127.0.0.1:5000**

Na primeira execução, o sistema cria automaticamente o banco de dados SQLite e, caso ainda não existam usuários, cria o administrador inicial.

---

## 🌐 Hospedagem

O projeto possui uma entrada WSGI e pode ser adaptado para implantação em plataformas compatíveis com Python, como o Render.

**Build Command:**

```bash
pip install -r requirements.txt
```

**Start Command:**

```bash
gunicorn wsgi:app
```

As variáveis de ambiente necessárias devem ser configuradas diretamente na plataforma de hospedagem.

**Importante:** para utilização em produção, é necessário testar a implantação, revisar a segurança e configurar um banco de dados com armazenamento persistente. O SQLite local pode perder informações em ambientes com sistema de arquivos temporário.

---

## 🔐 Segurança

O projeto utiliza recursos como:

- Autenticação de usuários.
- Armazenamento de senhas por hash.
- Controle de permissões conforme o cargo.
- Proteção CSRF em formulários.
- Configuração da chave de segurança por variável de ambiente.

O sistema ainda está em desenvolvimento e deve passar por testes adicionais de segurança antes de receber dados reais em uma implantação pública.

Arquivos de banco de dados, senhas e informações confidenciais não devem ser publicados no repositório.

---

## 📈 Aprendizados do projeto

Durante o desenvolvimento do NTW Gestão, foram aplicados conhecimentos de:

- Desenvolvimento backend com Python.
- Criação de aplicações web utilizando Flask.
- Integração com banco de dados SQLite.
- Operações CRUD (criar, consultar, atualizar e excluir registros).
- Autenticação e autorização de usuários.
- Organização de rotas e funcionalidades.
- Construção de interfaces com HTML, CSS e JavaScript.
- Versionamento de código com Git e GitHub.

---

## 🚧 Status do projeto

**Em desenvolvimento e aprimoramento contínuo.**

O sistema já possui funcionalidades implementadas e executa localmente. Novos testes e melhorias estão previstos para tornar a aplicação mais robusta e preparada para hospedagem.

---

## 👨‍💻 Autor

**Gabriel Soares Bento**

Estudante de Engenharia de Software e de desenvolvimento Full Stack Python.

[LinkedIn](https://www.linkedin.com/in/gabriel-s-7b775010b) | [GitHub](https://github.com/Gabrielsoaresb)

---

**NTW Gestão — Projeto de desenvolvimento web com Python e Flask.**
