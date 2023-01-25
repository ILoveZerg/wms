import csv
from io import StringIO

from django.core.exceptions import ObjectDoesNotExist

from .models import Item, ItemBarcode, Brand, Department, TaxClass, Vendor, Category, ItemGroup, Box, BoxBarcode, \
    TransferItemGroup


def read_csv(file):
    file_reader = StringIO(file.read().decode('utf-8'))
    csv_reader = csv.reader(file_reader, delimiter=',')
    for row in csv_reader:
        if row[0] == 'System ID':
            continue
        brand = Brand.objects.get_or_create(name=row[9])
        print(brand)
        department = ''
        if row[12] != '':
            department = Department.objects.get_or_create(name=row[12])
            print(department)
        tax_class = ''
        if row[14] != '':
            tax_class = TaxClass.objects.get_or_create(name=row[14])
            print(tax_class)
        vendor = Vendor.objects.get_or_create(name=row[16])
        print(vendor)
        category = Category.objects.get_or_create(name=row[17])
        print(category)
        item = Item(
            systemID=row[0],
            customSku=row[3],
            manufactureSku=row[4],
            name=row[5],
            lightSpeedQuantity=row[6] if row[6] != '-' else None,
            price=row[7],
            tax=True if row[8] == 'Yes' else False,
            brand=brand[0],
            publish_to_ecom=True if row[10] == 'Yes' else False,
            season=row[11],
            department=department[0] if department != '' else None,
            msrp=row[13],
            tax_class=tax_class[0] if tax_class != '' else None,
            default_cost=row[15],
            vendor=vendor[0],
            category=category[0],
        )
        item.save()
        print(item)
        if item:
            if row[1] != '':
                item_barcode = ItemBarcode(item=item, barcode=row[1])
                item_barcode.save()
                print(item_barcode)
            if row[2] != '':
                item_barcode = ItemBarcode(item=item, barcode=row[2])
                item_barcode.save()
                print(item_barcode)


def read_csv_map(file):
    file_reader = StringIO(file.read().decode('utf-8'))
    csv_reader = csv.reader(file_reader, delimiter=',')
    for row in csv_reader:
        try:
            item = Item.objects.get(name=row[0])
        except ObjectDoesNotExist:
            item = None
        if item:
            box = Box.objects.get_or_create(name=row[1])
            if box[1]:
                box_barcode = BoxBarcode.objects.get_or_create(box=box[0], barcode=box[0].name)
            item_group = ItemGroup(
                item=item,
                box=box[0],
                quantity=row[3]
            )
            item_group.save()


def read_csv_split(file):
    file_reader = StringIO(file.read().decode('utf-8'))
    csv_reader = csv.reader(file_reader, delimiter=',')
    destination_row = []
    for row in enumerate(csv_reader):
        if not destination_row:
            destination_row = row[1]
        try:
            item = Item.objects.get(name=row[1][0])
        except ObjectDoesNotExist:
            item = None
        if item:
            for rowEntryCount, rowEntry in enumerate(row[1]):
                try:
                    row_entry = int(rowEntry)
                except ValueError:
                    row_entry = None
                if row_entry and row_entry > 0:
                    destination = destination_row[rowEntryCount]
                    print(destination)
                    transfer_item_group = TransferItemGroup(
                        item=item,
                        box=None,
                        destination=destination,
                        quantityNeeded=rowEntry
                    )
                    transfer_item_group.save()


"""
name = models.CharField(max_length=100)  # 6 direct
    systemID = models.CharField(max_length=12)  # 1 direct
customSku = models.CharField(max_length=100, null=True)  # 4 direct
manufactureSku = models.CharField(max_length=100, null=True)  # 5 direct
brand = models.ForeignKey(Brand, on_delete=models.CASCADE)  # 10 foreign
itemGroups = models.ManyToManyField('Box', through='ItemGroup')
lightSpeedQuantity = models.SmallIntegerField(default=0)  # 7 direct
price = models.FloatField()  # 8 direct
tax = models.BooleanField(default=True)  # 9 convert to boolean from (Yes/No)
tax_class = models.ForeignKey(TaxClass, null=True, on_delete=models.SET_NULL)  # 15 foreign
season = models.CharField(max_length=20, null=True)  # 12 direct
department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)
msrp = models.FloatField()  # 14 direct
vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)  # 17 foreign
category = models.CharField(max_length=20)  # 18.19.20.21 foreign
"""

# item objects from lightspeed data
# itemgroup, box, and location objects from map data
# transferitemgroup objects from split data
