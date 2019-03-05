# coding:utf-8
# ihome目录：整个Flask项目核心目录

import redis
import logging  # python自带log库
from logging.handlers import RotatingFileHandler  # 设置日志文件路径/大小/数量

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session  # session扩展,修改session存储机制
from flask_wtf import CSRFProtect  # 为flask提供csrf保护
from config import config_map  # 配置映射


# 创建数据库
db = SQLAlchemy()

# 创建空的redis连接对象, 工厂模式创建后连接redis数据库
redis_store = None

# 为flask提供csrf防护机制
csrf = CSRFProtect()


# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 开启调试(DEBUG)级别
# 创建日志记录器，指明日志保存的路径，每个日志文件最大大小，保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式               日志等级     输入日志信息的文件名 行数      日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s: %(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象(flask app使用的) 添加日志记录器
logging.getLogger().addHandler(file_log_handler)
from ihome.utils.commons import ReConverter  # 自定义正则转换器


# 工厂模式
def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name: str 配置模式的名字 (“develop”, “product”)
    :return:
    """
    app = Flask(__name__)  # 创建flask项目

    # 根据配置模式的名字获取配置参数的类
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 使用app初始化db数据库
    db.init_app(app)
    # 初始化redis工具, 将redis连接设置全局
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # 利用flask-session修改存储机制, 将session数据自动保存到redis中,以前存放在cookie中
    Session(app)

    # 为flask提供csrf防护
    CSRFProtect(app)

    # 为flask添加自定义的转换器
    app.url_map.converters["re"] = ReConverter

    # 注册蓝图
    from ihome import api_1_0  # 蓝图
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")  # url以/api/v1.0为前缀

    # 注册提供静态文件的蓝图
    from ihome import web_html
    app.register_blueprint(web_html.html)

    return app