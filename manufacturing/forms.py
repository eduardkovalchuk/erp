# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

from .models import Resin, Structure, Machine


class CreateFormulaForm(forms.Form):
    '''
    Form that collects data for formula
    '''
    formula_name = forms.CharField(max_length=100, label='Назва рецепту')
    structure = forms.ModelChoiceField(label='Структура', queryset=Structure.objects.all())
    productivity = forms.IntegerField(label='Продуктивність')
    description = forms.CharField(label='Коментар', widget=forms.Textarea)
    confirm_repeatance = forms.BooleanField(
        required=False,
        label='Зберегти, незважаючи на те, що рецептура(и) з заданим вмістом вже існує(ють)'
    )

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine')
        extruders = machine.extruder_set.all()
        super(CreateFormulaForm, self).__init__(*args, **kwargs)
        for extruder in extruders:
            extruder_name = extruder.extruder_name
            if extruder.incapsulation:
                extruder_labelname = extruder_name + " , кг/год"
            else:
                extruder_labelname = extruder_name + " , %"
            extruder_str = 'extruder_{}'.format(extruder.extruder_position)
            self.fields[extruder_str] = forms.FloatField(label=extruder_labelname)
            for batcher in range(1, extruder.batchers_qty+1):
                batcher_str = extruder_str + '__batcher_{}'.format(str(batcher))
                batcher_labelname = extruder_name + " - " + str(batcher)+" , %"
                batcher_resin_str = batcher_str + '_resin'
                self.fields[batcher_str] = forms.FloatField(label=batcher_labelname, required=False)
                self.fields[batcher_resin_str] = forms.ModelChoiceField(
                    label='сировина',
                    queryset=Resin.objects.all(),
                    required=False,
                    widget=forms.Select
                )


class ClickToFormulaForm(forms.Form):
    '''
    form for redirection to create_fomula veiw
    '''
    machine = forms.ModelChoiceField(
        label='Cтворити для машини ',
        queryset=Machine.objects.all(),
        widget=forms.Select,
        required=False,
    )


class SearchForm(forms.Form):
    '''
    search form
    '''
    search = forms.CharField(max_length=300, label='Пошук ', required=False)
