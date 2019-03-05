from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login, logout  # 校验用户认证函数
from django.core.paginator import Paginator  # 分页
# app模块：
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderGoods, OrderInfo
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired  # 导入一个异常
import re
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection  # 导入配置redis链接的函数


# Create your views here.


# def register(request):
#     '''注册'''
#     if request.method == 'GET':
#         # 显示注册页面
#         return render(request, 'register.html')
#     else:
#         # 进行注册处理
#         # 接收数据
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         # 进行数据校验
#         if not all([username, password, email]):  # 依次判断三个数据全部为True通过
#             return render(request, 'register.html', {'errmsg': '数据不完整'})
#
#         # 校验邮箱
#         if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': '请勾选协议'})
#
#         # 校验用户名是否重复
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:  # 如果找不到用户
#             # 用户不存在
#             user = None
#             # 进行业务处理：进行用户注册
#             user = User.objects.create_user(username, email, password)
#             user.is_active = 0
#             user.save()
#             # 返回应答, 跳转首页
#             return redirect(reverse('goods:index'))
#
#         if user:
#             # 用户名已存在
#             return render(request, 'register.html', {'errmsg': '用户名已存在'})
#
#         # # 进行业务处理：进行用户注册
#         # user = User.objects.create_user(username, email, password)
#         # user.is_active = 0
#         # user.save()
#
#         # # 返回应答, 跳转首页
#         # return redirect(reverse('goods:index'))


# /user/register
class RegisterViews(View):
    '''注册'''
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
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
            user.is_active = 0  # 将用户激活状态改为否，因为create_user方法创建的用户默认激活了
            user.save()

            # 发送激活邮件，包含激活的链接：http://127.0.0.1:8000/user/active/3
            # 激活链接中需要包含用户的身份信息，并且要把信息进行加密

            # 加密用户的身份信息，生成激活的token
            serializer = Serializer(settings.SECRET_KEY, 3600)
            info = {'confirm': user.id}
            token = serializer.dumps(info)  # bytes字节
            token = token.decode('utf8')  # 解码成字符串

            # 发邮件
            send_register_active_email.delay(email, username, token)
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


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 激活链接已过期, 实际项目应该再发一次激活的链接
            return HttpResponse('激活链接过期')


# /user/login
class LoginView(View):
    '''登陆'''
    def get(self, request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        # 使用模板
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登陆校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理：内置函数进行 登陆校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态 ***必须开启redis服务器
                login(request, user)

                # 获取登陆后所要跳转到 next参数里面的的地址, 如果用户url里面没有next，就设置默认值 goods:index
                next_url = request.GET.get('next', reverse('goods:index'))

                # 跳转到首页  是HttpResponseRedirect的子类
                response = redirect(next_url)

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名, 设置缓存数据
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response

            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出'''
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user          LoginRequiredMixin 可以防止用户没有登录url 手动输入url进来
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示 + 欢迎信息的显示'''
        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='192.168.0.105', port='6379', db=2)
        con = get_redis_connection('default')  # 'default'对应的是 setting配置:CACHES{ 'default':{...} }

        history_key = 'history_%s' % user.id

        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)  # [2, 1, 3]

        # 方法1.  从数据库中查询用户浏览的商品的具体信息,返回列表集合
        # goods_set = GoodsSKU.objects.filter(id__in=sku_ids)
        # goods_res = []  # 定义一个列表
        # for a_id in sku_ids:  # sku_ids = [2, 1, 3]
        #     for goods in goods_set:  # goods_set = [1, 2, 3]
        #         if a_id == goods.id:  # 让goods.id的顺序强制按照a_id的顺序排列保持一致
        #             goods_res.append(goods)  # 如果数据库查出来的id顺序和用户浏览商品顺序相同就添加到goods_res

        # 方法2.  遍历获取用户浏览的历史商品信息
        goods_set = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_set.append(goods)

        # 组织上下文
        context = {'page': 'user', 'address': address, 'goods_set': goods_set}

        # 如果用户登录 --> User的一个实例                如果用户没登录 --> AnonymousUser的一个实例，
        # request.user.is_authenticated() 返回True，  request.anonymousUser.is_authenticated() 返回Fault
        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        # 为信息页面设置一个值page = 'user'，使用函数就自动 调用这个相关的html文件的 .active类
        return render(request, 'user_center_info.html', context)


# /user/order    LoginRequiredMixin 没有登录无法访问
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')  # 用户订单信息按时间从上向下排序

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题         order.order_status=1
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文 为信息页面设置一个值page = 'order'，使用函数就自动 调用这个相关的html文件的 .active类添加一个选中效果
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        return render(request, 'user_center_order.html', context)


# /user/address  LoginRequiredMixin 的作用是只有用户登陆了才能访问
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        # 获取用户的默认收货地址
        # 获取登录用户对用的 User 对象
        user = request.user

        # try:  # 如果查不到会抛出异常，要用try包起来
        #     address = Address.objects.get(user=user, is_default=True)  # objects是models.Manager的类对象
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        # 为信息页面设置一个值page = 'address'，使用函数就自动 调用这个相关的html文件的 .active类
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        '''地址额添加'''
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号码
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        # 业务处理：地址添加
        # 如果用户已存在默认的收货地址，添加的地址不作为默认地址，否则作为默认地址
        # 获取登录用户对用的 User 对象
        user = request.user
        # try:  # 如果查不到会抛出异常，要用try包起来
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:  # 如果存在说明这用户是默认地址，将下面创建的地址设置为否
            is_default = False
        else:        # 如果不存在说明不是默认地址，就下面创建的地址设为默认
            is_default = True

        # 添加地址
        Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)

        # 返回应答  get请求方式
        return redirect(reverse('user:address'))
