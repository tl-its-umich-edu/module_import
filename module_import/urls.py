from django.urls import path
from . import views
from lti_tool.views import jwks, OIDCLoginInitView
from module_import.views import ApplicationLaunchView
from .views import add_module_items, submit_selection

urlpatterns = [
     path('', views.get_home_template, name = 'home'),
     path('error', views.error, name="error" ),

     # LTI launch urls
    path(".well-known/jwks.json", jwks, name="jwks"),
    path("init/<uuid:registration_uuid>/", OIDCLoginInitView.as_view(), name="init"),
    path("ltilaunch", ApplicationLaunchView.as_view(), name="ltilaunch"),
    path('api/add_module_items/', add_module_items, name='add_module_items'),
    path('api/submit_selection/', submit_selection, name='submit_selection'),
]