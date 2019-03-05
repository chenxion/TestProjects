from django.shortcuts import render, redirect  # 页面渲染、页面跳转
from django.core.urlresolvers import reverse  # 反向解析
from django.views.generic import View
from apps.goods.models import GoodsType, GoodsSKU, IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection
from django.core.cache import cache
from apps.order.models import OrderGoods
from django.core.paginator import Paginator  # 分页类


# http://127.0.0.1:8000
class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示首页'''
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            print("给浏览器设置缓存")
            # 缓存中没有数据
            # 获取商品的种类信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for type in types: # GoodsType
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 设置缓存 key  value  timeout
            cache.set('index_page_data', context, 3600)
        # 获取用户购物车中商品的数目
        user = request.user  # 拿到用户信息，不管有没有登陆
        cart_count = 0
        if user.is_authenticated():  # 判断用户登陆没
            # 用户已登录
            conn = get_redis_connection('default')  # 链接redis数据库
            cart_key = 'cart_%d' % user.id  # 获取数据库里面 key的名字
            cart_count = conn.hlen(cart_key)  # 获取 key里面数据的数量

        # 组织模板上下文 字典的update方法值存在就替换，不存在就添加新的
        context.update(cart_count=cart_count)  # 关键字传参数
        # 使用模板
        return render(request, 'index.html', context)


# /goods/商品id
class DetailView(View):
    '''详情页'''
    def get(self, request, goods_id):
        '''显示详情页'''
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在，返回首页
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品的评论信息 filter.exclude()方法过滤掉里面的数据
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')  # 链接redis数据库
            cart_key = 'cart_%d' % user.id  # 获取数据库里面 key的名字
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史记录
            conn = get_redis_connection('default')  # 链接redis数据库
            history_key = 'history_%d' % user.id  # 获取数据库里面 key的名字
            # 移除列表中的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id插入到列表的左侧
            conn.lpush(history_key, goods_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)

        # 组织模板上下文
        context = {'sku': sku, 'types': types,
                   'sku_orders': sku_orders,
                   'new_skus': new_skus,
                   'same_spu_skus': same_spu_skus,
                   'cart_count': cart_count}

        # 使用模板
        return render(request, 'detail.html', context)


# 种类id 页码 排序方式 需要3种信息
# restful api -> 请求一种资源
# /list?type_id=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式
class ListView(View):
    '''列表页'''
    def get(self, request, type_id, page):
        '''显示列表页'''
        # 获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在，返回首页
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取排序的方式 获取分类商品的信息
        # sort=default 按照默认id排序
        # sort=price 按照商品价格排序
        # sort=hot 按照商品销量排序
        sort = request.GET.get('sort')  # 获取 list.html的sort属性

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据进行分页，对 skus分页每页显示1条数据
        paginator = Paginator(skus, 1)  # 总页数

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1  # 如果用户输入错了默认第一页

        if page > paginator.num_pages:
            page = 1  # 如果页数大于总页数默认第一页

        # 获取第page页的全部Page实例对象(数据)
        skus_page = paginator.page(page)  # 当前页上所有对象的列表

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示前的1-5页
        # 3.如果当前页是后3页，显示后面的5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages  # 总页数
        if num_pages < 5:  # 如果总页数小于5页
            pages = range(1, num_pages+1)  # 显示 [1,总页数+1]的页码范围
        elif page <= 3:  # 如果当前页数小于3
            pages = range(1, 6)  # 显示 [1,2,3,4,5]的页码范围
        elif num_pages - page <= 2:  # 如果总页数减去当前页小于等于2，也是后3页
            pages = range(num_pages-4, num_pages+1)  # 显示 [5页-4页,5页+1页] = [1, 6]的页码范围
        else:
            pages = range(page-2, page+3)  # 显示 [当前页-2,当前页+3]的范围，显示当前页的前2页，当前页，当前页的后2页



        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {'type': type, 'types': types,
                   'skus_page': skus_page,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'pages': pages,
                   'sort': sort}

        # 使用模板
        return render(request, 'list.html', context)
