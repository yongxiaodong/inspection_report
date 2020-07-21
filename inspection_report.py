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
import multiprocessing
from modules import sendmail
from sys import path


logging.basicConfig(filename='debug.txt', format='[%(levelname)s %(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO, filemode='a')


class Check_dir_status():
    def __init__(self, target_dir):
        self.target_dir = target_dir

    def check_dir_status(self):
        try:
            if not os.path.exists(self.target_dir):
                logging.INFO(f'检查目录{self.target_dir}不存在,开始创建目录{self.target_dir}')
                os.mkdir(self.target_dir)
        except Exception as e:
            logging.error(f'check_dir_status fail,message:{e}')


class Basic_config:
    """该类初始化一些配置"""

    def __init__(self, config_file='config.yml'):
        self.config_file = config_file
        # 加载config.yml
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.load(f.read(), Loader=yaml.FullLoader)
        except Exception as e:
            logging.error(f'加载配置文件{self.config_file}失败,message:{e}')

    def recursion_delete_file(self, dir):
        allfile = os.listdir(dir)
        for file in allfile:
            file = os.path.join(dir, file)
            if os.path.isdir(file):
                self.recursion_delete_file(file)
            else:
                os.remove(file)

    def get_config(self):
        return self.config

    def get_out_md_dir(self):
        try:
            out_md_dir = config['out_md_dir']
            if not os.path.exists(out_md_dir):
                logging.info(f'创建{out_md_dir}目录')
                os.mkdir(out_md_dir)
            else:
                logging.info(f'清空{out_md_dir}目录')
                self.recursion_delete_file(out_md_dir)
            return out_md_dir
        except KeyError as e:
            logging.error(f'获取key:out_md_dir失败，message:{e}')
        except Exception as e:
            logging.error(f'获取out_md_dir目录失败，message:{e}')

    def get_out_html_dir(self):
        try:
            out_html_dir = config['out_html_dir']
            if not os.path.exists(out_html_dir):
                os.mkdir(out_html_dir)
            else:
                logging.info(f'清空{out_html_dir}目录')
                self.recursion_delete_file(out_html_dir)
            return out_html_dir
        except KeyError as e:
            logging.error(f'获取key:out_html_dir，message:{e}')
        except Exception as e:
            logging.error(f'获取out_html_dir目录失败，message:{e}')

    def get_pcinfo(self):
        # 获取pcinfo
        try:
            pc_info = config['pcinfo']
            with open(pc_info, 'r', encoding='utf-8') as f:
                pc_info = f.read()
                return pc_info.strip().split('\n')
        except Exception as e:
            logging.error(f'加载{pcinfo}文件失败,message:{e}')

    def get_templates_path(self):
        try:
            templates_path = config['templates']
            return templates_path
        except Exception as e:
            logging.error(f'获取templates_path失败,message:{e}')

    def get_temp_dir(self):
        try:
            temp_dir = config['temp_dir']
            if not os.path.exists(temp_dir):
                logging.info(f'开始创建{temp_dir}目录')
                os.mkdir(temp_dir)
            else:
                logging.info(f'开始清空{temp_dir}目录')
                self.recursion_delete_file(temp_dir)
            return temp_dir
        except Exception as e:
            logging.error(f'初始化get_temp_dir函数失败,message:{e}')

    def get_temp_templates(self):
        try:
            temp_templates = config['temp_templates']
            if not os.path.exists(temp_templates):
                logging.info(f'开始创建{temp_templates}目录')
                os.mkdir(temp_templates)
            return temp_templates
        except Exception as e:
            logging.error(f'初始化get_temp_templates函数失败,message:{e}')


class Ssh:
    """该类执行命令并返回结果"""

    def __init__(self, ip, port, user, password, command, q, ssh_timeout=5, execute_timeout=20):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.command = command
        self.ssh_timeout = ssh_timeout
        self.execute_timeout = execute_timeout
        self.q = q
    def execute_command(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, self.port, self.user, self.password, timeout=self.ssh_timeout)
            for command, filename in self.command.items():
                stdin, stdout, stderr = ssh.exec_command(command, timeout=self.execute_timeout)
                response_out = stdout.read().decode('utf-8')
                yield response_out, filename, command
        except paramiko.ssh_exception.AuthenticationException as e:
            logging.error(f'{self.ip},密码验证错误，{e}')
            self.q.put(f'{self.ip}')
        except socket.timeout as e:
            logging.error(f'{self.ip},链接超时,{e}')
            self.q.put(f'{self.ip}')
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            logging.error(f'{self.ip},端口链接失败,{e}')
            self.q.put(f'{self.ip}')
        except Exception as e:
            logging.error(f'未知异常,{traceback.print_exc()},{e}')
            self.q.put(f'{self.ip}')
        finally:
            ssh.close()


class Generator_md(Ssh):
    """操作Markdown、控制生成Markdown"""

    def __init__(self, ip, port, user, password,
                 remarks='', ssh_timeout=5,
                 execute_timeout=20):
        super().__init__(ip, port, user, password, command, q, ssh_timeout, execute_timeout)
        self.target_dir = target_dir
        self.templates_path = templates_path
        self.temp_dir = temp_dir
        self.temp_templates = temp_templates
        self.remarks = remarks
        self.parse_rule = parse_rule
        self.command = command
        self.ip = ip
        self.remarks = remarks

# 获取到数据
    def get_data(self):
        for data, filename, command in self.execute_command():
            self.generator_abnormal_md(data, filename, command)
            data = re.sub('\n', '<br>', data)
            data = re.sub(' ', '&nbsp;', data)
            self.generator_normal_md(data, filename, command)

# 从templates复制详细数据页面md到temp，并写入数据
    def generator_normal_md(self, data, filename, command):
        try:
            status = 0
            if not os.path.exists(f'{self.temp_dir}/{filename}.md'):
                if os.path.exists(f'{self.temp_templates}/{filename}.md'):
                    shutil.copy(f'{self.temp_templates}/{filename}.md', f'{self.temp_dir}/{filename}.md')
                    status = 1
                else:
                    logging.error(f'当前处理服务器:{self.ip},从{self.temp_templates}复制模板{filename}.md失败,请检查{self.temp_templates}中是否存在{filename}.md模板文件')
            else:
                status = 1
            if status == 1:
                with open(f'{self.temp_dir}/{filename}.md', 'a', encoding='utf-8') as f:
                    data = re.sub('\n', '<br>', data)
                    f.write(f'{self.ip} | {data} | {self.remarks} | {command}' + '\n')
        except Exception as e:
            logging.error(f'generator_normal_md函数执行错误,message：{e}')

# 判断temp目录中是否已经包含当前命令对应的a_md文件(异常文件)，不存在则从templates复制
    def generator_a(self, filename, max_value):
        if not os.path.exists(f'{self.temp_dir}/a_{filename}.md'):
            with open(f'{self.templates_path}/{filename}.md', 'r', encoding='utf-8')as f, open(
                    f'{self.temp_dir}/a_{filename}.md', 'w', encoding='utf-8') as f2:
                f2.write(f.read().format(max_value))

    # 将获取到的数据进行异常分析并生成md
    def generator_abnormal_md(self, data, filename, command):
        try:
            #判断返回的数据是否为真，并判断命令是否在config文件中
            if command in self.parse_rule:
                max_value = self.parse_rule[command][0]
                description = self.parse_rule[command][1]
                if command == 'uptime':
                    self.generator_a(filename, max_value)
                    data = list(map(float, data.strip().split(':')[-1].split(',')))
                    if data[0] > max_value or data[1] > max_value or data[2] > max_value:
                        with open(f'{self.temp_dir}/a_{filename}.md', 'a', encoding='utf-8') as f:
                            f.write(description.format(self.ip, data) + '\n')
                elif command == 'df -hP':
                    result = ''
                    self.generator_a(filename, max_value)
                    data = data.split('\n')
                    for line in data[1:]:
                        if line:
                            line = line.split()
                            use_rate = line[-2].split('%')[0]
                            mount_point = line[-1]
                            if float(use_rate) > max_value:
                                result = result + f'{mount_point} : {use_rate}%<br>'
                    if result:
                        with open(f'{self.temp_dir}/a_{filename}.md', 'a', encoding='utf-8') as f:
                            f.write(description.format(self.ip, result) + '\n')
                elif command == 'free -m':
                    self.generator_a(filename, max_value)
                    if 'available' in data.split('\n')[0]:
                        line = list(map(int, data.split('\n')[1].split()[1:]))
                        use_rate = float((1 - line[5] / line[0]) * 100)
                    else:
                        line = list(map(int, data.split('\n')[1].split()[1:]))
                        use_rate = float((1 - (line[2] + line[4] + line[5]) / line[0]) * 100)
                    if use_rate > max_value:
                        use_rate = "%.1f" % use_rate + '%'
                        with open(f'{self.temp_dir}/a_{filename}.md', 'a', encoding='utf-8') as f:
                            f.write(description.format(self.ip, use_rate) + '\n')
                elif command == '''grep "^SELINUX=" /etc/selinux/config''':
                    self.generator_a(filename, max_value)
                    current_value = data.split('=')[1].strip('\n')
                    if current_value != max_value:
                        with open(f'{self.temp_dir}/a_{filename}.md', 'a', encoding='utf-8') as f:
                            f.write(description.format(self.ip, current_value) + '\n')
                elif command == 'ulimit -n':
                    self.generator_a(filename, max_value)
                    current_value = int(data)
                    if current_value < max_value:
                        with open(f'{self.temp_dir}/a_{filename}.md', 'a', encoding='utf-8') as f:
                            f.write(description.format(self.ip, current_value) + '\n')
                elif command == 'crontab -l':
                    self.generator_a(filename, max_value)
                elif command == 'cat /etc/rc.local':
                    self.generator_a(filename, max_value)

        except Exception as e:
            logging.error(f'异常分析并生成MD错误,command:{command},filename:{filename}message:{e}')

# 数据汇总，将temp中的md 集中生成为2个MD，并转换为html
class Summary_data:
    def __init__(self, *args):
        self.temp_dir = temp_dir
        self.target_dir = target_dir
        self.alldata_name = alldata_name
        self.parse_rule = parse_rule
        self.command = command
        self.data_name = data_name
        self.html_dir = html_dir
        self.templates_path = templates_path

    def summary_normal(self):
        try:
            for filename in command.values():
                with open(f'{self.temp_dir}/{filename}.md', 'r', encoding='utf-8') as f, open(
                        f'{self.target_dir}/{self.alldata_name}.md', 'a', encoding='utf-8') as f2:
                    f2.write(f.read() + '\n')
        except Exception as e:
            logging.error(f'汇总md错误,message:{e}')

    def summary_abnormal(self):
        ivo = [x for x in self.parse_rule]
        extand_name = '巡检报告'
        ivo.insert(0, extand_name)
        for key in ivo:
            if key != extand_name:
                filename = command[key] + '.md'
            else:
                filename = extand_name + '.md'
                with open(f'{self.templates_path}/{filename}', 'r', encoding='utf-8') as f, open(
                        f'{self.temp_dir}/a_{filename}', 'w', encoding='utf-8') as f2:
                    f2.write(f.read().format(time.strftime('%Y/%m/%d  %H:%M:%S'), pc_count, err_pc_count, err_pc_list, alldata_name))

            with open(f'{self.temp_dir}/a_{filename}', 'r', encoding='utf-8')as f, open(
                    f'{self.target_dir}/{self.data_name}.md', 'a', encoding='utf-8') as f2:
                data = f.read()
                result = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", data.split('\n')[-2])
                if result or filename == '巡检报告.md':
                    f2.write(data + '\n')
                else:
                    f2.write(data)
                    if not result:
                        f2.write('所有服务器检查正常|' + '\n\n')

    def md_to_html(self):
        try:
            exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 'markdown.extensions.tables',
                    'markdown.extensions.toc']
            allmd = [self.alldata_name, self.data_name]
            with open(f'{self.templates_path}/css.css', 'r', encoding='utf-8') as css:
                css = css.read()
            with open(f'{self.templates_path}/frame.html', 'r', encoding='utf-8') as frame:
                frame = frame.read()
            for filename in allmd:
                with open(f'{self.target_dir}/{filename}.md', 'r', encoding='utf-8') as f:
                    markdownText = f.read()
                    h = markdown.markdown(markdownText, output_format='html5', extensions=exts)
                    with open(f'{self.html_dir}/{filename}.html', 'w', encoding='utf-8') as f1:
                        f1.write(frame.format(css, h, alldata_name + '.html', data_name + '.html'))
        except Exception as e:
            logging.error(f'Md_to_html异常,{e}')


if __name__ == '__main__':
    logging.info('开始执行')
    start_time = time.time()
    path.append(os.path.abspath('./') + '\\modules')
    basic_config = Basic_config()
    config = basic_config.get_config()
    target_dir = basic_config.get_out_md_dir()
    templates_path = basic_config.get_templates_path()
    temp_dir = basic_config.get_temp_dir()
    temp_templates = basic_config.get_temp_templates()
    html_dir = basic_config.get_out_html_dir()
    alldata_name = config.get('alldata_name')
    command = config['command']
    parse_rule = config['parser_rule']
    data_name = config['data_name']
    pcinfo = basic_config.get_pcinfo()
    q = multiprocessing.Manager().Queue()
    p = multiprocessing.Pool(multiprocessing.cpu_count())
    pc_count = len(pcinfo)
    for pcinfo in pcinfo:
        pcinfo = pcinfo.split()
        if len(pcinfo) == 5:
            generator_md = Generator_md(pcinfo[0], pcinfo[1], pcinfo[2], pcinfo[3], remarks=pcinfo[4])
        else:
            generator_md = Generator_md(pcinfo[0], pcinfo[1], pcinfo[2], pcinfo[3])
        p.apply_async(generator_md.get_data, args=())
    p.close()
    p.join()
    err_pc_count = q.qsize()
    err_pc_list = []
    while True:
        if q.empty():
            break
        else:
            err_pc_list.append(q.get())
    err_pc_list = '<br>'.join(err_pc_list)
    if not err_pc_list:
        err_pc_list = '无'
    summary_data = Summary_data()
    summary_data.summary_normal()
    summary_data.summary_abnormal()
    summary_data.md_to_html()

    # 发送邮件
    if config['sendmail']['enable'] is True:
        email_config = config['sendmail']
        sendmail.sendmail_initial(email_config, html_dir, data_name+'.html', alldata_name+'.html')
        # 打包为zip后再发送邮件
        # zip_name = config['zip_name']
        # sendmail.att_to_zip(f'{html_dir}', zip_name)
        # sendmail.sendmail_initial(email_config, html_dir, zip_name)
    endtime = time.time()
    print(f'耗时:{ endtime- start_time},日志请查看debug.txt')
    logging.info(f'耗时:{endtime - start_time}')