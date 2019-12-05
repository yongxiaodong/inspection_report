### 主要文件介绍：
    inspection_report.py 主程序
    config.yml 配置文件
    templates 模板目录文件
    pcinfo.txt 主机IP、端口、用户、密码、描述5列


### 运行
    创建pcinfo.txt文件，写入主机IP、端口、用户、密码、描述5列，以空格分隔，每台机器一行
    例：192.168.1.1 22 root password db
    运行inspection_report.py，并等待执行结束，运行结束会在终端打印运行结束并显示耗时

### 结果输出
    运行结束后，会生成html_dir目录，改目录中包含了巡检记录和详细数据
    生成的其他目录：md_dir等是临时文件

> 不需要手动清空临时目录，主程序每次运行前会自动清空这些目录

### 运行依赖
    python 3
    import paramiko
    import traceback
    import socket
    import re
    import markdown
    import logging
    import yaml
    import time
    import os
    import shutil
    from multiprocessing import Pool
    