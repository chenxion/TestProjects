# coding:utf-8
import redis


class Config(object):
    '''配置信息'''
    SECRET_KEY = "dsafsarwqedsdss"

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome_python"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis配置文件
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask-session配置,并创建session_redis的实例
    SESSION_TYPE = "redis"  # 用redis存储session
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中的session_id进行隐藏
    PERMANENT_SESSION_LIFETIME = 3600 * 24  # session数据的有效时间


class DevelopmentConfig(Config):
    '''开发模式的配置信息'''
    DEBUG = True  # 开启之后会导致logging的日志等级失效


class ProductionConfig(Config):
    '''生产环境配置信息'''
    pass


# 配置信息的映射关系
config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}
