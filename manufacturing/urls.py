from django.conf.urls import url

from . import views

app_name = 'manufacturing'
urlpatterns  = [
    url(r'^$', views.base, name='base'),
    url(r'^login$', views.login, name='login'),
    url(r'^(?P<machine_id>[0-9]+)/create_formula/$', views.create_formula, name='create_formula'),
    url(r'^machine_list/$', views.machine_list, name='machine_list'),
    url(r'^formula_list/$', views.formula_list, name='formula_list'),
    url(r'^(?P<formula_id>[0-9]+)/formula_detail/$', views.formula_detail, name='formula_detail'),
]