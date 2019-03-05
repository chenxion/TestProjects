# 定义索引类
from haystack import indexes
# 导入你的模型类
from apps.goods.models import GoodsSKU


# 指定对于某个类的的某些数据建立索引
# 索引类名格式:模型类名+Index
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 索引字段 use_template=True的作用: 指定根据表中哪些字段建立索引文件，把说明放在一个文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回你的模型类
        return GoodsSKU

    # 建立索引的数据，对GoodsSKU所有实例对象建立索引
    def index_queryset(self, using=None):

        return self.get_model().objects.all()
