from django.db import models
from simple_history.models import HistoricalRecords


# Item (1:N)-> Box(s)
# Item (1:N)-> Location(s)
# Box (1:N)-> Item(s)
# Box (1:1)-> Location
# Location (1:N)-> Item(s)
# Location (1:N)-> Box(s)


class Brand(models.Model):
    name = models.CharField(max_length=100)
    history = HistoricalRecords()


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    history = HistoricalRecords()


class TaxClass(models.Model):
    name = models.CharField(max_length=20)
    history = HistoricalRecords()


class Department(models.Model):
    name = models.CharField(max_length=20)
    history = HistoricalRecords()


class Category(models.Model):
    name = models.CharField(max_length=100)
    history = HistoricalRecords()


# class ItemManager(models.Manager):
#    def get_quantity(self):

# Sum of related itemgroups quantity
class Item(models.Model):
    name = models.CharField(max_length=100)  # 6 direct
    systemID = models.CharField(max_length=12)  # 1 direct
    customSku = models.CharField(max_length=100, null=True)  # 4 direct
    manufactureSku = models.CharField(max_length=100, null=True)  # 5 direct
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)  # 10 foreign
    itemGroups = models.ManyToManyField('Box', through='ItemGroup')
    lightSpeedQuantity = models.SmallIntegerField(null=True)  # 7 direct
    price = models.CharField(max_length=10)  # 8 direct
    publish_to_ecom = models.BooleanField(default=False)  # 11 direct
    default_cost = models.FloatField(default=0)  # 15 direct
    tax = models.BooleanField(default=True)  # 9 convert to boolean from (Yes/No)
    tax_class = models.ForeignKey(TaxClass, null=True, on_delete=models.SET_NULL)  # 15 foreign
    season = models.CharField(max_length=20, null=True)  # 12 direct
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)
    msrp = models.FloatField(default=0)  # 14 direct
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)  # 17 foreign
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)  # 18.19.20.21 foreign
    history = HistoricalRecords()


# A1 B2 C3 D4 E5 F6 G7 H8 I9 J10 K11 L12 M13 N14 O15 P16 Q17 R18 S19 T20 U21

# barcodes are 2 and 3

#    def get_quantity(self):
#        quantity = 0
#        for itemgroup in self.objects('itemGroups').all():
#            quantity += itemgroup.quantity
#        return quantity

class Destination(models.Model):
    name = models.CharField(max_length=100)

    class Type(models.TextChoices):
        STORE = 'STORE'
        NOT_STORE = 'NOT_STORE'

    type = models.CharField(max_length=20, choices=Type.choices, default=Type.STORE)
    history = HistoricalRecords()


class Location(models.Model):
    name = models.CharField(max_length=20)

    class Type(models.TextChoices):
        SHELF = 'SHELF'
        NAVIGATIONAL = 'NAVIGATIONAL'

    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SHELF)
    history = HistoricalRecords()


class Box(models.Model):
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, null=True, on_delete=models.SET_NULL, default=None)
    history = HistoricalRecords()


class ItemGroup(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField(default=0)
    history = HistoricalRecords()


class BoxBarcode(models.Model):
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=20)
    history = HistoricalRecords()


class ItemBarcode(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=20)
    history = HistoricalRecords()


class LocationBarcode(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=20)
    history = HistoricalRecords()


class TransferItemGroup(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    box = models.ForeignKey(Box, null=True, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField(default=0)
    quantityNeeded = models.SmallIntegerField(default=1)
    destination = models.CharField(max_length=100)
    priority = models.SmallIntegerField(default=0)
    reference = models.CharField(max_length=100)
    history = HistoricalRecords()


"""
class Transfer(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED'
        PULL_STARTED = 'PULL_STARTED'
        PULL_FINISHED = 'PULL_FINISHED'
        SENT = 'SENT'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    physical_location = models.ForeignKey(PhysicalLocation, null=True, on_delete=models.SET_NULL)
    from_Location = models.CharField(max_length=20)
    to_location = models.CharField(max_length=20)
    note = models.TextField(max_length=200, null=True)


class TransferItemList(models.Model):
    class Status(models.TextChoices):
        NOT_PULLED = 'NOT_PULLED'
        PULLED = 'PULLED'
        NOT_FOUND = 'NOT_FOUND'

    class Type(models.TextChoices):
        DOWN_STOCK = 'DOWN_STOCK'
        NEW_STOCK = 'NEW_STOCK'
        RESTOCK = 'RESTOCK'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PULLED)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.NEW_STOCK)
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE)
    item = models.ManyToManyField(Item)
    quantity = models.SmallIntegerField(default=0)


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED'
        CHECKING_IN = 'CHECKING_IN'
        CHECKED_IN = 'CHECKED_IN'

    note = models.TextField(max_length=200, null=True)


class PurchaseOrderItemList(models.Model):
    class Status(models.TextChoices):
        SCANNED = 'NOT_SCANNED'
        NOT_CHECKED_IN = 'NOT_CHECKED_IN'
        CHECKED_IN = 'CHECKED_IN'
        NOT_FOUND = 'NOT_FOUND'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCANNED)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    item = models.ManyToManyField(Item)
    quantity_expected = models.SmallIntegerField(default=0)
    quantity_received = models.SmallIntegerField(default=0)
    
"""
