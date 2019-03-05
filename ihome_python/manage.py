# coding:utf-8
# 该文件只保留启动文件

from ihome import create_app, db  # flask应用模式
from flask_script import Manager  # 脚本管理
from flask_migrate import Migrate, MigrateCommand  # 数据库迁移管理

# 创建flask的应用对象
app = create_app("product")

# 管理flask项目
manager = Manager(app)
# 数据库迁移脚本
Migrate(app, db)  # 管理数据库
manager.add_command("db", MigrateCommand)

if __name__ == '__main__':
    manager.run()
