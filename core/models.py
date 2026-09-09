from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
class User(AbstractUser):
    age=models.PositiveSmallIntegerField(default=25); city=models.CharField(max_length=80,default='Bakı'); bio=models.TextField(blank=True,default='Yeni insanlarla tanışmağı sevirəm.'); avatar=models.ImageField(upload_to='avatars/',blank=True,null=True); coins=models.PositiveIntegerField(default=1250); is_online=models.BooleanField(default=False); is_banned=models.BooleanField(default=False); last_seen=models.DateTimeField(null=True,blank=True); phone_model=models.CharField(max_length=120,blank=True); soft_banned_until=models.DateTimeField(null=True,blank=True)
    def online_now(self): return self.is_online and (not self.last_seen or (timezone.now()-self.last_seen).total_seconds()<300)
class Conversation(models.Model):
    members=models.ManyToManyField(User,related_name='conversations'); updated_at=models.DateTimeField(auto_now=True)
    def other(self,user): return self.members.exclude(pk=user.pk).first()
class Message(models.Model):
    conversation=models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name='messages'); sender=models.ForeignKey(User,on_delete=models.CASCADE); body=models.TextField(); created_at=models.DateTimeField(auto_now_add=True); read_at=models.DateTimeField(null=True,blank=True)
class Room(models.Model): name=models.CharField(max_length=80); description=models.CharField(max_length=180,blank=True)
class RoomMessage(models.Model): room=models.ForeignKey(Room,on_delete=models.CASCADE,related_name='messages'); sender=models.ForeignKey(User,on_delete=models.CASCADE); body=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)
class Notification(models.Model): user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications'); kind=models.CharField(max_length=40,default='system'); text=models.CharField(max_length=240); created_at=models.DateTimeField(auto_now_add=True); is_read=models.BooleanField(default=False)
class CoinTransaction(models.Model): user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='coin_transactions'); amount=models.IntegerField(); reason=models.CharField(max_length=180); created_at=models.DateTimeField(auto_now_add=True)
class CoinClaim(models.Model): user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='coin_claim'); claimed_at=models.DateTimeField(auto_now=True)
class CoinPurchase(models.Model): user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='coin_purchases'); coins=models.PositiveIntegerField(); price=models.DecimalField(max_digits=8,decimal_places=2); status=models.CharField(max_length=20,default='completed'); created_at=models.DateTimeField(auto_now_add=True)
class Post(models.Model):
    author=models.ForeignKey(User,on_delete=models.CASCADE,related_name='posts'); body=models.TextField(); created_at=models.DateTimeField(auto_now_add=True); likes=models.ManyToManyField(User,related_name='liked_posts',blank=True)
class Comment(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments'); author=models.ForeignKey(User,on_delete=models.CASCADE); body=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)
class Complaint(models.Model):
    STATUS_CHOICES=[('open','Açıq'),('reviewing','İncələnir'),('resolved','Həll edildi'),('dismissed','Rədd edildi')]
    CATEGORY_CHOICES=[('spam','Spam və reklam'),('harassment','Təhqir və narahat etmə'),('fake','Saxta profil'),('inappropriate','Uyğunsuz məzmun'),('other','Digər')]
    reporter=models.ForeignKey(User,on_delete=models.CASCADE,related_name='sent_complaints'); target=models.ForeignKey(User,on_delete=models.CASCADE,related_name='received_complaints'); category=models.CharField(max_length=30,choices=CATEGORY_CHOICES,default='other'); reason=models.TextField(); status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='open'); created_at=models.DateTimeField(auto_now_add=True); admin_note=models.TextField(blank=True)
