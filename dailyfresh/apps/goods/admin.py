from django.contrib import admin
from apps.goods.models import GoodsType, IndexPromotionBanner, IndexGoodsBanner, IndexTypeGoodsBanner
from django.core.cache import cache
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''后台管理页面 新增或更新表中的数据时调用'''
        # 先调用父类默认的save_model，然后在修改现在的save_model方法
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker异步重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        '''后台管理页面 删除表中的数据时调用'''
        super().delete_model(request, obj)

        # 发出任务，让celery worker异步重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存
        cache.delete('index_page_data')


class GoodsTypeAdmin(BaseModelAdmin):  # 管理员每次进行增删改操作时重新生成静态页
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass

# 登陆管理页面的模块
admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
