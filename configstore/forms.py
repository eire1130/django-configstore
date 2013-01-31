from django import forms
from django.utils import simplejson
from django.contrib.sites.models import Site
from django.core.serializers.json import DjangoJSONEncoder

from configstore.models import Configuration, ConfigurationList


class ConfigurationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.key = kwargs.pop('key')
        super(ConfigurationForm, self).__init__(*args, **kwargs)
        if self.instance:
            initial = self.instance.data
            # model based fields don't know what to due with objects,
            # but they do know what to do with pks
            for key, value in initial.items():
                if hasattr(value, 'pk'):
                    initial[key] = value.pk
            self.initial.update(initial)

    def save(self, commit=True):
        instance = super(ConfigurationForm, self).save(False)
        data = dict(self.cleaned_data)
        del data['site']
        instance.data = data
        instance.key = self.key
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Configuration
        fields = ['site']

class ConfigurationListForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.key = kwargs.pop('key')
        self.group = kwargs.pop('group')
        super(ConfigurationListForm, self).__init__(*args, **kwargs)
        if self.instance:
            initial = self.instance.data
            # model based fields don't know what to due with objects,
            # but they do know what to do with pks
            for key, value in initial.items():
                if hasattr(value, 'pk'):
                    initial[key] = value.pk
            self.initial.update(initial)

    def save(self, commit=True):
        instance = super(ConfigurationListForm, self).save(False)
        data = dict(self.cleaned_data)
        del data['site']
        data['_key'] = self.key
        instance.data = data
        instance.key = self.key
        instance.group = self.group
        if commit:
            instance.save()
        return instance

    class Meta:
        model = ConfigurationList
        fields = ['label', 'site']

