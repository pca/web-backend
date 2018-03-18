from django.forms import ModelForm

from pca.models import PCAProfile


class PCAProfileForm(ModelForm):
    class Meta:
        model = PCAProfile
        fields = ['region', 'city_province']
