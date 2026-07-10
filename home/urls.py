from django.urls import path
from .views import add_funcionario, bloqueio, deletar_funcionario, index, lista_contas, modulos, login_view, cadastro, controle, deletar_usuario, dashboard, politica, add_item, add_venda, deletar_item, relatorio_mensal, add_cliente, deletar_cliente, toggle_conta, sellix, vendas


urlpatterns = [
    path('', index, name='introducao'),
    path('login/', login_view, name='login'),
    path('modulos/', modulos, name='modulos'),
    path('sellix/', sellix, name='sellix'),
    path('cadastro/', cadastro, name='cadastro'),
    path('controle/', controle, name='controle'),
    path('bloqueio/', bloqueio, name='bloqueio'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/add_funcionario/', add_funcionario, name='add_funcionario'),
    path('dashboard/add_venda/', add_venda, name='add_venda'),
    path('dashboard/add_item/', add_item, name='add_item'),
    path('item/delete/<int:id>/', deletar_item, name='deletar_item'),
    path('funcionario/delete/<int:id>/', deletar_funcionario, name='deletar_funcionario'),
    path('dashboard/politica/', politica, name='politica'),
    path('dashboard/add_cliente/', add_cliente, name='add_cliente'),
    path('dashboard/deletar_cliente/<int:id>/', deletar_cliente, name='deletar_cliente'), 
    path('controle/deletar/<int:user_id>/', deletar_usuario, name='deletar_usuario'),
    path('controle/deletar/<int:user_id>/', deletar_usuario, name='deletar_usuario'),
    path("relatorio/<int:company_id>/", relatorio_mensal, name="relatorio_mensal"),
    path('contas/', lista_contas, name='lista_contas'),
    path('contas/toggle/<int:id>/', toggle_conta, name='toggle_conta'),
    path('vendas/', vendas, name='vendas'),
]