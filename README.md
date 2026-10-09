# NTW Gestão — Gestão Automotiva

Projeto Flask original recuperado, com arquivos auxiliares para execução.

## Executar no Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app_ntw_gestao.py
```

Acesse http://127.0.0.1:5000

## Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn wsgi:app`
- Variável de ambiente obrigatória: `SECRET_KEY` com valor aleatório longo.

**ATENÇÃO ANTES DE PUBLICAR:** o código original cria um administrador padrão `admin` / `admin123`. Altere a senha antes de disponibilizar publicamente. Também revise `debug=True` no modo de execução local. O SQLite local pode perder dados em hospedagem sem armazenamento persistente; configure armazenamento persistente ou migre para banco gerenciado antes de uso real.

O arquivo `estetica.db` será criado na primeira execução. Este pacote não contém os registros de clientes antigos.
