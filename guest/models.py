from django.db import models

class Guest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    date_of_birth = models.DateField(blank=True, null=True)
    document_number = models.CharField(max_length=100, blank=True)

    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
