# -*- coding: utf-8 -*-

'''Models for manufacturing application'''

from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Division(models.Model):
    register_date = models.DateTimeField(auto_now=True)
    division_name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    
    class Meta:
        verbose_name = "Дільниця"
        verbose_name_plural = "Дільниці"
    
    def __str__(self):
        return self.division_name


class ExtrusionType(models.Model):
    extrusion_type_name = models.CharField(max_length=200, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = "Тип екструзії"
        verbose_name_plural = "Типи екструзії"

    def __str__(self):
        return self.extrusion_type_name


class MaterialType(models.Model):
    material_type_name = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = "Тип матеріалу"
        verbose_name_plural = "Типи матеріалів"

    def __str__(self):
        return self.material_type_name


class Resin(models.Model):
    manufacturer = models.CharField(max_length=200)
    resin_name = models.CharField(max_length=200, unique=True)
    material_type = models.ForeignKey(MaterialType, on_delete=models.CASCADE)
    density = models.FloatField()
    
    class Meta:
        verbose_name = "Полімер"
        verbose_name_plural = "Полімери"

    def __str__(self):
        return self.resin_name


class Machine(models.Model):
    register_date = models.DateTimeField(auto_now=True)
    machine_name = models.CharField(max_length=200, unique=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    extrusion_type = models.ForeignKey(ExtrusionType, on_delete=models.CASCADE)
    incapsulation = models.BooleanField()
    recycling = models.BooleanField()
    description = models.TextField()
    set_in = models.CharField(
        max_length=50, choices=(
            ('mass', 'mass percentage'),
            ('thickness', 'thickness'),
        )
    )
    settable_accuracy = models.FloatField(
        choices=(
            (1, '1'),
            (0.1, '0.1'),
            (0.01, '0.01'),
            (0.001, '0.001'),
        )
    )

    class Meta:
        verbose_name = "Машина"
        verbose_name_plural = "Машини"

    def __str__(self):
        return self.machine_name


class Structure(models.Model):
    register_date = models.DateTimeField(auto_now=True)
    structure_name = models.CharField(
        verbose_name='Структура', 
        max_length=200, 
        unique=True
    )
    
    class Meta:
        verbose_name = "Структура"
        verbose_name_plural = "Структури"

    def __str__(self):
        return self.structure_name


class Extruder(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    extruder_position = models.IntegerField(verbose_name='Extruder position')
    extruder_name = models.CharField(max_length=50, verbose_name='Extruder name')
    batchers_qty = models.IntegerField(verbose_name = 'Quantity of batchers')
    incapsulation = models.BooleanField()
    recycled = models.FloatField()
    inlet_of_recycled = models.FloatField()
    
    class Meta:
        verbose_name = "Екструдер"
        verbose_name_plural = "Екструдери"
    
    def __str__(self):
        return self.extruder_name


class Formula(models.Model):
    register_date = models.DateTimeField(auto_now=True)
    formula_name = models.CharField(max_length=200, unique=True)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    structure = models.ForeignKey(Structure, on_delete=models.PROTECT)
    productivity = models.FloatField()
    description = models.TextField()

    class Meta:
        verbose_name = "Рецептура"
        verbose_name_plural = "Рецептури"

    def __str__(self):
        return self.formula_name


class Layer(models.Model):
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)
    extruder = models.ForeignKey(Extruder, on_delete=models.PROTECT)
    percentage = models.FloatField()
    
    class Meta:
        verbose_name = "Шар"
        verbose_name_plural = "Шари"


class BatcherContent(models.Model):
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    resin = models.ForeignKey(Resin, on_delete=models.PROTECT, null=True)
    batcher_position = models.IntegerField()
    percentage = models.FloatField(null=True)
    
    class Meta:
        verbose_name = "Вміст дозатору"
        verbose_name_plural = "Вмісти дозаторів"

    def __str__(self):
        return str(self.batcher_position)

class FormulaContent(models.Model):
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)
    resin = models.ForeignKey(Resin, on_delete=models.PROTECT)
    percentage = models.FloatField()
