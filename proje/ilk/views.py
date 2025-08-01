from django.forms import ValidationError
from django.shortcuts import render
from django.urls import reverse
from .models import Etkinlik, Mesaj, Puan
from django.contrib import messages
from django.shortcuts import redirect
from django.db import connection
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.conf import settings
from django.utils.timezone import now
import os
from .models import Kullanici, Etkinlik, Katilimci, BekleyenEtkinlik
from datetime import datetime, timedelta, timezone
from django.core.paginator import Paginator
import random
import string

verification_codes = {}

def anasayfa(request):
    # SQL sorgusu ile etkinlikleri tarih sırasına göre al
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, ad, tarih, saat, aciklama, konum, kategori, sure
            FROM ilk_etkinlik
            ORDER BY tarih
        """)
        etkinlikler = cursor.fetchall()

    # Etkinlikleri bir sözlük listesine dönüştür
    events = []
    for etkinlik in etkinlikler:
        events.append({
            'id': etkinlik[0],
            'ad': etkinlik[1],
            'tarih': etkinlik[2],
            'saat': etkinlik[3],
            'aciklama': etkinlik[4],
            'konum': etkinlik[5],
            'kategori': etkinlik[6],
            'sure' : etkinlik[7],
        })

    context = {
        'events': events,
    }
    return render(request, 'anasayfa.html', context)
def logout(request):
    request.session.flush()  # Tüm oturum verilerini temizler
    return redirect('anasayfa')
def login(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('kullanici_adi')
        sifre = request.POST.get('sifre')

        with connection.cursor() as cursor:
            # Kullanıcı adı ve şifreyi kontrol et
            cursor.execute("SELECT id, is_admin FROM ilk_kullanici WHERE kullanici_adi = %s AND sifre = %s", [kullanici_adi, sifre])
            result = cursor.fetchone()
            if result:
                user_id, is_admin = result
                request.session['kullanici_id'] = user_id  # Oturum bilgisini ayarla

                # `next` parametresini kontrol et
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)  # Eğer `next` varsa o URL'ye yönlendir

                # Admin kontrolü
                if is_admin == 1:
                    return redirect('admin_profili')  # Admin profiline yönlendir
                else:
                    return redirect('kullanici_profili')  # Kullanıcı profiline yönlendir
            else:
                messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
                return render(request, 'login.html')
    else:
        return render(request, 'login.html')
    
def uye_ol(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('kullanici_adi')
        sifre = request.POST.get('sifre')
        email = request.POST.get('email')
        adi = request.POST.get('adi')
        soyadi = request.POST.get('soyadi')
        konum = request.POST.get('konum', '')  # Opsiyonel alan
        ilgi_alanlari = request.POST.get('ilgi_alanlari', '')  # Opsiyonel alan
        dogum_tarihi = request.POST.get('dogum_tarihi', None)  # Opsiyonel alan
        cinsiyet = request.POST.get('cinsiyet', None)  # Opsiyonel alan
        telefon_numarasi = request.POST.get('telefon_no', '')  # Opsiyonel alan

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO ilk_kullanici (kullanici_adi, sifre, email, "
                    "konum,ilgi_alanlari ,ad ,soyad , dogum_tarihi, cinsiyet, telefon_no,is_admin) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [kullanici_adi, sifre, email,konum,ilgi_alanlari,adi , soyadi , dogum_tarihi, cinsiyet, telefon_numarasi,0]
                )
            messages.success(request, 'Kullanıcı başarıyla kaydedildi.')
            return redirect('login')  # Kayıt sonrası giriş sayfasına yönlendirme
        except IntegrityError:
            messages.error(request, 'Bu kullanıcı adı zaten alınmış.')
        except Exception as e:
            messages.error(request, f'Kayıt sırasında bir hata oluştu: {str(e)}')
    return render(request, 'uye_ol.html')
def kullanici_profili(request):
    kullanici_id = request.session.get('kullanici_id')
    if not kullanici_id:
        messages.error(request, 'Lütfen giriş yapın.')
        return redirect('login')  # Kullanıcı giriş yapmamışsa login sayfasına yönlendir

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kullanici_adi, email, ad, soyad, konum, ilgi_alanlari, 
                   dogum_tarihi, cinsiyet, telefon_no, profil_fotografi 
            FROM ilk_kullanici 
            WHERE id = %s
        """, [kullanici_id])
        kullanici = cursor.fetchone()

    if not kullanici:
        messages.error(request, 'Kullanıcı bilgileri bulunamadı.')
        return redirect('login')

    # Profil fotoğrafı URL'sini oluştur
    profil_fotografi_url = None
    if kullanici[9]:  # profil_fotografi alanı
        profil_fotografi_url = settings.MEDIA_URL + kullanici[9]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT e.id, e.ad, e.tarih, e.saat 
            FROM ilk_katilimci k
            JOIN ilk_etkinlik e ON k.etkinlik_id = e.id
            WHERE k.kullanici_id = %s
        """, [kullanici_id])
        katildigi_etkinlikler = cursor.fetchall()
    # Kullanıcının toplam puanını hesapla
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT SUM(puan) 
            FROM ilk_puan 
            WHERE kullanici_id = %s
        """, [kullanici_id])
        toplam_puan = cursor.fetchone()[0] or 0
    context = {
        'kullanici_id': kullanici_id,
        'kullanici_adi': kullanici[0],
        'email': kullanici[1],
        'ad': kullanici[2],
        'soyad': kullanici[3],
        'konum': kullanici[4],
        'ilgi_alanlari': kullanici[5],
        'dogum_tarihi': kullanici[6],
        'cinsiyet': kullanici[7],
        'telefon_no': kullanici[8],
        'profil_fotografi_url': profil_fotografi_url,
        'katildigi_etkinlikler': katildigi_etkinlikler,
        'toplam_puan': toplam_puan,  
    }

    return render(request, 'kullanici_profili.html', context)
def admin_profili(request):
    # Kullanıcı oturum kontrolü
    kullanici_id = request.session.get('kullanici_id')
    if not kullanici_id:
        messages.error(request, 'Lütfen giriş yapın.')
        return redirect('login')

    # Kullanıcının admin olup olmadığını kontrol et
    try:
        admin_kullanici = Kullanici.objects.get(id=kullanici_id)
        if not admin_kullanici.is_admin:
            messages.error(request, 'Bu sayfaya erişim izniniz yok.')
            return redirect('anasayfa')
    except Kullanici.DoesNotExist:
        messages.error(request, 'Geçerli bir kullanıcı bulunamadı.')
        return redirect('login')

    # Tüm kullanıcıları id'ye göre sıralayıp sayfalandır
    kullanicilar_listesi = Kullanici.objects.all().order_by('id')
    paginator_kullanici = Paginator(kullanicilar_listesi, 10)  # Sayfa başına 10 kullanıcı
    sayfa_kullanici = request.GET.get('sayfa')
    kullanicilar = paginator_kullanici.get_page(sayfa_kullanici)

    # Bekleyen etkinlikleri al
    bekleyen_etkinlikler = BekleyenEtkinlik.objects.all()

    etkinlikler_listesi = Etkinlik.objects.prefetch_related('katilimci_set__kullanici').order_by('id')
    paginator_etkinlik = Paginator(etkinlikler_listesi, 100)
    sayfa_etkinlik = request.GET.get('sayfa_etkinlik')
    etkinlikler = paginator_etkinlik.get_page(sayfa_etkinlik)
    toplam_kullanicilar = Kullanici.objects.count()
    toplam_etkinlikler = Etkinlik.objects.count()
    context = {
        'toplam_kullanicilar': toplam_kullanicilar,
        'toplam_etkinlikler': toplam_etkinlikler,
        'kullanicilar': kullanicilar,
        'bekleyen_etkinlikler': bekleyen_etkinlikler,
        'etkinlikler': etkinlikler,
    }

    return render(request, 'admin_profili.html', context)
def kullanici_guncelle(request):
    kullanici_id = request.session.get('kullanici_id')
    if not kullanici_id:
        messages.error(request, 'Lütfen giriş yapın.')
        return redirect('login')

    if request.method == 'POST':
        # Formdan gelen verileri al
        email = request.POST.get('email')
        ad = request.POST.get('ad')
        soyad = request.POST.get('soyad')
        konum = request.POST.get('konum', '')
        ilgi_alanlari = request.POST.get('ilgi_alanlari', '')
        dogum_tarihi = request.POST.get('dogum_tarihi', None)
        cinsiyet = request.POST.get('cinsiyet', None)
        telefon_no = request.POST.get('telefon_no', '')

        # Profil fotoğrafını al
        profil_fotografi = request.FILES.get('profil_fotografi')

        # Veritabanını güncelle
        with connection.cursor() as cursor:
            if profil_fotografi:
                # Eski profil fotoğrafını sil
                cursor.execute("SELECT profil_fotografi FROM ilk_kullanici WHERE id = %s", [kullanici_id])
                eski_fotograf = cursor.fetchone()[0]
                if eski_fotograf:
                    eski_fotograf_path = os.path.join(settings.MEDIA_ROOT, eski_fotograf)
                    if os.path.exists(eski_fotograf_path):
                        os.remove(eski_fotograf_path)

                # Yeni profil fotoğrafını kaydet
                profil_fotografi_path = os.path.join('profil_fotografi', profil_fotografi.name)
                with open(os.path.join(settings.MEDIA_ROOT, profil_fotografi_path), 'wb+') as destination:
                    for chunk in profil_fotografi.chunks():
                        destination.write(chunk)

                cursor.execute("""
                    UPDATE ilk_kullanici
                    SET email = %s, ad = %s, soyad = %s, konum = %s, ilgi_alanlari = %s,
                        dogum_tarihi = %s, cinsiyet = %s, telefon_no = %s, profil_fotografi = %s
                    WHERE id = %s
                """, [email, ad, soyad, konum, ilgi_alanlari, dogum_tarihi, cinsiyet, telefon_no, profil_fotografi_path, kullanici_id])
            else:
                cursor.execute("""
                    UPDATE ilk_kullanici
                    SET email = %s, ad = %s, soyad = %s, konum = %s, ilgi_alanlari = %s,
                        dogum_tarihi = %s, cinsiyet = %s, telefon_no = %s
                    WHERE id = %s
                """, [email, ad, soyad, konum, ilgi_alanlari, dogum_tarihi, cinsiyet, telefon_no, kullanici_id])

        messages.success(request, 'Bilgileriniz başarıyla güncellendi.')
        return redirect('kullanici_profili')

    # GET isteği için mevcut kullanıcı bilgilerini al
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT email, ad, soyad, konum, ilgi_alanlari, dogum_tarihi, cinsiyet, telefon_no, profil_fotografi
            FROM ilk_kullanici
            WHERE id = %s
        """, [kullanici_id])
        kullanici = cursor.fetchone()

    if not kullanici:
        messages.error(request, 'Kullanıcı bilgileri bulunamadı.')
        return redirect('login')

    context = {
        'email': kullanici[0],
        'ad': kullanici[1],
        'soyad': kullanici[2],
        'konum': kullanici[3],
        'ilgi_alanlari': kullanici[4],
        'dogum_tarihi': kullanici[5],
        'cinsiyet': kullanici[6],
        'telefon_no': kullanici[7],
        'profil_fotografi': kullanici[8],
    }

    return render(request, 'kullanici_guncelle.html', context)
def sifre_sifirla(request, kullanici_id):
    # Kullanıcıyı al
    kullanici = get_object_or_404(Kullanici, id=kullanici_id)

    if request.method == 'POST':
        yeni_sifre = request.POST.get('yeni_sifre')
        yeni_sifre_onay = request.POST.get('yeni_sifre_onay')

        # Şifrelerin eşleşip eşleşmediğini kontrol edin
        if yeni_sifre != yeni_sifre_onay:
            messages.error(request, 'Şifreler eşleşmiyor!')
            return render(request, 'sifre_sifirla.html', {'kullanici_id': kullanici_id})

        # Şifre uzunluğunu kontrol edin
        if len(yeni_sifre) < 8:
            messages.error(request, 'Şifre en az 8 karakter uzunluğunda olmalıdır.')
            return render(request, 'sifre_sifirla.html', {'kullanici_id': kullanici_id})

        # Şifreyi hashleyip kaydedin
        kullanici.sifre = make_password(yeni_sifre)
        kullanici.save()

        messages.success(request, 'Şifreniz başarıyla sıfırlandı!')
        return redirect('login')  # Şifre sıfırlandıktan sonra giriş sayfasına yönlendirme

    return render(request, 'sifre_sifirla.html', {'kullanici_id': kullanici_id})
def etkinlik_detay(request, etkinlik_id):
    etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id)
    mesajlar = Mesaj.objects.filter(etkinlik=etkinlik).order_by('gonderim_zamani')

    if request.method == 'POST':
        metin = request.POST.get('mesaj')
        kullanici_id = request.session.get('kullanici_id')
        if kullanici_id:
            kullanici = get_object_or_404(Kullanici, id=kullanici_id)
            Mesaj.objects.create(etkinlik=etkinlik, gonderici=kullanici, metin=metin)
            return redirect('etkinlik_detay', etkinlik_id=etkinlik.id)
        else:
            messages.error(request, 'Mesaj göndermek için giriş yapmanız gerekiyor.')

    return render(request, 'etkinlik_detay.html', {
        'etkinlik': etkinlik,
        'mesajlar': mesajlar,
    })

def sohbet(request, etkinlik_id):
    etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id)

    # Kullanıcının giriş yapıp yapmadığını kontrol edin
    kullanici_id = request.session.get('kullanici_id')
    if not kullanici_id:
        return redirect(f"{reverse('login')}?next=/sohbet/{etkinlik_id}/")

    # Kullanıcı oturumu varsa devam edin
    gonderici = get_object_or_404(Kullanici, id=kullanici_id)
    mesajlar = Mesaj.objects.filter(etkinlik=etkinlik).order_by('gonderim_zamani')

    # Mesaj gönderme işlemi
    if request.method == 'POST':
        metin = request.POST.get('mesaj')
        if metin:
            Mesaj.objects.create(
                etkinlik=etkinlik,
                gonderici=gonderici,
                metin=metin,
                gonderim_zamani=now()  # Doğru fonksiyon burada kullanılıyor
            )
            return redirect('sohbet', etkinlik_id=etkinlik_id)

    context = {
        'etkinlik': etkinlik,
        'mesajlar': mesajlar,
    }
    return render(request, 'sohbet.html', context)

def kullanici_duzenle(request, kullanici_id):
    kullanici = get_object_or_404(Kullanici, id=kullanici_id)

    if request.method == 'POST':
        # Formdan gelen verileri al
        kullanici.kullanici_adi = request.POST.get('kullanici_adi')
        kullanici.email = request.POST.get('email')
        kullanici.ad = request.POST.get('ad')
        kullanici.soyad = request.POST.get('soyad')
        kullanici.konum = request.POST.get('konum')
        kullanici.ilgi_alanlari = request.POST.get('ilgi_alanlari')
        kullanici.dogum_tarihi = request.POST.get('dogum_tarihi')
        kullanici.cinsiyet = request.POST.get('cinsiyet')
        kullanici.telefon_no = request.POST.get('telefon_no')
        
        # Kullanıcıyı güncelle
        kullanici.save()
        messages.success(request, 'Kullanıcı bilgileri başarıyla güncellendi.')
        return redirect('admin_profili')  # Admin profil sayfasına yönlendir

    # Kullanıcının katıldığı etkinlikleri al
    katildigi_etkinlikler = Katilimci.objects.filter(kullanici=kullanici).select_related('etkinlik')

    context = {
        'kullanici': kullanici,
        'katildigi_etkinlikler': katildigi_etkinlikler,
    }

    return render(request, 'kullanici_duzenle.html', context)

def kullanici_sil(request, kullanici_id):
    kullanici = get_object_or_404(Kullanici, id=kullanici_id)

    if request.method == 'POST':
        # Kullanıcıyı sil
        kullanici.delete()
        messages.success(request, 'Kullanıcı başarıyla silindi.')
        return redirect('admin_profili')  # Admin profil sayfasına yönlendir

    context = {
        'kullanici': kullanici,
    }

    return render(request, 'kullanici_sil.html', context)

def etkinlik_duzenle(request, etkinlik_id):
    etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id)
    katilimcilar = Katilimci.objects.filter(etkinlik=etkinlik).select_related('kullanici')

    if request.method == 'POST':
        # Formdan gelen verileri al
        etkinlik.ad = request.POST.get('ad')
        etkinlik.tarih = request.POST.get('tarih')
        etkinlik.saat = request.POST.get('saat')
        
        # Etkinliği güncelle
        etkinlik.save()
        messages.success(request, 'Etkinlik başarıyla güncellendi.')
        return redirect('admin_profili')  # Admin profil sayfasına yönlendir

    context = {
        'etkinlik': etkinlik,
        'katilimcilar': katilimcilar,

    }

    return render(request, 'etkinlik_duzenle.html', context)

def etkinlik_sil(request, etkinlik_id):
    etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id)

    if request.method == 'POST':
        # Etkinliği sil
        etkinlik.delete()
        messages.success(request, 'Etkinlik başarıyla silindi.')
        return redirect('admin_profili')  # Admin profil sayfasına yönlendir

    context = {
        'etkinlik': etkinlik,
    }

    return render(request, 'etkinlik_sil.html', context)

def kullanici_etkinlik_olustur(request):
    if request.method == 'POST':
        # Oturum kontrolü (session üzerinden)
        kullanici_id = request.session.get('kullanici_id')
        if not kullanici_id:
            messages.error(request, 'Bu işlemi gerçekleştirmek için giriş yapmalısınız.')
            return redirect('login')  # Giriş sayfasına yönlendirme
        
        # Kullanıcının geçerli bir kullanıcı olup olmadığını kontrol et
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM ilk_kullanici WHERE id = %s", [kullanici_id])
            kullanici = cursor.fetchone()

        if not kullanici:
            messages.error(request, 'Geçersiz kullanıcı. Lütfen tekrar giriş yapın.')
            return redirect('login')

        # Etkinlik bilgilerini al
        ad = request.POST.get('ad')
        aciklama = request.POST.get('aciklama')
        tarih = request.POST.get('tarih')
        saat = request.POST.get('saat')
        sure = request.POST.get('sure')  # Kullanıcıdan gelen süre (dakika olarak)

        try:
            # Süreyi dakika olarak saklayın
            sure = int(sure)
        except ValueError:
            messages.error(request, 'Süre geçerli bir sayı olmalıdır.')
            return render(request, 'kullanici_etkinlik_olustur.html')

        konum = request.POST.get('konum')
        kategori = request.POST.get('kategori')

        # Bekleyen etkinliği kaydet
        bekleyen_etkinlik = BekleyenEtkinlik(
            ad=ad,
            aciklama=aciklama,
            tarih=tarih,
            saat=saat,
            sure=sure,  # Süre dakika olarak saklanır
            konum=konum,
            kategori=kategori,
            olusturan_id=kullanici_id
        )
        bekleyen_etkinlik.save()
        Puan.objects.create(kullanici_id=kullanici_id, puan=15, kazanilan_tarih=tarih)
        messages.success(request, 'Etkinliğiniz admin onayına gönderildi.')
        return redirect('kullanici_profili')  # Kullanıcı profil sayfasına yönlendirme

    return render(request, 'kullanici_etkinlik_olustur.html')

def etkinlige_katil(request, etkinlik_id):
    # Kullanıcının giriş yapıp yapmadığını kontrol edin
    
    kullanici_id = request.session.get('kullanici_id')
    if not kullanici_id:
        messages.error(request, 'Bu işlemi gerçekleştirmek için giriş yapmalısınız.')
        return redirect('login')  # Giriş sayfasına yönlendirme

    try:
        # Katılmak istenen etkinliği al
        etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id)
        # Kullanıcının katıldığı etkinlikleri kontrol et
        katildigi_etkinlikler = Katilimci.objects.filter(kullanici_id=kullanici_id).select_related('etkinlik')

        # Etkinlik tarih ve saat kontrolü
        etkinlik_baslangic = datetime.combine(etkinlik.tarih, etkinlik.saat)
        etkinlik_bitis = etkinlik_baslangic + timedelta(minutes=etkinlik.sure)

        for katilim in katildigi_etkinlikler:
            mevcut_etkinlik = katilim.etkinlik
            mevcut_baslangic = datetime.combine(mevcut_etkinlik.tarih, mevcut_etkinlik.saat)
            mevcut_bitis = mevcut_baslangic + timedelta(minutes=mevcut_etkinlik.sure)

            # Çakışma kontrolü
            if (etkinlik_baslangic < mevcut_bitis and etkinlik_bitis > mevcut_baslangic):
                messages.error(request, f"Bu etkinlik '{mevcut_etkinlik.ad}' ile çakışıyor.")
                return redirect('kullanici_profili')

        # Çakışma yoksa katılım kaydını oluştur
        Katilimci.objects.create(kullanici_id=kullanici_id, etkinlik=etkinlik)
        Puan.objects.create(kullanici_id=kullanici_id, puan=10, kazanilan_tarih=etkinlik.tarih)
        messages.success(request, 'Etkinliğe başarıyla katıldınız!')
        return redirect('kullanici_profili')

    except Exception as e:
        messages.error(request, f"Etkinliğe katılım sırasında bir hata oluştu: {e}")
        return redirect('kullanici_profili')


def admin_etkinlik_onayla(request, etkinlik_id):
    # Kullanıcının admin olup olmadığını kontrol et
    if not request.session.get('kullanici_id'):
        messages.error(request, 'Bu işlemi gerçekleştirmek için giriş yapmalısınız.')
        return redirect('login')

    # Bekleyen etkinliği al
    bekleyen_etkinlik = get_object_or_404(BekleyenEtkinlik, id=etkinlik_id)

    try:
        # `sure` değerini dakika cinsinden al ve timedelta'ya çevir
         # `sure` değerini dakika olarak al
        if isinstance(bekleyen_etkinlik.sure, timedelta):
            sure_dakika = int(bekleyen_etkinlik.sure.total_seconds() // 60)
        else:
            sure_dakika = int(bekleyen_etkinlik.sure)
        # Bekleyen etkinliği onayla ve Etkinlik tablosuna kaydet
        Etkinlik.objects.create(
            ad=bekleyen_etkinlik.ad,
            aciklama=bekleyen_etkinlik.aciklama,
            tarih=bekleyen_etkinlik.tarih,
            saat=bekleyen_etkinlik.saat,
            sure=sure_dakika,  # `DurationField` formatına uygun olarak timedelta kullanılıyor
            konum=bekleyen_etkinlik.konum,
            kategori=bekleyen_etkinlik.kategori,
            olusturan=bekleyen_etkinlik.olusturan,
            onay_durumu='approved',  # Onaylanmış olarak işaretle
        )

        # Bekleyen etkinliği sil
        bekleyen_etkinlik.delete()

        messages.success(request, 'Etkinlik başarıyla onaylandı.')
    except Exception as e:
        messages.error(request, f"Etkinlik onaylanırken bir hata oluştu: {e}")

    return redirect('admin_profili')


def ilgi_alanli(request):
    # Kullanıcı giriş yapmış mı kontrol edin
    kullanici_id = request.session.get('kullanici_id')
    if not kullanici_id:
        messages.error(request, 'Lütfen giriş yapın.')
        return redirect('login')

    # Kullanıcının ilgi alanlarını alın
    with connection.cursor() as cursor:
        cursor.execute("SELECT ilgi_alanlari FROM ilk_kullanici WHERE id = %s", [kullanici_id])
        user_interests = cursor.fetchone()
    
    if not user_interests or not user_interests[0]:
        messages.error(request, 'İlgi alanlarınız bulunamadı. Lütfen profil bilgilerinizi güncelleyin.')
        return redirect('kullanici_profili')

    user_interests = user_interests[0].split(', ')  # İlgi alanlarını listeye dönüştürün

    # Tüm etkinliklerin bilgilerini alın
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, ad, kategori, tarih, saat, aciklama, konum, sure
            FROM ilk_etkinlik
        """)
        etkinlikler = cursor.fetchall()

    # Etkinlikler ile kullanıcının ilgi alanlarını eşleştirip uyumluluk oranını hesaplayın
    etkinlik_listesi = []
    for etkinlik in etkinlikler:
        etkinlik_id, etkinlik_ad, etkinlik_kategori, etkinlik_tarih, etkinlik_saat, etkinlik_aciklama, etkinlik_konum, etkinlik_sure = etkinlik
        etkinlik_kategorileri = etkinlik_kategori.split(', ')

        # İlgi alanları ile kategoriler arasındaki kesişimi bulun
        ortak_ilgiler = set(user_interests) & set(etkinlik_kategorileri)
        uyumluluk_orani = (len(ortak_ilgiler) / len(user_interests)) * 100 if user_interests else 0

        etkinlik_listesi.append({
            'id': etkinlik_id,
            'ad': etkinlik_ad,
            'kategori': etkinlik_kategori,
            'tarih': etkinlik_tarih,
            'saat': etkinlik_saat,
            'aciklama': etkinlik_aciklama,
            'konum': etkinlik_konum,
            'sure': etkinlik_sure,
            'uyumluluk_orani': uyumluluk_orani,
        })

    # Uyumluluk oranına göre sıralayın
    etkinlik_listesi = sorted(etkinlik_listesi, key=lambda x: x['uyumluluk_orani'], reverse=True)

    context = {
        'etkinlik_listesi': etkinlik_listesi,
    }

    return render(request, 'ilgi_alanli.html', context)

def sifremi_unuttum(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            kullanici = Kullanici.objects.get(email=email)
            # Rastgele doğrulama kodu oluştur
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            verification_codes[email] = verification_code  # Kodları sakla

            # Doğrulama kodunu mesajlarla göster
            messages.success(request, f"Doğrulama kodunuz: {verification_code}")
            return redirect('dogrulama', email=email)
        except Kullanici.DoesNotExist:
            messages.error(request, "Bu e-posta adresine kayıtlı bir kullanıcı bulunamadı.")
    return render(request, 'sifremi_unuttum.html')

def dogrulama(request, email):
    if request.method == 'POST':
        entered_code = request.POST.get('verification_code')
        if email in verification_codes and verification_codes[email] == entered_code:
            del verification_codes[email]  # Kod doğruysa sil
            return redirect('yeni_sifre', email=email)
        else:
            messages.error(request, "Doğrulama kodu yanlış.")
    return render(request, 'dogrulama.html', {'email': email})

def yeni_sifre(request, email):
    if request.method == 'POST':
        yeni_sifre = request.POST.get('yeni_sifre')
        sifre_tekrar = request.POST.get('sifre_tekrar')
        if yeni_sifre == sifre_tekrar:
            try:
                kullanici = Kullanici.objects.get(email=email)
                kullanici.sifre = yeni_sifre  # Hash ile şifrelemek daha güvenlidir
                kullanici.save()
                messages.success(request, "Şifreniz başarıyla güncellendi.")
                return redirect('login')
            except Kullanici.DoesNotExist:
                messages.error(request, "Kullanıcı bulunamadı.")
        else:
            messages.error(request, "Şifreler eşleşmiyor.")
    return render(request, 'yeni_sifre.html', {'email': email})

def yol_tarifi(request, event_id):
    # Kullanıcı ID'sini session'dan al
    kullanici_id = request.session.get('kullanici_id')

    if kullanici_id is None:
        # Eğer kullanıcı giriş yapmamışsa login sayfasına yönlendir
        return redirect(f"{reverse('login')}?next={request.path}")

    # Kullanıcının bilgilerini al
    user = get_object_or_404(Kullanici, id=kullanici_id)

    # Etkinlik bilgilerini al
    event = get_object_or_404(Etkinlik, id=event_id)

    # Kullanıcı ve etkinlik konum bilgisi kontrolü
    user_konum = user.konum  # Kullanıcının modeldeki konum bilgisi
    if not user_konum or not event.konum:
        messages.error(request, 'Başlangıç veya bitiş konumu eksik.')
        return redirect('anasayfa')

    # Kullanıcı giriş yaptıysa yol tarifi sayfasını render et
    return render(request, 'yol_tarifi.html', {
        'user_konum': user_konum,
        'event_konum': event.konum,
        'event': event
    })


