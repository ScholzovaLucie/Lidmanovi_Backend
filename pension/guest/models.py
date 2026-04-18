from django.db import models

class Guest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True)

    country = models.CharField(max_length=100, blank=True)

    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('first_name', 'last_name', 'email')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
