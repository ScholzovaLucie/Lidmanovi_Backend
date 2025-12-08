from django.db import models

from package.models import Package


class PackageService(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="services")
    service_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)
    included_in_price = models.BooleanField(default=True)

    class Meta:
        unique_together = ("package", "service_name")
