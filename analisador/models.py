from django.db import models
from django.contrib.auth.models import User

#classe pra tabela de regras
class Regra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
#palavra chave
    palavra_chave = models.CharField(max_length=100)
#categoria:
    categoria = models.CharField(max_length=100)

    #ajuda a mostrar um nome legivel no painel de admin

def __str__(self):
        return f"'{self.palavra_chave}' -> '{self.categoria}' (Usuário: {self.usuario.username})"
