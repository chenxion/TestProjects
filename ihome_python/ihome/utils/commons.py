# coding:utf-8
# 自定义工具

from werkzeug.routing import BaseConverter  # 自定义转换器
from flask import session, jsonify, g  # 导入session数据, g全局对象
from ihome.utils.response_code import RET
import functools  # python内置：函数工具


# 定义一个正则转换器
class ReConverter(BaseConverter):
    """"""

    def __init__(self, url_map, regex):
        # 调用父类的初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# 定义的验证登录状态的装饰器
def login_required(view_func):  # 被装饰的函数
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):  # 被装饰的函数所接收的参数
        # 获取用户的登录状态
        user_id = session.get("user_id")

        # 如果用户是登录的，将被装饰的函数原样返回
        if user_id is not None:
            # 将user_id保存到g对象昂中，在视图函数中可以通过g对象获取和保存数据
            g.user_id = user_id
            return view_func(*args, **kwargs)
        # 如果没登录，阻止被装饰的函数的一切功能
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
        # 如果未登录，返回json数据(未登录的信息)

    # 将通过了用户登录验证的原函数，原样返还
    return wrapper
