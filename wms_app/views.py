import csv, json

from authlib.integrations.base_client import OAuthError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from .models import Item, TransferItemGroup, ItemGroup, ItemBarcode, Box
from django.db.models import Q, F
from django.http import HttpResponse, Http404, HttpResponseRedirect
from .forms import ItemSearchForm, UploadFileForm, PullForm, PullItemForm, TransferSearchForm, BoxSelectForm, \
    PutAwayForm
from .utilities import read_csv, read_csv_map, read_csv_split
from authlib.integrations.django_client import OAuth
from wms import settings
import logging

OAuth().register(
    name='lightspeed',
    client_id='1230262cdb25bd7485a1780b0c63b701a3d3eccd4598571524e469b7929ebc98',
    client_secret='d936758a5852fbf5788641a29df650065ce2ea38ba19bce670e6672a8e7db776',
    access_token_url='https://cloud.lightspeedapp.com/oauth/access_token.php',
    authorize_url='https://cloud.lightspeedapp.com/oauth/authorize.php',
    api_base_url='https://api.lightspeedapp.com/API/V3/Account',
    redirect_uri='https://nail.network/token',
    client_kwargs={
        'scope': 'employee:inventory_read',
        'token_placement': 'header'
    }
)


class PutAwayView(LoginRequiredMixin, View):
    login_url = 'login'
    put_away_form = PutAwayForm()
    template_name = "put_away.html"

    # box_select_form = BoxSelectForm()
    def get(self, request):
        alert_message = ''
        if request.session.__contains__('alert_message'):
            alert_message += request.session.__getitem__('alert_message')
        if request.GET.__contains__('box_select'):
            box = request.GET.__getitem__('box_select')
            box_object = Box.objects.get_or_create(name=box)
            request.session.__setitem__('box_select', box_object[0].id)
            alert_message = 'Adding to box: ' + box + ' '
        elif request.session.__contains__('box_select'):
            box = request.session.__getitem__('box_select')
            box_object = Box.objects.get_or_create(name=box)
        else:
            alert_message = "Didn't find box "
        context = {
            'put_away_form': self.put_away_form,
            'alert_message': alert_message
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST['scan_box']:
            box = request.session.__getitem__('box_select')
            try:
                box = Box.objects.get(id=box)
            except Box.DoesNotExist:
                alert_message = 'Box not found'
                return HttpResponseRedirect(reverse('items'))
            if request.POST['scan_box'].startswith('2100'):
                try:
                    scanned_item = Item.objects.get(systemID=request.POST['scan_box'])
                except Item.DoesNotExist:
                    request.session.__setitem__('alert_message', 'SystemID Not Found')
                    return HttpResponseRedirect(reverse('put_away'))
            else:
                try:
                    scanned_item = ItemBarcode.objects.get(barcode=request.POST['scan_box']).item
                except ItemBarcode.DoesNotExist:
                    request.session.__setitem__('alert_message', 'Barcode not found')
                    return HttpResponseRedirect(reverse('put_away'))
            try:
                item_group = ItemGroup.objects.get(item=scanned_item, box=box)
            except ItemGroup.DoesNotExist:
                item_group = None
            if not item_group:
                item_group = ItemGroup(
                    item=scanned_item,
                    box=box
                )
            request.session.__setitem__('alert_message', item_group.item.name + ' added to ' + item_group.box.name)
            item_group.quantity += 1
            item_group.save()
        return HttpResponseRedirect(reverse('put_away'))


class ItemView(View):
    login_url = 'login'
    search_form = ItemSearchForm()
    box_select_form = BoxSelectForm()
    template_name = "items.html"

    def get(self, request):
        oauth = OAuth()

        return HttpResponse(oauth.lightspeed.get('item').json())
        if request.session.__contains__('user'):
            if 'search_term' in request.GET:
                search_term = request.GET.__getitem__('search_term')
            else:
                search_term = ''
            if 'has_quantity' in request.GET:
                has_quantity = request.GET.__getitem__('has_quantity')
            else:
                has_quantity = ''
            try:
                item_objects = Item.objects.order_by('name')
            except ObjectDoesNotExist:
                item_objects = None
            if item_objects:
                if search_term:
                    item_objects = item_objects.filter(
                        Q(name__icontains=search_term) | Q(itembarcode__barcode=search_term) | Q(systemID=search_term)
                    )
                if has_quantity:
                    item_objects = item_objects.filter(lightSpeedQuantity__gt=0)
                item_objects = item_objects[:100].prefetch_related()
            context = {
                'item_objects': item_objects,
                'search_form': self.search_form,
                'box_select_form': self.box_select_form
            }
            return render(request, self.template_name, context)
        else:
            return HttpResponseRedirect(reverse('login'))


class TransferView(LoginRequiredMixin, View):
    login_url = 'login'
    search_form = TransferSearchForm()
    start_pull_form = PullForm()
    template_name = 'transfers.html'

    def get(self, request):
        try:
            if 'search_term' in request.GET:
                search_term = request.GET.__getitem__('search_term')
                transfer_objects = TransferItemGroup.objects.order_by('destination', 'priority').filter(
                    Q(item__name__icontains=search_term) | Q(box__boxbarcode__barcode=search_term) | Q(
                        destination=search_term)
                )[:100]
            else:
                transfer_objects = TransferItemGroup.objects.order_by('destination', 'priority')
        except ObjectDoesNotExist:
            transfer_objects = None
        context = {
            'transfer_objects': transfer_objects,
            'search_form': self.search_form,
            'start_pull_form': self.start_pull_form
        }
        return render(request, self.template_name, context)


class PullView(LoginRequiredMixin, View):
    login_url = 'login'
    pull_item_form = PullItemForm()
    template_name = 'pull.html'
    stores = (
        ('1', 'ALP'),
        ('2', 'BH'),
        ('3', 'EC'),
        ('4', 'FOR'),
        ('5', 'MID'),
        ('6', 'PTC'),
        ('7', 'UGA')
    )

    def get(self, request):
        alert_message = ''
        if request.session.__contains__('alert'):
            alert = request.session.__getitem__('alert')
            if alert != '':
                alert_message = alert
                request.session.__setitem__('alert', '')
        if 'store_choice' in request.GET:
            store_choice = request.GET.__getitem__('store_choice')
            request.session.__setitem__('store_choice', store_choice)
            store = self.stores[int(store_choice) - 1][1]
        else:
            store_choice = request.session.__getitem__('store_choice')
            store = self.stores[int(store_choice) - 1][1]
        try:
            transfer_item_group = TransferItemGroup.objects.filter(
                Q(destination__exact=store) & Q(quantity__lt=F('quantityNeeded'))
            )[0]
            try:
                item_group = ItemGroup.objects.filter(
                    Q(item__name=transfer_item_group.item.name)
                )[0]
            except (ObjectDoesNotExist, IndexError) as exception:
                item_group = None
        except ObjectDoesNotExist:
            transfer_item_group = None
        if transfer_item_group:
            request.session.__setitem__('current_transfer_item_group_pk', transfer_item_group.id)
            if item_group:
                request.session.__setitem__('current_item_group_pk', item_group.id)
        context = {
            'pull_item_form': self.pull_item_form,
            'transfer_item_group': transfer_item_group,
            'item_group': item_group,
            'alert_message': alert_message
        }
        return render(request, self.template_name, context)

    def post(self, request):
        store = request.session.__getitem__('store_choice')
        store = self.stores[int(store) - 1][1]
        current_transfer_item_group = request.session.__getitem__('current_transfer_item_group_pk')
        current_item_group = request.session.__getitem__('current_item_group_pk')
        scanned_barcode = request.POST['scan_box']
        # request.POST['scan_box']
        # request.POST['scan_to_box']
        try:
            current_transfer_item_group = TransferItemGroup.objects.get(id=current_transfer_item_group)
        except TransferItemGroup.DoesNotExist:
            request.session.__setitem__('alert', 'failure')
            return HttpResponseRedirect(reverse('pull'))
        try:
            current_item_group = ItemGroup.objects.get(id=current_item_group)
        except ItemGroup.DoesNotExist:
            request.session.__setitem__('alert', 'failure')
            return HttpResponseRedirect(reverse('pull'))
        try:
            scanned_barcode = ItemBarcode.objects.get(barcode=scanned_barcode)
        except ItemBarcode.DoesNotExist:
            scanned_barcode = request.POST['scan_box']
        if current_transfer_item_group and current_item_group and scanned_barcode:
            if (scanned_barcode in current_transfer_item_group.item.itembarcode_set.all()) or (
                    scanned_barcode == current_transfer_item_group.item.systemID):
                current_item_group.quantity -= 1
                current_transfer_item_group.quantity += 1
                current_transfer_box = Box.objects.get_or_create(name=store)
                if current_transfer_box[0]:
                    current_transfer_item_group.box = current_transfer_box[0]
                current_item_group.save()
                current_transfer_item_group.save()
                request.session.__setitem__('alert', 'success')
            else:
                request.session.__setitem__('alert', 'failure')
        return HttpResponseRedirect(reverse('pull'))


@login_required
def upload_data(request):
    if request.method == 'POST':
        file_form = UploadFileForm(request.POST, request.FILES)
        if file_form.is_valid():
            read_csv_split(request.FILES['file_form'])
            return HttpResponseRedirect('transfers/')
    else:
        file_form = UploadFileForm()
    context = {
        'file_form': file_form
    }
    return render(request, 'upload.html', context)


def home(request):
    user = request.session.get('user')
    if user:
        return HttpResponseRedirect(reverse('items'))
    else:
        return HttpResponseRedirect(reverse('login'))


def login(request):
    redirect_uri = request.build_absolute_uri(reverse('token'))
    return oauth.lightspeed.authorize_redirect(request, redirect_uri)


def token(request):
    token = oauth.lightspeed.authorize_access_token(request)
    logger = logging.getLogger(__name__)
    try:
        res = oauth.lightspeed.get('Account.json', token=token)
    except OAuthError as e:
        res = None
    if res and res.ok:
        logger.debug(res)
        request.session['user'] = res.json()
    return HttpResponseRedirect(reverse('items'))


def logout(request):
    request.session.pop('user', None)
    return redirect('/')


# Create your views here.

# Home Page = item table with search options/filter options/paging? Grid.js?
# Expandable cards for location/barcodes/History

# Transfers Home = table of transfers
# Transfer = status of transfer, table with item/location/quantity
# transfer started = Shows current Item/Location/Quantity and textbox for scanning items
# Matching scan shows next item/location/quantity (if no more from that location)
# start/end/send buttons

# Upload Split = Converts split csv formatted files into transfers

# Purchase Orders = table of purchase orders
# Purchase Order = status of PO, table with item/quantityExpected/quantityReceived/Location
# end/start, check in button
"""
def items(request):
    if 'search_term' in request.GET:
        search_term = request.GET.__getitem__('search_term')
        item_objects = Item.objects.order_by('name').filter(
            Q(name__icontains=search_term) | Q(itembarcode__barcode=search_term)
        )[:100]
    else:
        item_objects = Item.objects.order_by('name')[:100]
    search_form = SearchForm()
    context = {
        'item_objects': item_objects,
        'search_form': search_form
    }
    return render(request, 'wms_app/items.html', context)  # items


def pull(request):
    if request.method == 'POST':
        pull_item_form = PullItemForm()
        store = request.session.__getitem__('store_choice')
        # request.POST['scan_box']
        # request.POST['scan_to_box']
        try:
            transfer_item_group = TransferItemGroup.objects.filter(
                Q(destination__exact=store) & ~Q(box=None)
            )[:1]
        except ObjectDoesNotExist:
            transfer_item_group = None
        context = {
            'transfer_objects': transfer_item_group,
            'pull_item_form': pull_item_form
        }
        return render(request, 'wms_app/pull.html', context)
    if 'store_choice' in request.GET:
        stores = (
            ('1', 'ALP'),
            ('2', 'BH'),
            ('3', 'EC'),
            ('4', 'FOR'),
            ('5', 'MID'),
            ('6', 'PTC'),
            ('7', 'UGA')
        )
        store_choice = request.GET.__getitem__('store_choice')
        request.session.__setitem__('store_choice', store_choice)
        store = stores[int(store_choice)][1]
        pull_item_form = PullItemForm()
        try:
            transfer_item_group = TransferItemGroup.objects.filter(
                Q(destination__exact=store) & ~Q(box=None)
            )[:1]
        except ObjectDoesNotExist:
            transfer_item_group = None
        if transfer_item_group:
            try:
                item_found = ItemGroup.objects.filter(
                    Q(item=transfer_item_group[0].item)
                )[:1]
            except ObjectDoesNotExist:
                item_found = None
        else:
            item_found = None
        item_found = item_found[0] if item_found else None
        transfer_item_group = transfer_item_group[0] if transfer_item_group else None
        context = {
            'pull_item_form': pull_item_form,
            'transfer_item_group': transfer_item_group,
            'item_found': item_found
        }
        return render(request, 'wms_app/pull.html', context)


# Per Row Item_Objects
# class based views
# Transfer per box. Print Box Label for Transfer(Preprinted?), Scan until box is full, send
# When scanned item is removed from current itemgroup and placed in new itemgroup in transfer box
# transfer box itemgroups removed when box is sent

def transfers(request):
    if 'search_term' in request.GET:
        search_term = request.GET.__getitem__('search_term')
        try:
            transfer_objects = TransferItemGroup.objects.order_by('destination', 'priority').filter(
                Q(item__name__icontains=search_term) | Q(box__boxbarcode__barcode=search_term) | Q(
                    destination=search_term)
            )
        except ObjectDoesNotExist:
            transfer_objects = None
    else:
        try:
            transfer_objects = TransferItemGroup.objects.order_by('destination', 'priority')
        except ObjectDoesNotExist:
            transfer_objects = None
        search_form = SearchForm()
        pull_form = PullForm()
        context = {
            'transfer_objects': transfer_objects,
            'search_form': search_form,
            'pull_form': pull_form
        }
    return render(request, 'wms_app/transfers.html', context)

"""

# item.name, destination, quantityNeeded from upload
# Create new transferitemgroup for each item.name,destination combo if > 0
# quantity=0(hasnt been pulled), box=null

# button for start pull next to dropdown store selecter
# leads to view with textfield to scan box label into,
# highest priority transferitemgroup for selected store
# transferitemgroup.item.name
# transferitemgroup.item.brand
# transferitemgroup.item.sku
# if transferitemgroup.item.quantityNeeded > item.itemgroup_set[0].quantity
#   item.itemgroup_set[0].quantity
# else
#   transferitemgroup.item.quantityNeeded
# item.itemgroup_set[0].box.name
# item.itemgroup_set[0].box.location.name
# When an item is scanned it will redirect to either next item or same item and decrement quantityNeeded


"""

def item_search(request, search_term):
    return  # search results


def upload_split(request, split_csv):
    return  # confirmation


def transfers(request):
    return HttpResponse(Transfer.objects.all())  # transfer list


def transfer_search(request, search_term):
    return  # search results


def transfer_detail(request, transfer):
    return  # transfer item list, status


def transfer_item_scanned(request, transfer, scan):
    return  # confirmation, table/button updates, Async?


def start_transfer(request, transfer):
    return  # confirmation, table/button updates


def finish_transfer(request, transfer):
    return  # confirmation, table/button updates


def send_transfer(request, transfer):
    return  # confirmation, table/button updates


def purchase_orders(request):
    return HttpResponse(PurchaseOrder.objects.all())  # purchase order list


def purchase_order_search(request, search_term):
    return  # search results


def purchase_order_detail(request, purchase_order):
    return  # purchase order item list, status, textbox for scanning


def purchase_order_scanned(request, purchase_order, scan):
    return  # confirmation, table/button updates, Async?


def check_in_purchase_order(request, purchase_order):
    return  # confirmation table/textbox updates
"""
