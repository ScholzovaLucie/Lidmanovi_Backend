from django.db import models

class SaleType(models.TextChoices):
    PERCENTAGE = "percentage", "Percentage"
    FIXED = "fixed", "Fixed amount"

class SaleAppliesTo(models.TextChoices):
    PACKAGE = "package", "Package"
    ORDER = "order", "Order"


class Sale(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    sale_type = models.CharField(max_length=20, choices=SaleType.choices)
    sale_value = models.DecimalField(max_digits=10, decimal_places=2)

    applies_to = models.CharField(max_length=20, choices=SaleAppliesTo.choices)

    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    is_stackable = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(sale_type="percentage") | models.Q(sale_value__lte=100),
                name="percentage_max_100"
            )
        ]