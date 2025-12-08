from django.db import models

from package.models import Package
from sale.models import Sale


class PackageSale(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("package", "sale")
