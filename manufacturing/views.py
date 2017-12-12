# -*- coding: utf-8 -*-
'''views for manufacturing app'''

import re


#--------------------------------------------------------------------------------------------------


from django.shortcuts import render, get_object_or_404, redirect

from django.http import HttpResponse

from .models import Formula, Machine, Layer, BatcherContent, FormulaContent

from .forms import CreateFormulaForm, ClickToFormulaForm, SearchForm


#--------------------------------------------------------------------------------------------------


# Controller functions

def dict_2_outlay():
    pass

def calculate_outlay(formula):
    '''
    takes a formula (objects) and returns a dictionary where resins (objects) are keys and
    percentages of resin in formula are values.
    This is an initial calculation for outlay to create formula content objects
    '''
    layer_list = [f for f in formula.layer_set.all()]
    resin_list = []
    for layer in layer_list:
        resin_list.extend(list(map(lambda x: (x.resin, 0), layer.batchercontent_set.all())))
    resin_list = list(filter(lambda x: x[0] != None, resin_list))
    layout_dict = dict(resin_list)
    layer_list_with_inc = [f for f in formula.layer_set.all() if f.extruder.incapsulation is True]
    layer_list_wto_inc = [f for f in formula.layer_set.all() if f.extruder.incapsulation is False]
    content_list_wto_inc = []
    for layer in layer_list_wto_inc:
        content_list_wto_inc.extend(list(layer.batchercontent_set.all()))
    content_list_with_inc = []
    for layer in layer_list_with_inc:
        content_list_with_inc.extend(list(layer.batchercontent_set.all()))
    incapsulation = sum(map(lambda x: x.percentage, layer_list_with_inc))
    productivity = formula.productivity
    cof_wto_inc = productivity/(incapsulation+productivity)
    cof_with_inc = incapsulation/(incapsulation+productivity)
    content_list_wto_inc_None = list(
        filter(
            lambda x: x.resin != None and x.percentage != None,
            content_list_wto_inc
        )
    )
    content_perc_wto_inc = list(
        map(
            lambda x: (x.resin, (x.percentage*x.layer.percentage*cof_wto_inc)/100),
            content_list_wto_inc_None
        )
    )
    content_list_with_inc_None = list(
        filter(
            lambda x: x.resin != None and x.percentage != None, content_list_with_inc
        )
    )
    content_perc_with_inc = list(
        map(
            lambda x: (x.resin, x.percentage*cof_with_inc), content_list_with_inc_None
        )
    )
    for resin, perc in content_perc_wto_inc:
        layout_dict[resin] += perc
    for resin, perc in content_perc_with_inc:
        layout_dict[resin] += perc
    layout_dict = dict([(resin, round(perc, 4)) for resin, perc in layout_dict.items()])
    return layout_dict


def calculate_outlay_from_dict(machine, cdd):
    '''
    cdd - cleaned data dictionary that is ussually taken from form
    '''
    pattern = re.compile(r'extruder_(?P<extruder_position>\d+)')
    pattern_b = re.compile(r'extruder_[0-9]__batcher_(?P<batcher_position>\d+)')
    extruder_keys = set(filter(lambda x: 'extruder' in x and 'batcher' not in x, cdd))
    extruder_wo_inc_keys = set()
    extruder_with_inc_keys = set()
    for key in extruder_keys:
        extruder_position = pattern.match(key).group('extruder_position')
        extruder = machine.extruder_set.get(extruder_position=extruder_position)
        extr_tuple = tuple(
            filter(
                lambda x: key in x and 'batcher' in x and 'resin' not in x and cdd[x] != None,
                cdd
            )
        )
        if extruder.incapsulation:
            extruder_with_inc_keys.add((key, extr_tuple))
        else:
            extruder_wo_inc_keys.add((key, extr_tuple))
    incaps = sum(map(lambda x: cdd[x[0]], extruder_with_inc_keys))
    cof_with_inc = incaps/(incaps + cdd['productivity'])
    cof_wo_inc = cdd['productivity']/(incaps + cdd['productivity'])
    bc_with_inc = []
    for key, extr_tuple in extruder_with_inc_keys:
        bc_with_inc.extend(
            map(
                lambda x: (
                    cdd[x+'_resin'],
                    cof_with_inc*cdd[x]*cdd[key]/incaps
                ),
                extr_tuple
            )
        )
    bc_wo_inc = []
    for key, extr_tuple in extruder_wo_inc_keys:
        bc_wo_inc.extend(
            map(
                lambda x: (
                    cdd[x+'_resin'],
                    cof_wo_inc*cdd[x]*cdd[key]/100
                ),
                extr_tuple
            )
        )
    bc_all = bc_wo_inc + bc_with_inc
    resin_perc_dict = {}
    for resin, perc in bc_all:
        if resin in resin_perc_dict:
            resin_perc_dict[resin] += perc
        else:
            resin_perc_dict[resin] = perc
    resin_perc_dict = dict((resin, round(perc, 4)) for resin, perc in resin_perc_dict.items())
    return resin_perc_dict


def get_dict_outlay(formula):
    '''
    Takes formula object, return outlay dictionary.
    This function takes saved outlay from database
    '''
    dict_outlay = dict(map(lambda x: (x.resin, x.percentage), formula.formulacontent_set.all()))
    return dict_outlay


def get_dict_content(formula):
    '''
    Takes formula and returns a dictionary with detail content of formula by extruders and batchers
    '''
    content_dict = {}
    for layer in formula.layer_set.all():
        extruder_str = 'extruder_{}'.format(layer.extruder.extruder_position)
        content_dict[extruder_str] = layer.percentage
        for batchercontent in layer.batchercontent_set.all():
            batcher_str = extruder_str + '__batcher_{}'.format(str(batchercontent.batcher_position))
            batcher_resin_str = batcher_str + '_resin'
            content_dict[batcher_str] = batchercontent.percentage
            content_dict[batcher_resin_str] = batchercontent.resin
    content_dict['productivity'] = formula.productivity
    return content_dict


def validate_extruders(form, machine, extruders_are_valid):
    '''
    Takes form, machine and extruders_are_valid variable (that is defined as True in func that uses
    current func), returns Bool value
    '''
    extr_without_inc_pos = tuple(
        [extr.extruder_position for extr in machine.extruder_set.filter(incapsulation=False)]
    )
    extr_without_inc_keys = tuple(map(lambda x: 'extruder_{}'.format(x), extr_without_inc_pos))
    extruders_are_valid = 99.999 <= \
        sum(map(lambda x: form.cleaned_data[x], extr_without_inc_keys)) <= 100.001
    return extruders_are_valid


def validate_bc(form, bc_are_valid):
    '''
    Validation that percentage sum in extruder equals 100%
    '''
    form_extruder_keys = list(
        filter(
            lambda x: 'extruder' in x and 'batcher' not in x,
            form.cleaned_data.keys()
        )
    )
    bc_keys = [
        tuple(
            filter(
                lambda x: f in x and 'batcher' in x and 'resin' not in x,
                form.cleaned_data.keys()
            )
        ) for f in form_extruder_keys
    ]
    bc_perc_values = tuple([tuple(map(lambda x: form.cleaned_data[x], f)) for f in bc_keys])
    bc_perc_values_validation = tuple(
        [99.999 <= sum(filter(lambda x: x != None, f)) <= 100.001 for f in bc_perc_values]
    )
    if False in bc_perc_values_validation:
        bc_are_valid = False
    return bc_are_valid


def validate_bc_none(form, bc_1_None_validation):
    '''
    Validation "not a pair" values in batchers
    '''
    all_bc_keys = tuple(
        filter(lambda x: 'batcher' in x and 'resin' not in x, form.cleaned_data.keys())
    )
    all_bc_None_count = tuple(
        [(form.cleaned_data[f], form.cleaned_data[f+'_resin']).count(None) for f in all_bc_keys]
    )
    if 1 in all_bc_None_count:
        bc_1_None_validation = False
    return bc_1_None_validation


def validate_name(form, name_validation):
    '''
    Validation formula name repeatance
    '''
    if Formula.objects.filter(formula_name__exact=form.cleaned_data['formula_name']):
        name_validation = False
    return name_validation


def get_content_repeatance(machine, outlay, content_dict):
    '''
    cdd - cleaned data dictionary
    '''
    formulas = tuple(machine.formula_set.all())
    outlays = tuple(map(lambda x: (x, get_dict_outlay(x)), formulas))
    outlays_match = tuple(filter(lambda x: outlay in x, outlays))
    outlays_match_content = tuple(map(lambda x: (x[0], get_dict_content(x[0])), outlays_match))
    outlays_match_content_match = tuple(filter(lambda x: content_dict in x, outlays_match_content))
    print(outlays_match)
    print(outlays_match_content_match)
    return outlays_match_content_match


#--------------------------------------------------------------------------------------------------


# Create your views here.

def login(request):
    return render(request,  'manufacturing/login.html')

def base(request):
    ''' Manufacturing home page veiw'''
    return render(request, 'manufacturing/base.html')


def machine_list(request):
    ''' List of machines view '''
    query_set = Machine.objects.all()
    context = {'query_set':query_set}
    return render(request, 'manufacturing/machine_list.html', context)


def formula_list(request):
    ''' List of formulas view '''
    query_set = set(Formula.objects.all())
    crlick_2_create_form = ClickToFormulaForm(request.POST or None)
    search_form = SearchForm(request.GET or None)
    if crlick_2_create_form.is_valid() and crlick_2_create_form.cleaned_data['machine']:
        machine_id = crlick_2_create_form.cleaned_data['machine'].id
        return redirect('manufacturing:create_formula', machine_id)
    if search_form.is_valid():
        if type(search_form.cleaned_data['search']) is str:
            words_list = search_form.cleaned_data['search'].split()
            for word in words_list:
                search_list = []
                if word.isdigit():
                    search_list.extend(Formula.objects.filter(pk__exact=word))
                search_list.extend(Formula.objects.filter(formula_name__icontains=word))
                search_list.extend(
                    Formula.objects.filter(machine__division__division_name__icontains=word)
                )
                search_list.extend(Formula.objects.filter(machine__machine_name__icontains=word))
                search_list.extend(Formula.objects.filter(
                    machine__extrusion_type__extrusion_type_name__icontains=word
                    ))
                search_list.extend(Formula.objects.filter(structure__structure_name__icontains=word))
                search_list.extend(Formula.objects.filter(description__icontains=word))
                search_list.extend(Formula.objects.filter(formulacontent__resin__resin_name__icontains=word))
                search_set = set(search_list)
                query_set.intersection_update(search_set)
    qty = len(query_set)
    context = {
        'query_set':query_set,
        'qty':qty,
        'crlick_2_create_form':crlick_2_create_form,
        'search_form':search_form
    }
    return render(request, 'manufacturing/formula_list.html', context)


def create_formula(request, machine_id):
    ''' Formula creation view '''
    machine = get_object_or_404(Machine, pk=machine_id)
    form = CreateFormulaForm(request.POST or None, machine=machine)
    form_extruder_keys = list(filter(lambda x: 'extruder' in x and 'batcher' \
        not in x, form.fields.keys()))
    key_list = [(f, tuple(filter(lambda x: f in x and 'batcher' in x and 'resin' \
        not in x, form.fields.keys())),) for f in form_extruder_keys]
    field_list = list(
        map(
            lambda x: (
                form.fields[x[0]].label,
                form[x[0]],
                tuple([(form[f+'_resin'], form[f]) for f in x[1]]),
                int(len(x[1])+1)
            ),
            key_list
        )
    )
    pattern = re.compile(r'extruder_(?P<extruder_position>\d+)')
    pattern_b = re.compile(r'extruder_[0-9]__batcher_(?P<batcher_position>\d+)')
    extruders_are_valid, bc_are_valid, bc_1_None_validation, name_validation = (True,)*4
    repeat_validation_state = True
    content_repeatance_tuple = ()
    if form.is_valid():
        extruders_are_valid = validate_extruders(form, machine, extruders_are_valid)
        bc_are_valid = validate_bc(form, bc_are_valid)
        bc_1_None_validation = validate_bc_none(form, bc_1_None_validation)
        name_validation = validate_name(form, name_validation)
        if extruders_are_valid and bc_are_valid and bc_1_None_validation and name_validation:
            cdd = form.cleaned_data
            outlay = calculate_outlay_from_dict(machine, cdd)
            content = dict(filter(lambda x: 'extruder' in x[0] or 'productiv' in x[0], cdd.items()))
            content_repeatance_tuple = get_content_repeatance(machine, outlay, content)
            if not content_repeatance_tuple or cdd['confirm_repeatance']:
                formula = Formula(
                    formula_name=cdd['formula_name'],
                    machine=machine,
                    structure=cdd['structure'],
                    productivity=cdd['productivity'],
                    description=cdd['description'],
                )
                formula.save()
                for key in form_extruder_keys:
                    extruder_position = pattern.match(key).group('extruder_position')
                    extruder = machine.extruder_set.get(extruder_position=extruder_position)
                    layer = Layer(extruder=extruder, formula=formula, percentage=cdd[key])
                    layer.save()
                    batcher_keys = list(filter(lambda x: 'extruder_{}'.format(extruder_position) \
                        in x and 'batcher' in x and 'resin' not in x, cdd))
                    for b_key in batcher_keys:
                        batcher_position = pattern_b.match(b_key).group('batcher_position')
                        content = BatcherContent(
                            layer=layer,
                            resin=cdd[b_key+'_resin'],
                            batcher_position=batcher_position,
                            percentage=cdd[b_key],
                        )
                        content.save()
                for resin, perc in outlay.items():
                    formula_content = FormulaContent(
                        formula=formula,
                        resin=resin,
                        percentage=perc,
                    )
                    formula_content.save()
                return redirect('manufacturing:formula_list')
    extra_validation = {
        'extruders_are_valid': extruders_are_valid,
        'bc_are_valid': bc_are_valid,
        'bc_1_None_validation': bc_1_None_validation,
        'name_validation': name_validation,
    }
    context = {
        'form': form,
        'machine': machine,
        'field_list': field_list,
        'extra_validation': extra_validation,
        'content_repeatance_tuple':content_repeatance_tuple
    }
    return render(request, 'manufacturing/create_formula.html', context)


def formula_detail(request, formula_id):
    ''' View for detail formula '''
    formula = Formula.objects.get(pk=formula_id)
    layer_set = tuple((layer, layer.extruder.batchers_qty + 1) for layer in formula.layer_set.all())
    context = {'formula':formula, 'layer_set':layer_set}
    return render(request, 'manufacturing/formula_detail.html', context)
