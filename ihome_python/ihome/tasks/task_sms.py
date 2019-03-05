# coding:utf-8


from celery import Celery  # 导入Celery类
from ihome.libs.yuntongxun.sms import CCP  # 发送短信类


# 定义celery对象名字为 ihome，指定中间消息人为redis
celery_app = Celery("ihome", broker="redis://127.0.0.1/1")


# 建立异步任务, send_sms就是任务名
@celery_app.task
def send_sms(to, datas, temp_id):
    """发送短信的异步任务"""
    ccp = CCP()
    ccp.send_template_sms(to, datas, temp_id)
