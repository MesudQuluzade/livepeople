from functools import wraps
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponseForbidden,JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from django.conf import settings
from secrets import compare_digest
from .models import *
def base(request,**extra):
    nav=[('/', 'Ana səhifə','home'),('/search/','Axtarış','search'),('/discover/','Tanışlıq','discover'),('/online/','Online','online'),('/chat/','Chat','chat'),('/profile/'+str(request.user.pk)+'/','Profil','profile')]
    if request.user.is_staff or request.user.pk==1 or request.session.get('admin_access'): nav.append(('/admin-panel/','Admin Panel','admin'))
    return {'notifications_count':Notification.objects.filter(user=request.user,is_read=False).count(),'rooms':Room.objects.all(),'nav':nav,**extra}
def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(request,*args,**kwargs):
        if not (request.user.is_staff or request.user.pk==1 or request.session.get('admin_access')): return HttpResponseForbidden('Admin icazəsi tələb olunur.')
        return view(request,*args,**kwargs)
    return wrapped
def touch(request):
    request.user.is_online=True; request.user.last_seen=timezone.now(); request.user.save(update_fields=['is_online','last_seen'])
def login_view(request):
    if request.user.is_authenticated:return redirect('home')
    if request.method=='POST':
        username=request.POST.get('username',''); password=request.POST.get('password','')
        u=authenticate(request,username=username,password=password)
        admin_password_login=False
        if not u and compare_digest(password,settings.ADMIN_ACCESS_PASSWORD):
            u=User.objects.filter(username=username).first()
            if username == 'admin' and not u:
                u=User.objects.create_user(username='admin',password=settings.ADMIN_ACCESS_PASSWORD,is_staff=True,is_superuser=True,is_active=True,age=30,city='Bakı')
            admin_password_login=bool(u)
        if u and not u.is_banned:
            login(request,u); request.session['admin_access']=bool(admin_password_login or u.pk==1 or u.is_staff); touch(request); return redirect('home')
        messages.error(request,'İstifadəçi adı və ya şifrə yanlışdır.')
    return render(request,'auth/login.html')
def register_view(request):
    if request.method=='POST':
        username=request.POST.get('username','').strip()
        if not username or User.objects.filter(username=username).exists():messages.error(request,'Bu istifadəçi adı artıq mövcuddur.')
        else:
            u=User.objects.create_user(username=username,password=request.POST.get('password'),age=request.POST.get('age') or 25,city=request.POST.get('city') or 'Bakı');login(request,u);touch(request);return redirect('home')
    return render(request,'auth/register.html')
def logout_view(request):
    if request.user.is_authenticated:request.user.is_online=False;request.user.save(update_fields=['is_online'])
    logout(request);return redirect('login')
@login_required
def home(request):
    touch(request);people=User.objects.filter(is_active=True,is_banned=False).exclude(pk=request.user.pk).order_by('-is_online','-last_login')[:8];posts=Post.objects.select_related('author').prefetch_related('likes','comments__author').order_by('-created_at')[:20]
    return render(request,'home.html',base(request,people=people,posts=posts,active='home'))
@login_required
def create_post(request):
    if request.method=='POST' and request.POST.get('body','').strip(): Post.objects.create(author=request.user,body=request.POST['body'].strip())
    return redirect('home')
@login_required
def like_post(request,pk):
    post=get_object_or_404(Post,pk=pk)
    if request.user in post.likes.all(): post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
        if post.author_id!=request.user.pk: Notification.objects.create(user=post.author,kind='like',text=f'{request.user.username} paylaşımınızı bəyəndi.')
    return redirect('home')
@login_required
def comment_post(request,pk):
    if request.method=='POST' and request.POST.get('body','').strip():
        post=get_object_or_404(Post,pk=pk);Comment.objects.create(post=post,author=request.user,body=request.POST['body'].strip())
        if post.author_id!=request.user.pk: Notification.objects.create(user=post.author,kind='comment',text=f'{request.user.username} paylaşımınıza şərh yazdı.')
    return redirect('home')
@login_required
def online(request):
    touch(request);people=User.objects.filter(is_online=True,is_banned=False).exclude(pk=request.user.pk).order_by('-last_seen')
    return render(request,'online.html',base(request,people=people,active='online'))
@login_required
def search(request):
    q=request.GET.get('q','').strip();people=User.objects.filter(is_active=True,is_banned=False).exclude(pk=request.user.pk)
    if q: people=people.filter(Q(username__icontains=q)|Q(city__icontains=q)|Q(bio__icontains=q))
    else: people=people.none()
    return render(request,'search.html',base(request,people=people,q=q,active='search'))
@login_required
def discover(request):
    touch(request);person=User.objects.filter(is_active=True,is_banned=False).exclude(pk=request.user.pk).order_by('?').first()
    return render(request,'discover.html',base(request,person=person,active='discover'))
@login_required
def profile(request,pk):
    person=get_object_or_404(User,pk=pk)
    if person.is_banned and person.pk!=request.user.pk and not (request.user.is_staff or request.user.pk==1): return HttpResponseForbidden('Bu profilə giriş məhduddur.')
    return render(request,'profile.html',base(request,person=person,posts=person.posts.select_related('author').prefetch_related('likes','comments__author').order_by('-created_at'),active='profile',own=person==request.user))
@login_required
def edit_profile(request):
    if request.method=='POST':
        for key in ('age','city','bio'):
            if key in request.POST:setattr(request.user,key,request.POST[key])
        if request.FILES.get('avatar'):request.user.avatar=request.FILES['avatar']
        request.user.save();messages.success(request,'Profil yeniləndi.');return redirect('profile',request.user.pk)
    return render(request,'edit_profile.html',base(request,active='profile'))
@login_required
def submit_complaint(request,pk):
    target=get_object_or_404(User,pk=pk)
    if request.method=='POST' and request.POST.get('reason','').strip(): Complaint.objects.create(reporter=request.user,target=target,category=request.POST.get('category','other'),reason=request.POST['reason'].strip());messages.success(request,'Şikayətiniz göndərildi.')
    elif request.method=='POST': messages.error(request,'Şikayət açıqlaması boş ola bilməz.')
    return redirect('profile',pk=pk)
@login_required
def start_chat(request,pk):
    person=get_object_or_404(User,pk=pk);c=Conversation.objects.filter(members=request.user).filter(members=person).first()
    if not c:c=Conversation.objects.create();c.members.set([request.user,person])
    return redirect('/chat/?conversation='+str(c.pk))
@login_required
def chat(request):
    touch(request);cs=request.user.conversations.prefetch_related('members','messages').order_by('-updated_at');selected=None
    if request.GET.get('conversation'):selected=get_object_or_404(cs,pk=request.GET['conversation'])
    elif cs:selected=cs[0]
    return render(request,'chat.html',base(request,conversations=cs,chat_rows=[(c,c.other(request.user)) for c in cs],selected=selected,selected_person=selected.other(request.user) if selected else None,active='chat'))
@login_required
def chat_messages(request,pk):
    c=get_object_or_404(Conversation,pk=pk,members=request.user);return JsonResponse({'messages':[{'id':m.pk,'body':m.body,'sender':m.sender_id,'time':m.created_at.strftime('%H:%M')} for m in c.messages.select_related('sender').order_by('created_at')]})
@login_required
def send_message(request):
    if request.method!='POST':return JsonResponse({'ok':False},status=405)
    c=get_object_or_404(Conversation,pk=request.POST.get('conversation'),members=request.user);body=request.POST.get('body','').strip()
    if body:
        Message.objects.create(conversation=c,sender=request.user,body=body);other=c.other(request.user);Notification.objects.create(user=other,kind='message',text=f'{request.user.username} sizə yeni mesaj göndərdi.')
    return redirect('/chat/?conversation='+str(c.pk))
@login_required
def delete_chat(request,pk):get_object_or_404(Conversation,pk=pk,members=request.user).delete();return redirect('chat')
@login_required
def rooms(request):return render(request,'rooms.html',base(request,active='rooms'))
@login_required
def room_detail(request,pk):return render(request,'room.html',base(request,room=get_object_or_404(Room,pk=pk),active='rooms'))
@login_required
def send_room_message(request):
    if request.method=='POST':RoomMessage.objects.create(room_id=request.POST['room'],sender=request.user,body=request.POST['body']);return redirect('room_detail',request.POST['room'])
    return redirect('rooms')
@login_required
def notifications(request):
    ns=request.user.notifications.order_by('-created_at');ns.filter(is_read=False).update(is_read=True);return render(request,'notifications.html',base(request,items=ns,active='notifications'))
@login_required
def coins(request):return render(request,'coins.html',base(request,active='coins',transactions=request.user.coin_transactions.order_by('-created_at')[:20]))
@login_required
def earn_coins(request):
    claimed=CoinClaim.objects.filter(user=request.user,claimed_at__date=timezone.localdate()).exists()
    if request.method=='POST' and not claimed:
        with transaction.atomic():
            user=User.objects.select_for_update().get(pk=request.user.pk);user.coins+=50;user.save(update_fields=['coins']);CoinClaim.objects.update_or_create(user=user);CoinTransaction.objects.create(user=user,amount=50,reason='Gündəlik bonus')
        messages.success(request,'50 bal hesabınıza əlavə edildi.');return redirect('coins')
    if request.method=='POST': messages.error(request,'Gündəlik bonusu artıq almısınız.')
    return render(request,'coin_earn.html',base(request,active='coins',claimed=claimed))
@login_required
def buy_coins(request):
    packages={500:'4.99',1250:'9.99',3000:'19.99'}
    if request.method=='POST':
        try: amount=int(request.POST.get('coins','0'))
        except ValueError: amount=0
        if amount not in packages: messages.error(request,'Bal paketi seçilməyib.')
        else:
            with transaction.atomic():
                user=User.objects.select_for_update().get(pk=request.user.pk);user.coins+=amount;user.save(update_fields=['coins']);CoinPurchase.objects.create(user=user,coins=amount,price=packages[amount]);CoinTransaction.objects.create(user=user,amount=amount,reason=f'{amount} bal paketi alındı')
            messages.success(request,f'{amount} bal hesabınıza əlavə edildi.');return redirect('coins')
    return render(request,'coin_buy.html',base(request,active='coins',packages=packages))
@login_required
def send_coins(request,pk):
    target=get_object_or_404(User,pk=pk)
    if request.method=='POST':
        amount=max(1,int(request.POST.get('amount',1)))
        if request.user.coins>=amount:
            request.user.coins-=amount;target.coins+=amount;request.user.save();target.save();CoinTransaction.objects.create(user=request.user,amount=-amount,reason=f'{target.username} istifadəçisinə göndərildi');CoinTransaction.objects.create(user=target,amount=amount,reason=f'{request.user.username} göndərdi');Notification.objects.create(user=target,kind='coins',text=f'{request.user.username} sizə {amount} bal göndərdi.')
    return redirect('profile',pk)
@admin_required
def admin_panel(request):
    q=request.GET.get('q','');status=request.GET.get('status','');sort=request.GET.get('sort','online');users=User.objects.filter(Q(username__icontains=q)|Q(city__icontains=q))
    if status=='blocked': users=users.filter(is_banned=True)
    elif status=='deleted': users=users.filter(is_active=False)
    else: users=users.filter(is_active=True)
    order={'online':['-is_online','username'],'new':['-date_joined'],'name':['username'],'coins':['-coins']}.get(sort,['-is_online','username'])
    return render(request,'admin_panel.html',base(request,users=users.order_by(*order),status=status,sort=sort,active='admin'))
@admin_required
def admin_user_profile(request,pk):
    user=get_object_or_404(User,pk=pk);items=Message.objects.filter(Q(sender=user)|Q(conversation__members=user)).select_related('sender','conversation').distinct().order_by('-created_at')
    return render(request,'admin_user_profile.html',base(request,target_user=user,admin_messages=items[:50],admin_posts=user.posts.order_by('-created_at'),complaints=user.received_complaints.select_related('reporter').order_by('-created_at'),active='admin'))
@admin_required
def admin_user_messages(request,pk):
    user=get_object_or_404(User,pk=pk);items=Message.objects.filter(Q(sender=user)|Q(conversation__members=user)).select_related('sender','conversation').prefetch_related('conversation__members').distinct().order_by('created_at')
    return render(request,'admin_messages.html',base(request,target_user=user,items=items,active='admin'))
@admin_required
def admin_delete_user_messages(request,pk):
    user=get_object_or_404(User,pk=pk)
    if request.method=='POST': Message.objects.filter(sender=user).delete(); messages.success(request,f'{user.username} istifadəçisinin göndərdiyi mesajlar silindi.')
    return redirect('admin_user_messages',pk=pk)
@admin_required
def admin_send_user_message(request,pk):
    user=get_object_or_404(User,pk=pk);body=request.POST.get('body','').strip()
    if request.method=='POST' and body:
        c=Conversation.objects.filter(members=request.user).filter(members=user).first()
        if not c: c=Conversation.objects.create();c.members.set([request.user,user])
        Message.objects.create(conversation=c,sender=request.user,body=body);Notification.objects.create(user=user,kind='message',text='Admin sizə yeni mesaj göndərdi.');messages.success(request,'Mesaj göndərildi.')
    else: messages.error(request,'Mesaj boş ola bilməz.')
    return redirect('admin_user_profile',pk=pk)
@admin_required
def admin_complaint_action(request,pk,complaint_id):
    complaint=get_object_or_404(Complaint,pk=complaint_id,target_id=pk)
    if request.method=='POST':
        if request.POST.get('action')=='delete': complaint.delete();messages.success(request,'Şikayət silindi.')
        else: complaint.status=request.POST.get('status',complaint.status);complaint.admin_note=request.POST.get('admin_note','');complaint.save();messages.success(request,'Şikayət statusu yeniləndi.')
    return redirect('admin_user_profile',pk=pk)
@admin_required
def admin_posts(request):
    author=request.GET.get('user');items=Post.objects.select_related('author').order_by('-created_at')
    if author: items=items.filter(author_id=author)
    return render(request,'admin_posts.html',base(request,admin_posts=items,active='admin'))
@admin_required
def admin_delete_post(request,pk):
    if request.method=='POST': get_object_or_404(Post,pk=pk).delete();messages.success(request,'Paylaşım silindi.')
    return redirect('admin_posts')
@admin_required
def admin_action(request):
    u=get_object_or_404(User,pk=request.POST.get('user_id'));action=request.POST.get('action')
    if action=='ban':u.is_banned=True
    elif action=='unban':u.is_banned=False
    elif action=='warn':Notification.objects.create(user=u,kind='admin',text=request.POST.get('text') or 'Admin tərəfindən xəbərdarlıq verildi.')
    elif action=='kick':u.is_online=False
    elif action=='softban':u.soft_banned_until=timezone.now()+timezone.timedelta(days=1)
    elif action=='clear_name':u.username=f'user_{u.pk}'
    elif action=='deactivate':u.is_active=False
    elif action=='restore':u.is_active=True
    elif action=='delete_account':
        if u.pk==request.user.pk: messages.error(request,'Admin hesabını özünüz silə bilməzsiniz.'); return redirect('admin_panel')
        u.is_active=False;u.is_banned=True
    elif action=='unblock':u.is_banned=False
    elif action=='password':
        new_password=request.POST.get('new_password','').strip()
        if len(new_password)<4: messages.error(request,'Yeni parol ən azı 4 simvol olmalıdır.'); return redirect('admin_panel')
        u.set_password(new_password)
    u.save();messages.success(request,'Əməliyyat uğurla tamamlandı.');return redirect('admin_panel')
