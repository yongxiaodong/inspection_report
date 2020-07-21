### 演示地址
    巡检报告输出：https://itgod.org/book/inspection_example/%E5%B7%A1%E6%A3%80%E6%8A%A5%E5%91%8A.md.html
    巡检数据记录输出：https://itgod.org/book/inspection_example/%E5%B7%A1%E6%A3%80%E8%AF%A6%E7%BB%86%E6%95%B0%E6%8D%AE%E8%AE%B0%E5%BD%95.md.html

### 用途
    1、通过SSH方式自动登陆机器获取CPU、内存、磁盘等数据（无需客户端）
    2、分析获取的数据并以HTML方式汇总出 巡检报告 和 巡检的数据记录
    3、可以开启发送邮件功能，通过与Crontab结合定时将汇总后的报告发送到指定邮箱

### 主要文件介绍：
    inspection_report.py 主程序
    config.yml 配置文件
    templates 模板目录文件
    pcinfo.txt 其中包含 主机IP、端口、用户、密码、主机描述信息 5列，主机描述信息可任意填写


### 运行
    注意：首先你需要具备Python3环境
    
    1、git clone https://github.com/yongxiaodong/inspection_report.git
    2、pip3 install -r required.txt
    3、修改pcinfo.txt文件，按需写入主机IP、端口、用户、密码、描述5列，以空格分隔。依次写入多行，每行表示一台主机
    例：
    192.168.1.1 22 root password db1
    192.168.1.2 22 root password db2
    
    4、python3 inspection_report.py，并等待执行结束，运行结束会在终端打印运行结束并显示耗时

### 结果输出
    运行结束后，会生成html_dir目录，改目录中包含了巡检记录和详细数据
    生成的其他目录：md_dir等是临时文件

> 不需要手动清空临时目录，主程序每次运行前会自动清空这些目录

### 运行依赖
    pip3 install -r required.txt
    
