from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
'''
此功能无法再windows运行，需要Linux环境下，配合FastDFS + Nginx
'''


class FDFSStorage(Storage):
    '''fast dfs文件存储类'''
    def _open(self, name, mode='rb'):
        '''打开文件时使用，没有重写此方法'''
        pass

    def _save(self, name, content):
        '''保存文件时使用'''
        # name:你选择上传文件的名字
        # content:包含你上传文件内容的File对象

        # 创建一个Fdfs_client对象
        Fdfs_client