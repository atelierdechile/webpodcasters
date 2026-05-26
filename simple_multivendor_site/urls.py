from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core.views import custom_404
from core import views as core_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('location/', include('location.urls')),
    path('', include('core.urls')),
    path("api/", include("botapi.urls")),
    path('analytics/', include('analytics.urls')),
    path('vendor/', include('vendor.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('product/', include('product.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    path("assistant/", include("assistant.urls")),

    #  Ubicación del usuario
    # path("set-location/", core_views.set_location, name="set_location"),
    path("api/set-location-auto/", core_views.set_location_auto, name="set_location_auto"),
    path("api/marketing/", include("marketing.urls")),


    path("vendorapi/", include("vendorapi.urls")),
    path("vendorpos/", include("vendorpos.urls")),


    path("super-admin/", include("superadmin_panel.urls", namespace="superadmin_panel")),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#  Página personalizada de error 404
handler404 = 'core.views.custom_404'

# Permite mostrar la pagina 404 tambien en DEBUG=True
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^.*/$', custom_404),
    ]
