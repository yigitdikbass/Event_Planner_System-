from django.urls import path
from django.conf import settings
from . import views
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.anasayfa, name='anasayfa'),
    path('login/', views.login, name='login'),
    path('etkinlik/<int:etkinlik_id>/', views.etkinlik_detay, name='etkinlik_detay'),
    path('sohbet/<int:etkinlik_id>/', views.sohbet, name='sohbet'),
    path('profil/', views.kullanici_profili, name='kullanici_profili'),
    path('admin_profili/', views.admin_profili, name='admin_profili'),
    path('uye_ol/', views.uye_ol, name='uye_ol'),  # Üye Ol sayfası için URL tanımı
    path('kullanici_profili/', views.kullanici_profili, name='kullanici_profili'),
    path('kullanici_guncelle/', views.kullanici_guncelle, name='kullanici_guncelle'),
    path('kullanici_duzenle/<int:kullanici_id>/', views.kullanici_duzenle, name='kullanici_duzenle'),
    path('kullanici_sil/<int:kullanici_id>', views.kullanici_sil, name='kullanici_sil'),
    path('sifre_sifirla/<int:kullanici_id>/', views.sifre_sifirla, name='sifre_sifirla'),  # Updated to accept kullanici_id

    path('etkinlik_duzenle/<int:etkinlik_id>', views.etkinlik_duzenle, name='etkinlik_duzenle'),
    path('etkinlik_sil/<int:etkinlik_id>', views.etkinlik_sil, name='etkinlik_sil'),
    path('kullanici_etkinlik_olustur/', views.kullanici_etkinlik_olustur, name='kullanici_etkinlik_olustur'),  # Etkinlik oluşturma URL'si
    path('etkinlige_katil/<int:etkinlik_id>/', views.etkinlige_katil, name='etkinlige_katil'),
    path('etkinlik_onayla/<int:etkinlik_id>/', views.admin_etkinlik_onayla, name='etkinlik_onayla'),
    path('logout/', views.logout, name='logout'),
    path('ilgi_alanli/', views.ilgi_alanli, name='ilgi_alanli'),
    path('sifremi_unuttum/', views.sifremi_unuttum, name='sifremi_unuttum'),
    path('dogrulama/<str:email>/', views.dogrulama, name='dogrulama'),
    path('yeni_sifre/<str:email>/', views.yeni_sifre, name='yeni_sifre'),
    path('etkinlik/<int:event_id>/yol_tarifi/', views.yol_tarifi, name='yol_tarifi'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)