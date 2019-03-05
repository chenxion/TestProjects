# coding:utf-8
# api_1.0目录：项目的蓝图

from flask import Blueprint  # 蓝图


# 创建蓝图对象
api = Blueprint("api_1_0", __name__)

# 让'api_1_0蓝图' 知道自己的文件里面有几个视图
from . import index, verify_code, passport, profile, houses, orders, pay
