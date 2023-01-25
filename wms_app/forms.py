from django import forms


class ItemSearchForm(forms.Form):
    search_term = forms.CharField(label='Search', max_length=100)
    has_quantity = forms.BooleanField(label='Has Quantity', required=False)


class TransferSearchForm(forms.Form):
    search_term = forms.CharField(label='Search', max_length=100)


class PutAwayForm(forms.Form):
    scan_box = forms.CharField(
        label='Item',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )


class BoxSelectForm(forms.Form):
    box_select = forms.CharField(label='Box', max_length=100)


class UploadFileForm(forms.Form):
    file_form = forms.FileField()


class TransferInputForm(forms.Form):
    input_form = forms.CharField(label='Input', max_length=100)


class PullForm(forms.Form):
    # replace hardcoded store choices with db entry for destination (new destination model?)
    stores = (
        ('1', 'ALP'),
        ('2', 'BH'),
        ('3', 'EC'),
        ('4', 'FOR'),
        ('5', 'MID'),
        ('6', 'PTC'),
        ('7', 'UGA')
    )
    store_choice = forms.ChoiceField(choices=stores)


class PullItemForm(forms.Form):
    scan_box = forms.CharField(label='Scan', max_length=100)
