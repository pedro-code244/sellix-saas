from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    contato = models.CharField(max_length=200, blank=True, null=True)

    active = models.BooleanField(default=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # <- isso aqui
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'company')


class TableItem(models.Model):

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    nome = models.CharField(max_length=255)
    preco = models.CharField(max_length=100)

    
    def __str__(self):
        return self.nome


class Funcionario(models.Model):
    nome = models.CharField(max_length=200)
    cargo = models.CharField(max_length=200)

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome
    

class Venda(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    valor = models.DecimalField(max_digits=10, decimal_places=2)
    gastos = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()


class Cliente(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    nome = models.CharField(max_length=200)
    contato = models.CharField(max_length=200)
