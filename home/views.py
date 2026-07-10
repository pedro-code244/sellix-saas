from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import yfinance as yf
import json
from django.db.models import Sum
from decimal import Decimal
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password


from .models import Company, Funcionario, Membership, TableItem, Venda, Cliente, NewVenda


# -----------------------
# PÁGINAS PÚBLICAS
# -----------------------

def index(request):
    return render(request, 'core/index.html')


def modulos(request):
    return render(request, 'core/modulos.html')

def sellix(request):
    return render(request, 'core/sellix.html')

def bloqueio(request):
    return render(request, 'core/bloqueio.html')


def politica(request):
    return render(request, 'core/politica.html')


# -----------------------
# LOGIN
# -----------------------

def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # 1. primeiro verifica se user existe
        if user is None:
            return render(request, 'core/login.html', {
                'error': 'Login inválido, tente novamente'
            })

        # Superuser deve conseguir logar mesmo sem membership ou bloqueio
        if user.is_superuser:
            auth_login(request, user)
            return redirect('controle')

        # 2. pega membership com segurança
        membership = Membership.objects.filter(user=user).first()

        if not membership:
            return render(request, "core/bloqueio.html", {"username": user.username})

        # 3. verifica se está ativo (superuser pula essa verificação acima)
        if not membership.is_active:
            return render(request, "core/bloqueio.html", {"username": user.username})

        # 4. login
        auth_login(request, user)

        # 5. redirect
        if user.is_superuser:
            return redirect('controle')

        return redirect('dashboard')

    return render(request, 'core/login.html')


# -----------------------
# CADASTRO
# -----------------------

def cadastro(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')
        contato = request.POST.get('contato')

        if User.objects.filter(username=username).exists():
            return render(request, 'core/cadastro.html', {
                'error': 'Usuário já existe'
            })

        user = User.objects.create_user(
            username=username,
            password=make_password(password)
        )

        company = Company.objects.create(
            name=username,
            contato=contato
        )

        Membership.objects.create(
            user=user,
            company=company,
            is_admin=True
        )

        auth_login(request, user)

        return redirect('dashboard')

    return render(request, 'core/cadastro.html')


# -----------------------
# DASHBOARD
# -----------------------
@login_required
def dashboard(request):

    membership = Membership.objects.filter(user=request.user).first()


    if not membership:
        return redirect('bloqueio')

    company = membership.company

    # ATUALIZA NOME DA EMPRESA (opcional)
    if request.method == "POST":
        new_name = request.POST.get("name")
        if new_name:
            company.name = new_name
            company.save()

        

     # Dólar (USD/BRL)
    usd = yf.Ticker("USDBRL=X")
    usd_price = usd.history(period="1d")["Close"].iloc[-1]

    # Euro (EUR/BRL)
    eur = yf.Ticker("EURBRL=X")
    eur_price = eur.history(period="1d")["Close"].iloc[-1]

    context = {
        "usd_price": round(usd_price, 2),
        "eur_price": round(eur_price, 2),
    }

     # Dólar (USD/BRL)
    usd = yf.Ticker("USDBRL=X")
    usd_price = usd.history(period="1d")["Close"].iloc[-1]

    # Euro (EUR/BRL)
    eur = yf.Ticker("EURBRL=X")
    eur_price = eur.history(period="1d")["Close"].iloc[-1]

    context = {
        "usd_price": round(usd_price, 2),
        "eur_price": round(eur_price, 2),
    }

    vendas = Venda.objects.filter(company=company).order_by("data")

    # GRÁFICO DE VENDAS - agregar por mês (YYYY-MM)
    month_sums = {}
    for v in vendas:
        key = v.data.strftime("%Y-%m")
        if key not in month_sums:
            month_sums[key] = {"valor": 0.0, "gastos": 0.0}
        month_sums[key]["valor"] += float(v.valor or 0)
        month_sums[key]["gastos"] += float(v.gastos or 0)

    labels = list(month_sums.keys())
    values = [round(month_sums[k]["valor"], 2) for k in labels]
    gastos_values = [round(month_sums[k]["gastos"], 2) for k in labels]

    grafico = {
        "vendas": vendas,
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "gastos": json.dumps(gastos_values),
    }

    return render(request, "core/dashboard.html", {
        "company": company,
        "items": TableItem.objects.filter(company=company),
        "funcionarios": Funcionario.objects.filter(company=company),
        "vendas": Venda.objects.filter(company=company),
        'clientes': Cliente.objects.filter(company=company),
        **context,
        **grafico
        
    })

@login_required
def vendas(request):
    membership = Membership.objects.filter(user=request.user).first()

    company = membership.company

    vendas_qs = NewVenda.objects.filter(company=company)

    # Contagem total de vendas (registros)
    vendas_count = vendas_qs.count()

    # Calcular soma do total vendido em Python para evitar variação entre DBs
    vendas_total = Decimal('0.00')
    for v in vendas_qs:
        try:
            item_total = (v.valor_venda or Decimal('0.00')) * (v.quantidade or 0)
        except Exception:
            item_total = Decimal('0.00')
        # anexa atributo para uso no template
        setattr(v, 'total', item_total)
        vendas_total += item_total


    return render(request, "core/vendas.html", {
        "vendas": vendas_qs,
        "vendas_count": vendas_count,
        "vendas_total": vendas_total,
    })



# -----------------------
# PRODUTOS
# -----------------------

@login_required
def add_item(request):

    if request.method == "POST":

        membership = Membership.objects.filter(user=request.user).first()

        if not membership:
            return redirect('dashboard')

        company = membership.company

        produto = request.POST.get("produto")
        preco = request.POST.get("preco")

        if produto and preco:

            TableItem.objects.create(
                company=company,
                nome=produto,
                preco=preco,
            )

    return redirect('dashboard')


def deletar_item(request, id):
    produto = get_object_or_404(TableItem, id=id)
    produto.delete()
    return redirect('dashboard')


# -----------------------
# FUNCIONÁRIOS
# -----------------------

@login_required
def add_funcionario(request):

    if request.method == "POST":

        membership = Membership.objects.filter(user=request.user).first()
        if not membership:
            return redirect('dashboard')

        company = membership.company

        nome = request.POST.get("nome")
        cargo = request.POST.get("cargo")

        if nome and cargo:  # 👈 EVITA ERRO
            Funcionario.objects.create(
                company=company,
                nome=nome,
                cargo=cargo
            )

    return redirect('dashboard')


def deletar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, id=id)
    funcionario.delete()
    return redirect('dashboard')

# -----------------------
# VENDAS
# -----------------------

@login_required
def add_venda(request):
    if request.method == "POST":
        membership = Membership.objects.filter(user=request.user).first()
        if not membership:
            return redirect('dashboard')

        company = membership.company

        # Se recebeu dados de nova venda (página "vendas")
        produto = request.POST.get('produto')
        if produto:
            quantidade = request.POST.get('quantidade') or 1
            valor_venda = request.POST.get('valor_venda') or 0
            forma_pagamento = request.POST.get('forma_pagamento') or ''
            
            NewVenda.objects.create(
                company=company,
                produto=produto,
                quantidade=quantidade,
                valor_venda=valor_venda,
                forma_pagamento=forma_pagamento
            )
            return redirect("vendas")

# -----------------------
# CLIENTES
# -----------------------
@login_required
def add_cliente(request):

    if request.method == "POST":

        membership = Membership.objects.filter(user=request.user).first()

        if not membership:
            return redirect('dashboard')

        company = membership.company

        nome = request.POST.get("nome")
        contato = request.POST.get("contato")

        if nome and contato:
            Cliente.objects.create(
                company=company,
                nome=nome,
                contato=contato
            )

    return redirect("dashboard")


def deletar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.delete()
    return redirect('dashboard')

# -----------------------
# CONTROLE (ADMIN)
# -----------------------

@login_required
def controle(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    usuarios = User.objects.all()
    usuarios_com_contato = []
    
    for u in usuarios:
        membership = Membership.objects.filter(user=u).first()
        company = membership.company if membership else None
        usuarios_com_contato.append({
            'user': u,
            'company': company
        })

    return render(request, 'core/controle.html', {
        'usuarios_com_contato': usuarios_com_contato
    })


@login_required
def deletar_usuario(request, user_id):

    if not request.user.is_superuser:
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    # Não permitir exclusão de superuser
    if user.is_superuser:
        return redirect('controle')

    if request.method == 'POST':
        user.delete()

    return redirect('controle')


@login_required
def lista_contas(request):
    contas = Membership.objects.all()
    return render(request, "core/lista_contas.html", {"contas": contas})


@login_required
def toggle_conta(request, id):
    conta = get_object_or_404(Membership, id=id)

    # Não permitir desativar/ativar conta de superuser
    if conta.user.is_superuser:
        return redirect("lista_contas")

    conta.is_active = not conta.is_active
    conta.save()

    return redirect("lista_contas")


# -----------------------
# RELATÓRIO MENSAL (IA)     
# -----------------------

@login_required
def relatorio_mensal(request, company_id):
    company = get_object_or_404(
        Company,
        id=company_id
    )
    possui_acesso = Membership.objects.filter(
        user=request.user,
        company=company
    ).exists()

    if not possui_acesso:
        return Response(
            {"erro": "Você não tem acesso a essa empresa"},
            status=403
        )
    vendas = Venda.objects.filter(company=company)
    funcionarios = Funcionario.objects.filter(company=company)
    quantidade_funcionarios = funcionarios.count()
    gastos = Venda.objects.filter(company=company).aggregate(total_gastos=Sum("gastos"))["total_gastos"] or 0

    # Agrupar séries mensais (YYYY-MM) para relatório e gráfico
    month_sums = {}
    for v in vendas.order_by('data'):
        key = v.data.strftime("%Y-%m")
        if key not in month_sums:
            month_sums[key] = {"valor": 0.0, "gastos": 0.0}
        month_sums[key]["valor"] += float(v.valor or 0)
        month_sums[key]["gastos"] += float(v.gastos or 0)

    meses = list(month_sums.keys())
    vendas_series = [round(month_sums[k]["valor"], 2) for k in meses]
    gastos_series = [round(month_sums[k]["gastos"], 2) for k in meses]


    # Pegar o faturamento do mês atual e do mês anterior
    #------------------------------------------------------

    hoje = now().date()
    inicio_mes_atual = hoje.replace(day=1)
    inicio_mes_anterior = (inicio_mes_atual - timedelta(days=1)).replace(day=1)
    fim_mes_anterior = inicio_mes_atual

    faturamento_atual = vendas.filter(
        data__gte=inicio_mes_atual
    ).aggregate(total=Sum("valor"))["total"] or 0

    faturamento_passado = vendas.filter(
        data__gte=inicio_mes_anterior,
        data__lt=fim_mes_anterior
    ).aggregate(total=Sum("valor"))["total"] or 0

    # Gastos do mês atual e mês passado
    gasto_atual = vendas.filter(
        data__gte=inicio_mes_atual
    ).aggregate(total=Sum("gastos"))["total"] or 0

    gasto_passado = vendas.filter(
        data__gte=inicio_mes_anterior,
        data__lt=fim_mes_anterior
    ).aggregate(total=Sum("gastos"))["total"] or 0

    #--------------------------------
    # Ver o crescimento da empresa
    #--------------------------------

    if faturamento_atual > faturamento_passado:
        crescimento = "Positivo"

    elif faturamento_atual < faturamento_passado:
        crescimento = "Negativo"

    else:
        crescimento = "Estável"


    lucro = faturamento_atual - gasto_atual


    relatorio = {
        "faturamento_atual": faturamento_atual,
        "faturamento_passado": faturamento_passado,
        "crescimento": crescimento,
        "quantidade_funcionarios": quantidade_funcionarios,
        "gasto_atual": gasto_atual,
        "gasto_passado": gasto_passado,
        "lucro": lucro,
    }
    
    
    return render(request, "core/relatorio.html", {"company": company, "dados": relatorio})


# -----------------------
#         APIs
# -----------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_relatorio_mensal(request, company_id):

    # Seguraça no acesso da API
    company = get_object_or_404(
        Company,
        id=company_id
    )

    possui_acesso = Membership.objects.filter(
        user=request.user,  
        company=company 
    ).exists()

    if not possui_acesso:
        return Response(
            {"erro": "Você não tem acesso a essa empresa"},
            status=403
        )
    
    # Dados: 

    dados = {
        "nome": "pedro", 
        "idade": 13
    }

    # Falta a URL 

    
    return Response(dados)