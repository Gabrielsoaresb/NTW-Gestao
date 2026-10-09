from flask import (
    Flask, request, redirect, url_for, render_template_string,
    session, flash, get_flashed_messages
)
import sqlite3
import os
from datetime import datetime, timedelta
from urllib.parse import quote
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(BASE_DIR, "estetica.db")
app.secret_key = os.environ["SECRET_KEY"]

APP_NOME = "NTW Gestão"
APP_SUBTITULO = "Gestão Automotiva"

CARGOS = ["Administrador", "Gerente", "Financeiro", "Atendimento", "Operacional"]
PERMISSOES = {
    "Administrador": {"dashboard", "clientes", "veiculos", "servicos", "agenda", "retornos", "funcionarios", "financeiro", "despesas", "usuarios"},
    "Gerente": {"dashboard", "clientes", "veiculos", "servicos", "agenda", "retornos", "funcionarios", "financeiro", "despesas"},
    "Financeiro": {"dashboard", "financeiro", "despesas", "funcionarios"},
    "Atendimento": {"dashboard", "clientes", "veiculos", "servicos", "agenda", "retornos"},
    "Operacional": {"dashboard", "agenda", "servicos"},
}


def conectar():
    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row
    return con


def coluna_existe(con, tabela, coluna):
    return any(c["name"] == coluna for c in con.execute(f"PRAGMA table_info({tabela})").fetchall())


def adicionar_coluna(con, tabela, coluna, tipo):
    if not coluna_existe(con, tabela, coluna):
        con.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")


def criar_banco():
    con = conectar()
    con.execute("""CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        cpf TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        placa TEXT NOT NULL,
        cor TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        cargo TEXT DEFAULT 'Operacional',
        tipo_comissao TEXT DEFAULT 'Percentual',
        comissao REAL DEFAULT 0,
        ativo INTEGER DEFAULT 1
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data_servico TEXT NOT NULL,
        dias_retorno INTEGER DEFAULT 30
    )""")
    for col, tipo in {
        "horario": "TEXT",
        "status": "TEXT DEFAULT 'Agendado'",
        "retorno_realizado": "INTEGER DEFAULT 0",
        "funcionario_id": "INTEGER",
        "forma_pagamento": "TEXT",
        "status_pagamento": "TEXT DEFAULT 'Pendente'",
        "data_pagamento": "TEXT",
    }.items():
        adicionar_coluna(con, "servicos", col, tipo)

    adicionar_coluna(con, "funcionarios", "cargo", "TEXT DEFAULT 'Operacional'")
    adicionar_coluna(con, "funcionarios", "ativo", "INTEGER DEFAULT 1")

    con.execute("""CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria TEXT,
        valor REAL NOT NULL,
        data_despesa TEXT NOT NULL,
        status TEXT DEFAULT 'Pago'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS pagamentos_funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funcionario_id INTEGER NOT NULL,
        valor REAL NOT NULL,
        data_pagamento TEXT NOT NULL,
        observacao TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL,
        cargo TEXT NOT NULL,
        ativo INTEGER DEFAULT 1
    )""")

    if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        con.execute(
            "INSERT INTO usuarios (nome,usuario,senha_hash,cargo,ativo) VALUES (?,?,?,?,1)",
            ("Administrador", "admin", generate_password_hash(os.environ["ADMIN_INITIAL_PASSWORD"]), "Administrador"),
        )
    con.commit()
    con.close()


def tem_permissao(permissao_nome):
    return permissao_nome in PERMISSOES.get(session.get("cargo"), set())


def login_obrigatorio(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def permissao(nome):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "usuario_id" not in session:
                return redirect(url_for("login"))
            if not tem_permissao(nome):
                flash("Seu cargo não possui acesso a esta área.", "erro")
                return redirect(url_for("inicio"))
            return fn(*args, **kwargs)
        return wrapper
    return deco


def dinheiro(valor):
    txt = f"{float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + txt


def mes_atual():
    return datetime.now().strftime("%Y-%m")


def nome_mes(mes):
    meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    try:
        ano, numero = mes.split("-")
        return f"{meses[int(numero)]} {ano}"
    except Exception:
        return mes


def telefone_whatsapp(telefone):
    numero = "".join(c for c in (telefone or "") if c.isdigit())
    return ("55" + numero) if numero and not numero.startswith("55") else numero


def classe_status(status):
    return {
        "Agendado": "badge azul",
        "Em andamento": "badge laranja",
        "Finalizado": "badge verde",
        "Cancelado": "badge vermelho",
    }.get(status, "badge cinza")


def e(valor):
    return escape(str(valor or ""))


CSS = r'''
<style>
:root{
  --bg:#f7f8fa;--card:#fff;--txt:#172033;--muted:#64748b;--border:#dbe3ec;
  --blue:#2563eb;--green:#16a34a;--red:#dc2626;--orange:#d97706;
  --sidebar:#90D5FF;--sidebar-hover:rgba(255,255,255,.45);--dark:#0f172a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
.layout{display:flex;min-height:100vh}
.sidebar{width:270px;background:var(--sidebar);border-right:1px solid rgba(15,23,42,.12);position:fixed;inset:0 auto 0 0;padding:14px 12px;display:flex;flex-direction:column;z-index:1000;transition:width .22s ease,transform .22s ease;overflow-x:hidden}
.sidebar-top{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.menu-toggle{width:42px;height:42px;border:0;border-radius:10px;background:transparent;color:var(--dark);cursor:pointer;font-size:19px;display:grid;place-items:center;flex:0 0 auto}
.menu-toggle:hover{background:var(--sidebar-hover)}
.logo{display:flex;align-items:center;gap:10px;padding:5px 6px;text-decoration:none;color:var(--dark);font-weight:900;min-width:190px}
.logo-icon{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;background:var(--dark);color:#fff;flex:0 0 auto}
.logo-text{display:flex;flex-direction:column;line-height:1.08}.logo-text small{font-size:10px;text-transform:uppercase;letter-spacing:.08em;margin-top:4px;opacity:.72}
.menu-titulo{padding:16px 12px 7px;color:#355269;text-transform:uppercase;font-size:10px;letter-spacing:.10em;font-weight:800;white-space:nowrap}
.nav-link{display:flex;align-items:center;gap:12px;min-height:44px;padding:10px 12px;border-radius:10px;text-decoration:none;color:var(--dark);font-size:14px;font-weight:650;margin-bottom:3px;white-space:nowrap}
.nav-link i{width:21px;text-align:center;font-size:17px;flex:0 0 auto}.nav-link:hover{background:var(--sidebar-hover)}
.sidebar-footer{margin-top:auto;border-top:1px solid rgba(15,23,42,.12);padding-top:10px}.perfil{padding:9px 12px;font-size:13px;color:var(--dark);white-space:nowrap}.perfil strong{display:block}.perfil span{opacity:.72}
.conteudo{margin-left:270px;width:calc(100% - 270px);transition:margin-left .22s ease,width .22s ease}
body.menu-fechado .sidebar{width:76px}body.menu-fechado .conteudo{margin-left:76px;width:calc(100% - 76px)}body.menu-fechado .logo{display:none}body.menu-fechado .nav-link span,body.menu-fechado .menu-titulo,body.menu-fechado .perfil{display:none}body.menu-fechado .nav-link{justify-content:center;padding-left:10px;padding-right:10px}body.menu-fechado .nav-link i{width:auto}body.menu-fechado .sidebar-top{justify-content:center}
.topbar{min-height:70px;background:rgba(255,255,255,.95);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:14px 28px;position:sticky;top:0;z-index:100}.topbar h1{margin:0;font-size:20px}.topbar .cargo{font-size:13px;color:var(--muted)}
.main{max-width:1500px;padding:28px}.titulo-pagina{margin:0 0 5px;font-size:28px}.subtitulo{color:var(--muted);margin:0 0 24px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:15px;margin-bottom:25px}.card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px}.card-topo{display:flex;align-items:center;justify-content:space-between;margin-bottom:15px}.card-icone{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:#eef6ff}.card-label{color:var(--muted);font-size:13px;font-weight:600}.card-valor{margin:0;font-size:26px;font-weight:800}.painel{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:20px}.painel h3{margin:0 0 16px}
.botao{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:40px;background:var(--dark);color:#fff;border:0;border-radius:8px;padding:10px 14px;text-decoration:none;cursor:pointer;font-weight:650}.botao.azul{background:var(--blue)}.botao.verde{background:var(--green)}.botao.vermelho{background:var(--red)}.botao.cinza{background:#64748b}.botao.amarelo{background:#ca8a04}.acoes{display:flex;flex-wrap:wrap;gap:8px;margin:15px 0}
form{background:#fff;border:1px solid var(--border);border-radius:14px;padding:22px;max-width:900px}label{display:block;font-weight:650;font-size:14px;margin:14px 0 7px}input,select,textarea{width:100%;padding:11px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font-size:15px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}.item{background:#fff;border:1px solid var(--border);border-radius:12px;padding:17px;margin-bottom:10px}.item h3{margin:0 0 8px}.item p{margin:6px 0;color:#475569}.badge{display:inline-block;border-radius:999px;padding:5px 9px;color:#fff;font-size:12px;font-weight:700}.badge.azul{background:var(--blue)}.badge.verde{background:var(--green)}.badge.vermelho{background:var(--red)}.badge.laranja{background:var(--orange)}.badge.cinza{background:#64748b}
.flash{padding:12px 14px;border-radius:9px;margin-bottom:18px;background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af}.flash.erro{background:#fef2f2;border-color:#fecaca;color:#991b1b}.flash.ok{background:#f0fdf4;border-color:#bbf7d0;color:#166534}.seletor form{max-width:430px;display:flex;gap:8px;align-items:end;margin-bottom:20px}.positivo{color:#15803d}.negativo{color:#b91c1c}.muted{color:var(--muted)}
.login-page{min-height:100vh;display:grid;place-items:center;padding:20px;background:linear-gradient(135deg,#fff 0%,#eaf7ff 100%)}.login-box{width:100%;max-width:410px;background:#fff;border:1px solid var(--border);border-radius:18px;padding:30px;box-shadow:0 12px 38px rgba(15,23,42,.08)}.login-box form{border:0;padding:0}.login-logo{width:58px;height:58px;border-radius:16px;background:var(--sidebar);color:var(--dark);display:grid;place-items:center;font-size:24px;margin:0 auto 18px}.login-box h1,.login-box p{text-align:center}.login-box p{color:var(--muted)}
.overlay{display:none}
@media(max-width:760px){
  body.menu-fechado .sidebar{transform:translateX(-100%);width:270px}body.menu-fechado .conteudo{margin-left:0;width:100%}
  body:not(.menu-fechado) .sidebar{width:270px;box-shadow:12px 0 30px rgba(15,23,42,.12)}body:not(.menu-fechado) .conteudo{margin-left:0;width:100%}
  body:not(.menu-fechado) .overlay{display:block;position:fixed;inset:0;background:rgba(15,23,42,.25);z-index:900}
  body.menu-fechado .logo,body.menu-fechado .nav-link span,body.menu-fechado .menu-titulo,body.menu-fechado .perfil{display:flex}
  body.menu-fechado .menu-titulo{display:block}body.menu-fechado .perfil{display:block}body.menu-fechado .nav-link{justify-content:flex-start}
  .main{padding:18px}.topbar{padding:13px 18px}.form-grid{grid-template-columns:1fr}.cards{grid-template-columns:1fr}.titulo-pagina{font-size:24px}
}
</style>
'''

JS = r'''
<script>
function alternarMenu(){
  document.body.classList.toggle('menu-fechado');
  localStorage.setItem('ntw_menu_fechado', document.body.classList.contains('menu-fechado') ? '1' : '0');
}
function fecharMenuMobile(){
  if(window.innerWidth <= 760){
    document.body.classList.add('menu-fechado');
    localStorage.setItem('ntw_menu_fechado','1');
  }
}
(function(){
  const salvo = localStorage.getItem('ntw_menu_fechado');
  if(window.innerWidth <= 760 || salvo === '1') document.body.classList.add('menu-fechado');
})();
</script>
'''


def menu_item(url, icone, texto, p=None):
    if p and not tem_permissao(p):
        return ""
    return f'<a class="nav-link" href="{url}" title="{texto}"><i class="{icone}"></i><span>{texto}</span></a>'


def pagina(titulo, conteudo):
    mensagens = "".join(
        f'<div class="flash {categoria}">{e(msg)}</div>'
        for categoria, msg in get_flashed_messages(with_categories=True)
    )
    menu = (
        menu_item(url_for("inicio"), "fa-solid fa-chart-pie", "Visão geral", "dashboard") +
        menu_item(url_for("agenda"), "fa-regular fa-calendar-check", "Agenda", "agenda") +
        menu_item(url_for("clientes"), "fa-regular fa-address-book", "Clientes", "clientes") +
        menu_item(url_for("veiculos"), "fa-solid fa-car-side", "Veículos", "veiculos") +
        menu_item(url_for("novo_servico"), "fa-solid fa-spray-can-sparkles", "Novo serviço", "servicos") +
        menu_item(url_for("retornos"), "fa-brands fa-whatsapp", "Retornos", "retornos")
    )
    gestao = (
        menu_item(url_for("financeiro"), "fa-solid fa-chart-line", "Financeiro", "financeiro") +
        menu_item(url_for("despesas"), "fa-solid fa-file-invoice-dollar", "Despesas", "despesas") +
        menu_item(url_for("funcionarios"), "fa-solid fa-users", "Funcionários", "funcionarios") +
        menu_item(url_for("usuarios"), "fa-solid fa-user-shield", "Usuários e cargos", "usuarios")
    )
    template = f'''<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)} · {APP_NOME}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">
{CSS}
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-top">
      <button class="menu-toggle" onclick="alternarMenu()" title="Abrir ou fechar menu"><i class="fa-solid fa-bars"></i></button>
      <a class="logo" href="{url_for('inicio')}" title="Voltar ao início">
        <div class="logo-icon">N</div>
        <div class="logo-text"><span>NTW Gestão</span><small>Gestão Automotiva</small></div>
      </a>
    </div>
    <div class="menu-titulo">Menu</div>
    {menu}
    {('<div class="menu-titulo">Gestão</div>'+gestao) if gestao else ''}
    <div class="sidebar-footer">
      <div class="perfil"><strong>{e(session.get('nome',''))}</strong><span>{e(session.get('cargo',''))}</span></div>
      <a class="nav-link" href="{url_for('logout')}" title="Sair"><i class="fa-solid fa-arrow-right-from-bracket"></i><span>Sair</span></a>
    </div>
  </aside>
  <div class="overlay" onclick="fecharMenuMobile()"></div>
  <section class="conteudo">
    <header class="topbar"><h1>{APP_NOME}</h1><div class="cargo"><i class="fa-solid fa-user-shield"></i> {e(session.get('cargo',''))}</div></header>
    <main class="main">{mensagens}{conteudo}</main>
  </section>
</div>
{JS}
</body>
</html>'''
    return render_template_string(template)


def card(icone, label, valor, classe=""):
    return f'''<div class="card"><div class="card-topo"><span class="card-label">{label}</span><div class="card-icone"><i class="{icone}"></i></div></div><p class="card-valor {classe}">{valor}</p></div>'''


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        con = conectar()
        u = con.execute("SELECT * FROM usuarios WHERE usuario=? AND ativo=1", (usuario,)).fetchone()
        con.close()
        if u and check_password_hash(u["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = u["id"]
            session["nome"] = u["nome"]
            session["cargo"] = u["cargo"]
            return redirect(url_for("inicio"))
        flash("Usuário ou senha inválidos.", "erro")

    mensagens = "".join(f'<div class="flash {c}">{e(m)}</div>' for c, m in get_flashed_messages(with_categories=True))
    return render_template_string(f'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Entrar · {APP_NOME}</title><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">{CSS}</head><body><div class="login-page"><div class="login-box"><div class="login-logo"><i class="fa-solid fa-car-side"></i></div><h1>{APP_NOME}</h1><p>{APP_SUBTITULO}</p>{mensagens}<form method="post"><label>Usuário</label><input name="usuario" required autofocus><label>Senha</label><input type="password" name="senha" required><button class="botao azul" style="width:100%;margin-top:18px"><i class="fa-solid fa-right-to-bracket"></i> Entrar</button></form></div></div></body></html>''')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_obrigatorio
def inicio():
    mes = request.args.get("mes", mes_atual())
    con = conectar()
    recebidos = con.execute("SELECT COALESCE(SUM(valor),0) FROM servicos WHERE status_pagamento='Pago' AND status!='Cancelado' AND substr(COALESCE(data_pagamento,data_servico),1,7)=?", (mes,)).fetchone()[0]
    a_receber = con.execute("SELECT COALESCE(SUM(valor),0) FROM servicos WHERE status_pagamento='Pendente' AND status!='Cancelado' AND substr(data_servico,1,7)=?", (mes,)).fetchone()[0]
    despesas_pagas = con.execute("SELECT COALESCE(SUM(valor),0) FROM despesas WHERE status='Pago' AND substr(data_despesa,1,7)=?", (mes,)).fetchone()[0]
    folha = con.execute("SELECT COALESCE(SUM(valor),0) FROM pagamentos_funcionarios WHERE substr(data_pagamento,1,7)=?", (mes,)).fetchone()[0]
    finalizados = con.execute("SELECT COUNT(*) FROM servicos WHERE status='Finalizado' AND substr(data_servico,1,7)=?", (mes,)).fetchone()[0]
    clientes_qtd = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    hoje = datetime.now().strftime("%Y-%m-%d")
    agenda_hoje = con.execute("SELECT COUNT(*) FROM servicos WHERE data_servico=? AND status!='Cancelado'", (hoje,)).fetchone()[0]
    con.close()
    resultado = float(recebidos) - float(despesas_pagas) - float(folha)
    ticket = float(recebidos) / finalizados if finalizados else 0

    html = f'''<h2 class="titulo-pagina">Visão geral</h2><p class="subtitulo">Resumo de {nome_mes(mes)}.</p><div class="seletor"><form><div style="flex:1"><label>Mês</label><input type="month" name="mes" value="{mes}"></div><button class="botao"><i class="fa-solid fa-filter"></i> Filtrar</button></form></div><div class="cards">'''
    cargo = session.get("cargo")
    if cargo in ("Administrador", "Gerente"):
        html += card("fa-solid fa-arrow-trend-up", "Recebido", dinheiro(recebidos), "positivo")
        html += card("fa-solid fa-arrow-trend-down", "Saídas pagas", dinheiro(float(despesas_pagas)+float(folha)), "negativo")
        html += card("fa-solid fa-chart-line", "Resultado", dinheiro(resultado), "positivo" if resultado >= 0 else "negativo")
        html += card("fa-solid fa-car-side", "Carros finalizados", finalizados)
        html += card("fa-solid fa-receipt", "Ticket médio", dinheiro(ticket))
        html += card("fa-solid fa-wallet", "A receber", dinheiro(a_receber))
    elif cargo == "Financeiro":
        html += card("fa-solid fa-arrow-trend-up", "Recebido", dinheiro(recebidos), "positivo")
        html += card("fa-solid fa-wallet", "A receber", dinheiro(a_receber))
        html += card("fa-solid fa-file-invoice-dollar", "Despesas pagas", dinheiro(despesas_pagas), "negativo")
        html += card("fa-solid fa-hand-holding-dollar", "Pago à equipe", dinheiro(folha))
    elif cargo == "Atendimento":
        html += card("fa-solid fa-users", "Clientes cadastrados", clientes_qtd)
        html += card("fa-regular fa-calendar-check", "Serviços hoje", agenda_hoje)
        html += card("fa-solid fa-car-side", "Finalizados no mês", finalizados)
    else:
        html += card("fa-regular fa-calendar-check", "Serviços hoje", agenda_hoje)
        html += card("fa-solid fa-car-side", "Finalizados no mês", finalizados)
    html += "</div>"
    return pagina("Visão geral", html)


# CLIENTES --------------------------------------------------------------------
@app.route("/clientes")
@permissao("clientes")
def clientes():
    busca = request.args.get("q", "").strip()
    con = conectar()
    if busca:
        termo = f"%{busca}%"
        dados = con.execute("SELECT * FROM clientes WHERE nome LIKE ? OR telefone LIKE ? OR cpf LIKE ? ORDER BY nome", (termo, termo, termo)).fetchall()
    else:
        dados = con.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    con.close()
    html = f'''<h2 class="titulo-pagina">Clientes</h2><p class="subtitulo">Cadastre, consulte e exclua clientes.</p><div class="acoes"><a class="botao azul" href="{url_for('novo_cliente')}"><i class="fa-solid fa-user-plus"></i> Novo cliente</a></div><form method="get" style="max-width:600px;margin-bottom:18px"><div style="display:flex;gap:8px"><input name="q" value="{e(busca)}" placeholder="Buscar por nome, telefone ou CPF"><button class="botao"><i class="fa-solid fa-magnifying-glass"></i> Buscar</button></div></form>'''
    if not dados:
        html += '<div class="item">Nenhum cliente encontrado.</div>'
    for c in dados:
        html += f'''<div class="item"><h3><i class="fa-regular fa-user"></i> {e(c['nome'])}</h3><p><i class="fa-solid fa-phone"></i> {e(c['telefone'])}</p><p><i class="fa-regular fa-id-card"></i> CPF: {e(c['cpf'] or '-')}</p><div class="acoes"><a class="botao azul" href="{url_for('editar_cliente', id=c['id'])}"><i class="fa-solid fa-pen-to-square"></i> Editar</a><a class="botao vermelho" href="{url_for('excluir_cliente', id=c['id'])}" onclick="return confirm('Excluir este cliente? Os veículos e serviços dele também serão apagados.')"><i class="fa-solid fa-trash"></i> Excluir</a></div></div>'''
    return pagina("Clientes", html)


@app.route("/cliente/novo", methods=["GET", "POST"])
@permissao("clientes")
def novo_cliente():
    if request.method == "POST":
        con = conectar()
        con.execute("INSERT INTO clientes(nome,telefone,cpf) VALUES(?,?,?)", (request.form["nome"], request.form["telefone"], request.form.get("cpf", "")))
        con.commit(); con.close()
        flash("Cliente cadastrado.", "ok")
        return redirect(url_for("clientes"))
    return pagina("Novo cliente", '''<h2 class="titulo-pagina">Novo cliente</h2><p class="subtitulo">Cadastre os dados do cliente.</p><form method="post"><label>Nome</label><input name="nome" required><label>Telefone</label><input name="telefone" required><label>CPF</label><input name="cpf"><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar cliente</button></form>''')


@app.route("/cliente/<int:id>/editar", methods=["GET", "POST"])
@permissao("clientes")
def editar_cliente(id):
    con = conectar(); c = con.execute("SELECT * FROM clientes WHERE id=?", (id,)).fetchone()
    if not c:
        con.close(); flash("Cliente não encontrado.", "erro"); return redirect(url_for("clientes"))
    if request.method == "POST":
        con.execute("UPDATE clientes SET nome=?,telefone=?,cpf=? WHERE id=?", (request.form["nome"], request.form["telefone"], request.form.get("cpf", ""), id))
        con.commit(); con.close(); flash("Cliente atualizado.", "ok"); return redirect(url_for("clientes"))
    html = f'''<h2 class="titulo-pagina">Editar cliente</h2><form method="post"><label>Nome</label><input name="nome" value="{e(c['nome'])}" required><label>Telefone</label><input name="telefone" value="{e(c['telefone'])}" required><label>CPF</label><input name="cpf" value="{e(c['cpf'])}"><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar alterações</button></form>'''
    con.close(); return pagina("Editar cliente", html)


@app.route("/cliente/<int:id>/excluir")
@permissao("clientes")
def excluir_cliente(id):
    con = conectar()
    veiculos_ids = [r[0] for r in con.execute("SELECT id FROM veiculos WHERE cliente_id=?", (id,)).fetchall()]
    for vid in veiculos_ids:
        con.execute("DELETE FROM servicos WHERE veiculo_id=?", (vid,))
    con.execute("DELETE FROM veiculos WHERE cliente_id=?", (id,))
    con.execute("DELETE FROM clientes WHERE id=?", (id,))
    con.commit(); con.close(); flash("Cliente, veículos e serviços relacionados foram excluídos.", "ok")
    return redirect(url_for("clientes"))


# VEÍCULOS --------------------------------------------------------------------
@app.route("/veiculos")
@permissao("veiculos")
def veiculos():
    con = conectar()
    dados = con.execute("SELECT v.*, c.nome AS cliente FROM veiculos v JOIN clientes c ON c.id=v.cliente_id ORDER BY c.nome,v.marca,v.modelo").fetchall()
    con.close()
    html = f'''<h2 class="titulo-pagina">Veículos</h2><p class="subtitulo">Veículos cadastrados.</p><div class="acoes"><a class="botao azul" href="{url_for('novo_veiculo')}"><i class="fa-solid fa-car-side"></i> Novo veículo</a></div>'''
    if not dados: html += '<div class="item">Nenhum veículo cadastrado.</div>'
    for v in dados:
        html += f'''<div class="item"><h3><i class="fa-solid fa-car"></i> {e(v['marca'])} {e(v['modelo'])}</h3><p>Cliente: <strong>{e(v['cliente'])}</strong></p><p>Placa: {e(v['placa'])} · Cor: {e(v['cor'] or '-')}</p><div class="acoes"><a class="botao azul" href="{url_for('editar_veiculo', id=v['id'])}"><i class="fa-solid fa-pen-to-square"></i> Editar</a><a class="botao vermelho" href="{url_for('excluir_veiculo', id=v['id'])}" onclick="return confirm('Excluir este veículo? Os serviços vinculados a ele também serão apagados.')"><i class="fa-solid fa-trash"></i> Excluir</a></div></div>'''
    return pagina("Veículos", html)


@app.route("/veiculo/novo", methods=["GET", "POST"])
@permissao("veiculos")
def novo_veiculo():
    con = conectar(); clientes_lista = con.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    if request.method == "POST":
        con.execute("INSERT INTO veiculos(cliente_id,marca,modelo,placa,cor) VALUES(?,?,?,?,?)", (request.form["cliente_id"], request.form["marca"], request.form["modelo"], request.form["placa"], request.form.get("cor", "")))
        con.commit(); con.close(); flash("Veículo cadastrado.", "ok"); return redirect(url_for("veiculos"))
    ops = "".join(f'<option value="{c["id"]}">{e(c["nome"])}</option>' for c in clientes_lista)
    con.close()
    return pagina("Novo veículo", f'''<h2 class="titulo-pagina">Novo veículo</h2><form method="post"><label>Cliente</label><select name="cliente_id" required>{ops}</select><div class="form-grid"><div><label>Marca</label><input name="marca" required></div><div><label>Modelo</label><input name="modelo" required></div><div><label>Placa</label><input name="placa" required></div><div><label>Cor</label><input name="cor"></div></div><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar veículo</button></form>''')


@app.route("/veiculo/<int:id>/editar", methods=["GET", "POST"])
@permissao("veiculos")
def editar_veiculo(id):
    con = conectar(); v = con.execute("SELECT * FROM veiculos WHERE id=?", (id,)).fetchone(); cs = con.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    if not v:
        con.close(); flash("Veículo não encontrado.", "erro"); return redirect(url_for("veiculos"))
    if request.method == "POST":
        con.execute("UPDATE veiculos SET cliente_id=?,marca=?,modelo=?,placa=?,cor=? WHERE id=?", (request.form["cliente_id"], request.form["marca"], request.form["modelo"], request.form["placa"], request.form.get("cor", ""), id))
        con.commit(); con.close(); flash("Veículo atualizado.", "ok"); return redirect(url_for("veiculos"))
    ops = "".join(f'<option value="{c["id"]}" {"selected" if c["id"]==v["cliente_id"] else ""}>{e(c["nome"])}</option>' for c in cs)
    html = f'''<h2 class="titulo-pagina">Editar veículo</h2><form method="post"><label>Cliente</label><select name="cliente_id">{ops}</select><div class="form-grid"><div><label>Marca</label><input name="marca" value="{e(v['marca'])}" required></div><div><label>Modelo</label><input name="modelo" value="{e(v['modelo'])}" required></div><div><label>Placa</label><input name="placa" value="{e(v['placa'])}" required></div><div><label>Cor</label><input name="cor" value="{e(v['cor'])}"></div></div><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar alterações</button></form>'''
    con.close(); return pagina("Editar veículo", html)


@app.route("/veiculo/<int:id>/excluir")
@permissao("veiculos")
def excluir_veiculo(id):
    con = conectar(); con.execute("DELETE FROM servicos WHERE veiculo_id=?", (id,)); con.execute("DELETE FROM veiculos WHERE id=?", (id,)); con.commit(); con.close(); flash("Veículo e serviços relacionados foram excluídos.", "ok"); return redirect(url_for("veiculos"))


# SERVIÇOS / AGENDA -----------------------------------------------------------
@app.route("/servico/novo", methods=["GET", "POST"])
@permissao("servicos")
def novo_servico():
    con = conectar()
    veics = con.execute("SELECT v.*,c.nome AS cliente FROM veiculos v JOIN clientes c ON c.id=v.cliente_id ORDER BY c.nome").fetchall()
    funcs = con.execute("SELECT * FROM funcionarios WHERE ativo=1 ORDER BY nome").fetchall()
    if request.method == "POST":
        valor = request.form["valor"].replace(".", "").replace(",", ".")
        pago = request.form["status_pagamento"]
        data_pagamento = request.form.get("data_pagamento") or None
        if pago != "Pago": data_pagamento = None
        con.execute("""INSERT INTO servicos(veiculo_id,funcionario_id,descricao,valor,data_servico,horario,dias_retorno,status,retorno_realizado,forma_pagamento,status_pagamento,data_pagamento) VALUES(?,?,?,?,?,?,?,?,0,?,?,?)""",
                    (request.form["veiculo_id"], request.form.get("funcionario_id") or None, request.form["descricao"], valor, request.form["data_servico"], request.form.get("horario"), request.form["dias_retorno"], request.form["status"], request.form["forma_pagamento"], pago, data_pagamento))
        con.commit(); con.close(); flash("Serviço cadastrado.", "ok"); return redirect(url_for("agenda"))
    ov = "".join(f'<option value="{v["id"]}">{e(v["cliente"])} · {e(v["marca"])} {e(v["modelo"])} · {e(v["placa"])}</option>' for v in veics)
    of = '<option value="">Sem responsável</option>' + "".join(f'<option value="{f["id"]}">{e(f["nome"])}</option>' for f in funcs)
    hoje = datetime.now().strftime("%Y-%m-%d"); con.close()
    return pagina("Novo serviço", f'''<h2 class="titulo-pagina">Novo serviço</h2><p class="subtitulo">Agendamento, responsável e pagamento.</p><form method="post"><label>Veículo</label><select name="veiculo_id" required>{ov}</select><label>Funcionário responsável</label><select name="funcionario_id">{of}</select><label>Serviço</label><input name="descricao" required><div class="form-grid"><div><label>Valor</label><input name="valor" required></div><div><label>Data</label><input type="date" name="data_servico" value="{hoje}" required></div><div><label>Horário</label><input type="time" name="horario"></div><div><label>Status</label><select name="status"><option>Agendado</option><option>Em andamento</option><option>Finalizado</option><option>Cancelado</option></select></div><div><label>Forma de pagamento</label><select name="forma_pagamento"><option>PIX</option><option>Dinheiro</option><option>Cartão de débito</option><option>Cartão de crédito</option><option>Outro</option></select></div><div><label>Status pagamento</label><select name="status_pagamento"><option>Pendente</option><option>Pago</option></select></div><div><label>Data pagamento</label><input type="date" name="data_pagamento" value="{hoje}"></div><div><label>Retorno em dias</label><input type="number" name="dias_retorno" value="30"></div></div><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar serviço</button></form>''')


@app.route("/agenda")
@permissao("agenda")
def agenda():
    con = conectar(); dados = con.execute("""SELECT s.*,c.nome AS cliente,v.marca,v.modelo,v.placa,f.nome AS funcionario FROM servicos s JOIN veiculos v ON v.id=s.veiculo_id JOIN clientes c ON c.id=v.cliente_id LEFT JOIN funcionarios f ON f.id=s.funcionario_id ORDER BY s.data_servico DESC,s.horario DESC""").fetchall(); con.close()
    html = '<h2 class="titulo-pagina">Agenda</h2><p class="subtitulo">Serviços agendados e em execução.</p>'
    if tem_permissao("servicos"): html += f'<div class="acoes"><a class="botao azul" href="{url_for("novo_servico")}"><i class="fa-solid fa-plus"></i> Novo serviço</a></div>'
    if not dados: html += '<div class="item">Nenhum serviço cadastrado.</div>'
    for s in dados:
        try: data = datetime.strptime(s["data_servico"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception: data = e(s["data_servico"])
        pagar = f'<a class="botao azul" href="{url_for("pagar_servico", id=s["id"])}"><i class="fa-solid fa-credit-card"></i> Marcar pago</a>' if tem_permissao("financeiro") and s["status_pagamento"] != "Pago" else ""
        excluir = f'<a class="botao vermelho" href="{url_for("excluir_servico", id=s["id"])}" onclick="return confirm(\'Excluir este serviço definitivamente?\')"><i class="fa-solid fa-trash"></i> Excluir</a>' if tem_permissao("servicos") else ""
        html += f'''<div class="item"><h3>{e(s['cliente'])} · {e(s['marca'])} {e(s['modelo'])}</h3><p><i class="fa-regular fa-calendar"></i> {data} às {e(s['horario'] or '--:--')} · {e(s['placa'])}</p><p><i class="fa-solid fa-spray-can-sparkles"></i> {e(s['descricao'])} · <strong>{dinheiro(s['valor'])}</strong></p><p><i class="fa-regular fa-user"></i> {e(s['funcionario'] or 'Sem responsável')}</p><p>Pagamento: <strong>{e(s['status_pagamento'] or 'Pendente')}</strong></p><span class="{classe_status(s['status'])}">{e(s['status'])}</span><div class="acoes"><a class="botao cinza" href="{url_for('mudar_status', id=s['id'], status='Em andamento')}"><i class="fa-solid fa-play"></i> Iniciar</a><a class="botao verde" href="{url_for('mudar_status', id=s['id'], status='Finalizado')}"><i class="fa-solid fa-check"></i> Finalizar</a>{pagar}<a class="botao amarelo" href="{url_for('mudar_status', id=s['id'], status='Cancelado')}"><i class="fa-solid fa-ban"></i> Cancelar</a>{excluir}</div></div>'''
    return pagina("Agenda", html)


@app.route("/servico/<int:id>/status/<status>")
@permissao("agenda")
def mudar_status(id, status):
    if status not in ["Agendado", "Em andamento", "Finalizado", "Cancelado"]: return redirect(url_for("agenda"))
    con = conectar(); con.execute("UPDATE servicos SET status=? WHERE id=?", (status, id)); con.commit(); con.close(); return redirect(url_for("agenda"))


@app.route("/servico/<int:id>/pagar")
@permissao("financeiro")
def pagar_servico(id):
    con = conectar(); con.execute("UPDATE servicos SET status_pagamento='Pago',data_pagamento=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d"), id)); con.commit(); con.close(); flash("Pagamento marcado como pago.", "ok"); return redirect(url_for("agenda"))


@app.route("/servico/<int:id>/excluir")
@permissao("servicos")
def excluir_servico(id):
    con = conectar(); con.execute("DELETE FROM servicos WHERE id=?", (id,)); con.commit(); con.close(); flash("Serviço excluído.", "ok"); return redirect(url_for("agenda"))


# RETORNOS --------------------------------------------------------------------
@app.route("/retornos")
@permissao("retornos")
def retornos():
    con = conectar(); dados = con.execute("""SELECT s.*,c.nome,c.telefone,v.marca,v.modelo FROM servicos s JOIN veiculos v ON v.id=s.veiculo_id JOIN clientes c ON c.id=v.cliente_id WHERE s.retorno_realizado=0 AND s.status!='Cancelado' ORDER BY s.data_servico""").fetchall(); con.close()
    hoje = datetime.now().date(); html = '<h2 class="titulo-pagina">Retornos</h2><p class="subtitulo">Clientes que já estão na hora de receber novo contato.</p>'; achou = False
    for s in dados:
        try: retorno = datetime.strptime(s["data_servico"], "%Y-%m-%d").date() + timedelta(days=int(s["dias_retorno"] or 0))
        except Exception: continue
        if retorno <= hoje:
            achou = True
            msg = f'Olá, {s["nome"]}! Já está na época de cuidar novamente do seu {s["marca"]} {s["modelo"]}. Quer agendar um horário?'
            link = f'https://wa.me/{telefone_whatsapp(s["telefone"])}?text={quote(msg)}'
            html += f'''<div class="item"><h3>{e(s['nome'])}</h3><p>{e(s['marca'])} {e(s['modelo'])}</p><p>Retorno desde {retorno.strftime('%d/%m/%Y')}</p><div class="acoes"><a class="botao verde" href="{link}" target="_blank"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a><a class="botao cinza" href="{url_for('concluir_retorno', id=s['id'])}"><i class="fa-solid fa-check"></i> Marcar contatado</a></div></div>'''
    if not achou: html += '<div class="item">Nenhum retorno pendente.</div>'
    return pagina("Retornos", html)


@app.route("/retorno/<int:id>/concluir")
@permissao("retornos")
def concluir_retorno(id):
    con = conectar(); con.execute("UPDATE servicos SET retorno_realizado=1 WHERE id=?", (id,)); con.commit(); con.close(); flash("Retorno marcado como contatado.", "ok"); return redirect(url_for("retornos"))


# FINANCEIRO / DESPESAS -------------------------------------------------------
@app.route("/financeiro")
@permissao("financeiro")
def financeiro():
    mes = request.args.get("mes", mes_atual()); con = conectar()
    r = con.execute("SELECT COALESCE(SUM(valor),0) FROM servicos WHERE status_pagamento='Pago' AND status!='Cancelado' AND substr(COALESCE(data_pagamento,data_servico),1,7)=?", (mes,)).fetchone()[0]
    ar = con.execute("SELECT COALESCE(SUM(valor),0) FROM servicos WHERE status_pagamento='Pendente' AND status!='Cancelado' AND substr(data_servico,1,7)=?", (mes,)).fetchone()[0]
    d = con.execute("SELECT COALESCE(SUM(valor),0) FROM despesas WHERE status='Pago' AND substr(data_despesa,1,7)=?", (mes,)).fetchone()[0]
    f = con.execute("SELECT COALESCE(SUM(valor),0) FROM pagamentos_funcionarios WHERE substr(data_pagamento,1,7)=?", (mes,)).fetchone()[0]
    con.close(); res = float(r) - float(d) - float(f)
    html = f'''<h2 class="titulo-pagina">Financeiro</h2><p class="subtitulo">Resumo de {nome_mes(mes)}.</p><div class="seletor"><form><div style="flex:1"><label>Mês</label><input type="month" name="mes" value="{mes}"></div><button class="botao"><i class="fa-solid fa-filter"></i> Filtrar</button></form></div><div class="cards">{card('fa-solid fa-arrow-trend-up','Recebido',dinheiro(r),'positivo')}{card('fa-solid fa-wallet','A receber',dinheiro(ar))}{card('fa-solid fa-file-invoice-dollar','Despesas',dinheiro(d),'negativo')}{card('fa-solid fa-users','Folha paga',dinheiro(f))}{card('fa-solid fa-chart-line','Resultado',dinheiro(res),'positivo' if res>=0 else 'negativo')}</div>'''
    return pagina("Financeiro", html)


@app.route("/despesas")
@permissao("despesas")
def despesas():
    con = conectar(); dados = con.execute("SELECT * FROM despesas ORDER BY data_despesa DESC,id DESC").fetchall(); con.close()
    html = f'''<h2 class="titulo-pagina">Despesas</h2><p class="subtitulo">Controle das saídas.</p><div class="acoes"><a class="botao vermelho" href="{url_for('nova_despesa')}"><i class="fa-solid fa-plus"></i> Nova despesa</a></div>'''
    if not dados: html += '<div class="item">Nenhuma despesa cadastrada.</div>'
    for d in dados:
        html += f'''<div class="item"><h3>{e(d['descricao'])}</h3><p>{e(d['categoria'] or 'Sem categoria')} · {e(d['data_despesa'])}</p><p><strong>{dinheiro(d['valor'])}</strong> · {e(d['status'])}</p><div class="acoes"><a class="botao vermelho" href="{url_for('excluir_despesa', id=d['id'])}" onclick="return confirm('Excluir esta despesa?')"><i class="fa-solid fa-trash"></i> Excluir</a></div></div>'''
    return pagina("Despesas", html)


@app.route("/despesa/nova", methods=["GET", "POST"])
@permissao("despesas")
def nova_despesa():
    if request.method == "POST":
        valor = request.form["valor"].replace(".", "").replace(",", ".")
        con = conectar(); con.execute("INSERT INTO despesas(descricao,categoria,valor,data_despesa,status) VALUES(?,?,?,?,?)", (request.form["descricao"], request.form["categoria"], valor, request.form["data_despesa"], request.form["status"])); con.commit(); con.close(); flash("Despesa cadastrada.", "ok"); return redirect(url_for("despesas"))
    hoje = datetime.now().strftime("%Y-%m-%d")
    return pagina("Nova despesa", f'''<h2 class="titulo-pagina">Nova despesa</h2><form method="post"><label>Descrição</label><input name="descricao" required><label>Categoria</label><select name="categoria"><option>Produtos</option><option>Aluguel</option><option>Água</option><option>Energia</option><option>Marketing</option><option>Fornecedor</option><option>Manutenção</option><option>Outros</option></select><label>Valor</label><input name="valor" required><label>Data</label><input type="date" name="data_despesa" value="{hoje}" required><label>Status</label><select name="status"><option>Pago</option><option>Pendente</option></select><button class="botao vermelho" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar</button></form>''')


@app.route("/despesa/<int:id>/excluir")
@permissao("despesas")
def excluir_despesa(id):
    con = conectar(); con.execute("DELETE FROM despesas WHERE id=?", (id,)); con.commit(); con.close(); flash("Despesa excluída.", "ok"); return redirect(url_for("despesas"))


# FUNCIONÁRIOS ----------------------------------------------------------------
@app.route("/funcionarios")
@permissao("funcionarios")
def funcionarios():
    con = conectar(); funcs = con.execute("SELECT * FROM funcionarios ORDER BY ativo DESC,nome").fetchall(); pags = con.execute("""SELECT p.*,f.nome AS funcionario FROM pagamentos_funcionarios p JOIN funcionarios f ON f.id=p.funcionario_id ORDER BY p.data_pagamento DESC,p.id DESC LIMIT 30""").fetchall(); con.close()
    html = '<h2 class="titulo-pagina">Funcionários</h2><p class="subtitulo">Equipe, cargos, comissão e pagamentos.</p><div class="acoes">'
    if session.get("cargo") in ("Administrador", "Gerente"): html += f'<a class="botao azul" href="{url_for("novo_funcionario")}"><i class="fa-solid fa-user-plus"></i> Novo funcionário</a>'
    if tem_permissao("financeiro"): html += f'<a class="botao verde" href="{url_for("pagamento_funcionario")}"><i class="fa-solid fa-money-bill-transfer"></i> Registrar pagamento</a>'
    html += '</div>'
    for f in funcs:
        excluir = f'<a class="botao vermelho" href="{url_for("excluir_funcionario", id=f["id"])}" onclick="return confirm(\'Excluir este funcionário? Os pagamentos dele serão removidos e os serviços ficarão sem responsável.\')"><i class="fa-solid fa-trash"></i> Excluir</a>' if session.get("cargo") in ("Administrador", "Gerente") else ""
        html += f'''<div class="item"><h3>{e(f['nome'])}</h3><p><i class="fa-solid fa-id-badge"></i> {e(f['cargo'] or 'Operacional')}</p><p><i class="fa-solid fa-phone"></i> {e(f['telefone'] or '-')}</p><p>Comissão: <strong>{float(f['comissao'] or 0):g}{'%' if f['tipo_comissao']=='Percentual' else ' por carro'}</strong></p><div class="acoes">{excluir}</div></div>'''
    if tem_permissao("financeiro"):
        html += '<div class="painel"><h3><i class="fa-solid fa-clock-rotate-left"></i> Pagamentos recentes</h3>'
        if not pags: html += '<p class="muted">Nenhum pagamento registrado.</p>'
        for p in pags:
            html += f'''<div class="item"><strong>{e(p['funcionario'])}</strong><p>{e(p['data_pagamento'])} · {dinheiro(p['valor'])}</p><div class="acoes"><a class="botao vermelho" href="{url_for('excluir_pagamento_funcionario', id=p['id'])}" onclick="return confirm('Excluir este pagamento?')"><i class="fa-solid fa-trash"></i> Excluir pagamento</a></div></div>'''
        html += '</div>'
    return pagina("Funcionários", html)


@app.route("/funcionario/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_funcionario():
    if session.get("cargo") not in ("Administrador", "Gerente"):
        flash("Sem permissão.", "erro"); return redirect(url_for("inicio"))
    if request.method == "POST":
        con = conectar(); con.execute("INSERT INTO funcionarios(nome,telefone,cargo,tipo_comissao,comissao,ativo) VALUES(?,?,?,?,?,1)", (request.form["nome"], request.form.get("telefone", ""), request.form["cargo"], request.form["tipo_comissao"], request.form["comissao"].replace(",", "."))); con.commit(); con.close(); flash("Funcionário cadastrado.", "ok"); return redirect(url_for("funcionarios"))
    ops = "".join(f"<option>{c}</option>" for c in CARGOS if c != "Administrador")
    return pagina("Novo funcionário", f'''<h2 class="titulo-pagina">Novo funcionário</h2><form method="post"><label>Nome</label><input name="nome" required><label>Telefone</label><input name="telefone"><label>Cargo</label><select name="cargo">{ops}</select><label>Tipo de comissão</label><select name="tipo_comissao"><option>Percentual</option><option>Valor por carro</option></select><label>Comissão</label><input name="comissao" required><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Salvar</button></form>''')


@app.route("/funcionario/<int:id>/excluir")
@login_obrigatorio
def excluir_funcionario(id):
    if session.get("cargo") not in ("Administrador", "Gerente"):
        flash("Sem permissão.", "erro"); return redirect(url_for("inicio"))
    con = conectar(); con.execute("UPDATE servicos SET funcionario_id=NULL WHERE funcionario_id=?", (id,)); con.execute("DELETE FROM pagamentos_funcionarios WHERE funcionario_id=?", (id,)); con.execute("DELETE FROM funcionarios WHERE id=?", (id,)); con.commit(); con.close(); flash("Funcionário excluído.", "ok"); return redirect(url_for("funcionarios"))


@app.route("/funcionario/pagamento", methods=["GET", "POST"])
@permissao("financeiro")
def pagamento_funcionario():
    con = conectar(); funcs = con.execute("SELECT * FROM funcionarios WHERE ativo=1 ORDER BY nome").fetchall()
    if request.method == "POST":
        con.execute("INSERT INTO pagamentos_funcionarios(funcionario_id,valor,data_pagamento,observacao) VALUES(?,?,?,?)", (request.form["funcionario_id"], request.form["valor"].replace(".", "").replace(",", "."), request.form["data_pagamento"], request.form.get("observacao", ""))); con.commit(); con.close(); flash("Pagamento registrado.", "ok"); return redirect(url_for("funcionarios"))
    ops = "".join(f'<option value="{f["id"]}">{e(f["nome"])}</option>' for f in funcs); hoje = datetime.now().strftime("%Y-%m-%d"); con.close()
    return pagina("Pagamento", f'''<h2 class="titulo-pagina">Pagamento de funcionário</h2><form method="post"><label>Funcionário</label><select name="funcionario_id">{ops}</select><label>Valor</label><input name="valor" required><label>Data</label><input type="date" name="data_pagamento" value="{hoje}" required><label>Observação</label><textarea name="observacao"></textarea><button class="botao verde" style="margin-top:18px"><i class="fa-solid fa-floppy-disk"></i> Registrar</button></form>''')


@app.route("/funcionario/pagamento/<int:id>/excluir")
@permissao("financeiro")
def excluir_pagamento_funcionario(id):
    con = conectar(); con.execute("DELETE FROM pagamentos_funcionarios WHERE id=?", (id,)); con.commit(); con.close(); flash("Pagamento excluído.", "ok"); return redirect(url_for("funcionarios"))


# USUÁRIOS --------------------------------------------------------------------
@app.route("/usuarios")
@permissao("usuarios")
def usuarios():
    con = conectar(); dados = con.execute("SELECT * FROM usuarios ORDER BY nome").fetchall(); con.close()
    html = f'''<h2 class="titulo-pagina">Usuários e cargos</h2><p class="subtitulo">Cada cargo vê apenas o que precisa.</p><div class="acoes"><a class="botao azul" href="{url_for('novo_usuario')}"><i class="fa-solid fa-user-plus"></i> Novo usuário</a></div><div class="painel"><h3><i class="fa-solid fa-shield-halved"></i> Permissões</h3><p><strong>Administrador:</strong> acesso completo.</p><p><strong>Gerente:</strong> operação, equipe e financeiro.</p><p><strong>Financeiro:</strong> recebimentos, despesas e pagamentos.</p><p><strong>Atendimento:</strong> clientes, veículos, agenda, serviços e retornos.</p><p><strong>Operacional:</strong> agenda e serviços.</p></div>'''
    for u in dados:
        if u["id"] == session.get("usuario_id"):
            acao = '<span class="muted">Usuário conectado — não pode ser excluído agora.</span>'
        else:
            acao = f'<a class="botao vermelho" href="{url_for("excluir_usuario", id=u["id"])}" onclick="return confirm(\'Excluir este usuário?\')"><i class="fa-solid fa-trash"></i> Excluir</a>'
        html += f'''<div class="item"><h3>{e(u['nome'])}</h3><p><i class="fa-solid fa-user"></i> {e(u['usuario'])}</p><p><i class="fa-solid fa-id-badge"></i> <strong>{e(u['cargo'])}</strong></p><div class="acoes">{acao}</div></div>'''
    return pagina("Usuários e cargos", html)


@app.route("/usuario/novo", methods=["GET", "POST"])
@permissao("usuarios")
def novo_usuario():
    if request.method == "POST":
        con = conectar()
        try:
            con.execute("INSERT INTO usuarios(nome,usuario,senha_hash,cargo,ativo) VALUES(?,?,?,?,1)", (request.form["nome"], request.form["usuario"], generate_password_hash(request.form["senha"]), request.form["cargo"])); con.commit()
        except sqlite3.IntegrityError:
            con.close(); flash("Esse usuário já existe.", "erro"); return redirect(url_for("novo_usuario"))
        con.close(); flash("Usuário criado.", "ok"); return redirect(url_for("usuarios"))
    ops = "".join(f"<option>{c}</option>" for c in CARGOS)
    return pagina("Novo usuário", f'''<h2 class="titulo-pagina">Novo usuário</h2><p class="subtitulo">O cargo define o painel e o menu.</p><form method="post"><label>Nome</label><input name="nome" required><label>Usuário</label><input name="usuario" required><label>Senha</label><input type="password" name="senha" required><label>Cargo</label><select name="cargo">{ops}</select><button class="botao azul" style="margin-top:18px"><i class="fa-solid fa-user-shield"></i> Criar usuário</button></form>''')


@app.route("/usuario/<int:id>/excluir")
@permissao("usuarios")
def excluir_usuario(id):
    if id == session.get("usuario_id"):
        flash("Você não pode excluir o usuário que está conectado.", "erro"); return redirect(url_for("usuarios"))
    con = conectar(); u = con.execute("SELECT * FROM usuarios WHERE id=?", (id,)).fetchone()
    if not u:
        con.close(); flash("Usuário não encontrado.", "erro"); return redirect(url_for("usuarios"))
    if u["cargo"] == "Administrador":
        admins = con.execute("SELECT COUNT(*) FROM usuarios WHERE cargo='Administrador' AND ativo=1").fetchone()[0]
        if admins <= 1:
            con.close(); flash("Não é possível excluir o último administrador.", "erro"); return redirect(url_for("usuarios"))
    con.execute("DELETE FROM usuarios WHERE id=?", (id,)); con.commit(); con.close(); flash("Usuário excluído.", "ok"); return redirect(url_for("usuarios"))


if __name__ == "__main__":
    criar_banco()
    app.run(debug=False, host="127.0.0.1", port=5000)
