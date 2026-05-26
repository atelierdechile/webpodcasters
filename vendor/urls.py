from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .views import profile_view, select_preferences, edit_preferences
from .api import vendors_sales_today

app_name = "vendor"

urlpatterns = [
    # =========================
    # VITRINA / LISTADOS
    # =========================
    path("", views.vendors, name="vendors"),
    path("<int:vendor_id>/", views.vendor, name="vendor"),

    # =========================
    # AUTENTICACIÓN / REGISTRO
    # =========================
    path("become-vendor/", views.register_vendor_view, name="become-vendor"),
    path("become-customer/", views.register_customer_view, name="become-customer"),

    # 🔐 RECUPERAR CONTRASEÑA (OLVIDÉ MI CONTRASEÑA)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset_form.html",
            email_template_name="auth/password_reset_email.html",
            subject_template_name="auth/password_reset_subject.txt",
            success_url="/vendor/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html",
            success_url="/vendor/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # =========================
    # PERFIL / PREFERENCIAS
    # =========================
    path("profile/", profile_view, name="profile"),
    path("select-preferences/", select_preferences, name="select-preferences"),
    path("edit-preferences/", edit_preferences, name="edit-preferences"),

    # =========================
    # PANEL DEL VENDEDOR
    # =========================
    path("dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path("vendor-admin/", views.vendor_admin, name="vendor-admin"),
    path("edit-vendor/", views.edit_vendor, name="edit-vendor"),

    # =========================
    # PRODUCTOS / OFERTAS
    # =========================
    path("add-product/", views.add_product, name="add-product"),
    path("delete-product/<int:pk>/", views.delete_product, name="delete-product"),
    path("product/<int:product_id>/offer/", views.edit_offer, name="edit-offer"),

    # =========================
    # MENÚ SEMANAL
    # =========================
    path("weekly-menu/", views.weekly_menu_edit, name="weekly_menu_edit"),
    path("weekly-menu/assign/", views.weekly_menu_assign, name="weekly_menu_assign"),
    path("weekly-menu/history/", views.weekly_menu_history, name="weekly_menu_history"),
    path("weekly-menu/clear/", views.weekly_menu_clear, name="weekly_menu_clear"),
]
