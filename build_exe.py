import PyInstaller.__main__
import os
import sys

def build():
    # 确保在项目根目录下运行
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # 准备打包参数
    args = [
        'modifier/main.py',              # 入口文件
        '--onefile',                     # 打包成单个文件
        '--noconsole',                   # 运行时不显示控制台
        '--name=StardewSaveEditor',      # 生成的可执行文件名
        '--paths=modifier',              # 将 modifier 目录加入搜索路径，解决 ui/models 模块找不到的问题
        f'--add-data=modifier/F.png{os.pathsep}.', # 添加图标资源
        f'--add-data=modifier/F.ico{os.pathsep}.', # 添加图标资源
        f'--add-data=modifier/i18n{os.pathsep}i18n', # 添加语言包
        f'--add-data=generated/cookingrecipes.json{os.pathsep}generated', # 添加数据文件
        f'--add-data=generated/craftingrecipes.json{os.pathsep}generated',
        f'--add-data=generated/iteminfo.json{os.pathsep}generated',
        '--icon=modifier/F.ico',         # 设置可执行文件图标
        '--clean',                       # 打包前清理临时文件
    ]

    # 执行打包
    print(f"开始打包 StardewSaveEditor.exe...")
    PyInstaller.__main__.run(args)
    print(f"打包完成！可执行文件位于 dist/StardewSaveEditor.exe")

if __name__ == "__main__":
    build()
