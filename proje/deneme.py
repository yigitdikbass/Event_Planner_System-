import os
import django
from django.core.mail import send_mail

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proje.settings')
django.setup()

try:
    send_mail(
        'Test Email',
        'This is a test email sent via Django.',
        'gunessenol6128@hotmail.com',  # Gönderen
        ['recipient@example.com'],  # Alıcı
        fail_silently=False,
    )
    print("E-posta başarıyla gönderildi.")
except Exception as e:
    print(f"Hata oluştu: {e}")