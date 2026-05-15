import shutil
import os

src = r'C:/Users/wm881/WorkBuddy/20260513090923/data'
dst = r'C:/Users/wm881/WorkBuddy/20260513090923/github-pages-deploy/data'

if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print(f'已复制数据文件夹到: {dst}')
