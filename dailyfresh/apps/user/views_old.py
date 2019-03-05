from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
import re
from apps.user.models import User

# Create your views here.


def register(request):
    '''显示注册页面'''
    return render(request, 'register.html')


def register_handle(request):
    '''进行注册处理'''
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')
    # 进行数据校验
    if not all([username, password, email]):  # 依次判断三个数据全部为True通过
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请勾选协议'})

    # 校验用户名是否重复
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:  # 如果找不到用户
        # 用户不存在
        user = None
        # 进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 返回应答, 跳转首页
        return redirect(reverse('goods:index'))

    if user:
        # 用户名已存在
        return render(request, 'register.html', {'errmsg': '用户名已存在'})

    # # 进行业务处理：进行用户注册
    # user = User.objects.create_user(username, email, password)
    # user.is_active = 0
    # user.save()

    # # 返回应答, 跳转首页
    # return redirect(reverse('goods:index'))
