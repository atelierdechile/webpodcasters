from django.urls import path
from . import views
from core.views import CustomLoginView


app_name = 'core'


urlpatterns = [
    path('', views.frontpage, name="home"),
    path('contact-us/', views.contactpage, name="contact"),
    path('api/countries/<int:pk>/', views.get_country_phone_code, name='get_country_phone_code'),
    path('admin-landing/', views.admin_landing, name='admin_landing'),
    path('login/', CustomLoginView.as_view(), name='login'),
   
    

]
