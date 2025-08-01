from django.db import models

class Kullanici(models.Model):
    kullanici_adi = models.CharField(max_length=30, unique=True)
    sifre = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    konum = models.CharField(max_length=255, blank=True, null=True)
    ilgi_alanlari = models.TextField(blank=True, null=True)
    ad = models.CharField(max_length=30)
    soyad = models.CharField(max_length=30)
    dogum_tarihi = models.DateField(blank=True, null=True)
    cinsiyet = models.CharField(max_length=10, choices=[('Erkek', 'Erkek'), ('Kadın', 'Kadın')], blank=True, null=True)
    telefon_no = models.CharField(max_length=15, blank=True, null=True)
    profil_fotografi = models.ImageField(upload_to='profil_fotografi/', blank=True, null=True)
    is_admin = models.BooleanField(default=False)  # Varsayılan olarak False (0)

    def __str__(self):
        return self.kullanici_adi


class Etkinlik(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField()
    tarih = models.DateField()
    saat = models.TimeField()
    sure = models.IntegerField()  # Süreyi dakika cinsinden saklamak için
    konum = models.CharField(max_length=255)
    kategori = models.CharField(max_length=100)
    onay_durumu = models.CharField(max_length=20, default='pending')  # Onay durumu
    olusturan = models.ForeignKey(Kullanici, null=True, on_delete=models.CASCADE)  # Kullanıcıyı temsil eden alan, null=True eklendi
    def __str__(self):
        return self.ad


class BekleyenEtkinlik(models.Model):
    ad = models.CharField(max_length=100)
    aciklama = models.TextField()
    tarih = models.DateField()
    saat = models.TimeField()
    sure = models.IntegerField()  # Süreyi dakika cinsinden saklamak için
    konum = models.CharField(max_length=200)
    kategori = models.CharField(max_length=100)
    olusturan = models.ForeignKey(Kullanici, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.ad



class Katilimci(models.Model):
    kullanici = models.ForeignKey(Kullanici, on_delete=models.CASCADE)
    etkinlik = models.ForeignKey(Etkinlik, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.kullanici} - {self.etkinlik.ad}"
    
class Mesaj(models.Model):
    etkinlik = models.ForeignKey(Etkinlik, on_delete=models.CASCADE, related_name='mesajlar')  # Etkinlik bağlantısı
    gonderici = models.ForeignKey(Kullanici, related_name='gonderilen_mesajlar', on_delete=models.CASCADE)
    metin = models.TextField()
    gonderim_zamani = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mesaj {self.gonderici} -> {self.etkinlik.ad}"
    
class Puan(models.Model):
    kullanici = models.ForeignKey(Kullanici, on_delete=models.CASCADE)
    puan = models.IntegerField()
    kazanilan_tarih = models.DateField()

    def __str__(self):
        return f"{self.kullanici} - {self.puan}"