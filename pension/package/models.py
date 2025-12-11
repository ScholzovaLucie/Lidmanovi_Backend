from django.db import models



class Package(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    base_nights = models.PositiveIntegerField()
    base_adults = models.PositiveIntegerField()
    base_children = models.PositiveIntegerField(default=0)

    room = models.ForeignKey('pension.Room', on_delete=models.PROTECT, related_name='packages', null=True, blank=True)
    items = models.ManyToManyField('pension.ReservationItem')

    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")

    def __str__(self):
        return self.name
