# coding=utf-8

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def sendmail_initial(email_config, att1name, att2name):
    # qq邮箱smtp服务器
    host_server = email_config['email_server']
    # sender_qq为发件人的qq号码
    sender_qq = email_config['sender_qq']
    # pwd为qq邮箱的授权码
    pwd = email_config['pwd']
    # sender_qq为发件人的邮箱
    sender_qq_mail = email_config['sender_qq_mail']
    # 收件人邮箱
    receiver = email_config['receiver']

    # 邮件标题
    inspectiondata = time.strftime("%Y/%m/%d", time.localtime(time.time()))
    mail_title = email_config['email_title'] + inspectiondata
    # 邮件的正文内容
    mail_content = email_config['mail_content'].format(inspectiondata)


    # 邮件正文内容
    msg = MIMEMultipart()
    # msg = MIMEText(mail_content, "plain", 'utf-8')
    msg["Subject"] = Header(mail_title, 'utf-8')
    msg["From"] = sender_qq_mail
    msg["To"] = Header("管理员{0}".format(receiver), 'utf-8')  ## 接收者的别名

    # 邮件正文内容
    msg.attach(MIMEText(mail_content, 'html', 'utf-8'))

    # 构造附件1
    att1 = MIMEText(open(att1name, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    att1.add_header("Content-Disposition" , 'attachment', filename=("gbk", "","巡检报告.html"))
    msg.attach(att1)

    # 构造附件2，传送当前目录下的 runoob.txt 文件

    att2 = MIMEText(open(att2name, 'rb').read(), 'base64', 'utf-8')
    att2["Content-Type"] = 'application/octet-stream'
    att2.add_header("Content-Disposition" , 'attachment',filename=("gbk", "","详细数据记录.html"))
    msg.attach(att2)

    # ssl登录
    smtp = SMTP_SSL(host_server)
    # set_debuglevel()是用来调试的。参数值为1表示开启调试模式，参数值为0关闭调试模式
    smtp.set_debuglevel(1)
    smtp.ehlo(host_server)
    smtp.login(sender_qq, pwd)
    smtp.sendmail(sender_qq_mail, receiver, msg.as_string())
    smtp.quit()


if __name__ == '__main__':
    import yaml
    with open('../config.yml', 'r', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
    if config['sendmail']['enable'] is True:
        sendmail_initial(config)