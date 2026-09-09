from django.contrib import admin
from .models import User,Conversation,Message,Room,RoomMessage,Notification,CoinTransaction,Post,Comment,Complaint,CoinClaim,CoinPurchase
admin.site.register([User,Conversation,Message,Room,RoomMessage,Notification,CoinTransaction,Post,Comment,Complaint,CoinClaim,CoinPurchase])
