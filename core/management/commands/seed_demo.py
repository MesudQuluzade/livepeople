from django.core.management.base import BaseCommand
from core.models import User, Room
class Command(BaseCommand):
    help='Live People üçün demo otaqlarını və istifadəçiləri yaradır'
    def handle(self,*args,**kwargs):
        for name,description in [('Ümumi','Hamı üçün açıq söhbət'),('Dostluq','Yeni dostlar tap'),('Bakı','Bakıdan olanlar'),('Gəncə','Gəncə icması'),('Digər','Digər mövzular')]: Room.objects.get_or_create(name=name,defaults={'description':description})
        demo=[('nigar','Bakı',24),('elvin','Gəncə',27),('aysel','Sumqayıt',23),('kamran','Bakı',30),('leyla','Şəki',26)]
        for username,city,age in demo:
            User.objects.get_or_create(username=username,defaults={'city':city,'age':age,'is_online':True,'bio':'Səmimi söhbət və yeni tanışlıqlar üçün buradayam.'})
        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
