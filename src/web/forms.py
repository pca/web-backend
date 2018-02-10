from django.forms import ModelForm

from web.models import PCAProfile


class PCAProfileForm(ModelForm):
    class Meta:
        model = PCAProfile
        fields = ['region', 'city_province']
