from django.contrib import admin
from .models import Company, Funcionario, Membership, TableItem, Venda

admin.site.register(Company)
admin.site.register(Membership)
admin.site.register(TableItem)  
admin.site.register(Funcionario)
admin.site.register(Venda)