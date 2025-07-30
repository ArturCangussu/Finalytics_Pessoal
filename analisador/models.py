from django.db import models
from django.contrib.auth.models import User

# --- NOVO MODEL ---
# Representa um único arquivo de extrato enviado pelo usuário
class Extrato(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    mes_referencia = models.CharField(max_length=50, help_text="Ex: Julho/2025")
    data_upload = models.DateTimeField(auto_now_add=True) # Salva a data do upload automaticamente

    def __str__(self):
        return f"{self.mes_referencia} (Upload por: {self.usuario.username})"

# Este model você já tinha
class Regra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    palavra_chave = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)

    def __str__(self):
        return f"'{self.palavra_chave}' -> '{self.categoria}' (Usuário: {self.usuario.username})"

# --- MODEL ATUALIZADO ---
class Transacao(models.Model):
    # Link para o extrato ao qual esta transação pertence
    extrato = models.ForeignKey(Extrato, on_delete=models.CASCADE, null=True) # ADICIONADO

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.CharField(max_length=20)
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    topico = models.CharField(max_length=50)
    subtopico = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.data} - {self.descricao} - {self.valor}"