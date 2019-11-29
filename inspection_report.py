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

logging.basicConfig(filename='debug.txt', format='[%(levelname)s %(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.ERROR, filemode='w')


class Check_dir_status:
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
        #加载config.yml
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.load(f.read(), Loader=yaml.FullLoader)
        except Exception as e:
            logging.error(f'加载配置文件{self.config_file}失败,message:{e}')


    def get_config(self):
        return self.config

    def get_out_md_dir(self):
        try:
            out_md_dir = config['out_md_dir']
            if not os.path.exists(out_md_dir):
                os.mkdir(out_md_dir)
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
            return out_html_dir
        except KeyError as e:
            logging.error(f'获取key:out_html_dir，message:{e}')
        except Exception as e:
            logging.error(f'获取out_html_dir目录失败，message:{e}')

    def get_pcinfo(self):
        # 获取pcinfo
        try:
            pcinfo = config['pcinfo']
            with open(pcinfo, 'r', encoding='utf-8') as f:
                pcinfo = f.read()
                return pcinfo.split('\n')
        except Exception as e:
            logging.error(f'加载{pcinfo}文件失败,message:{e}')

    def get_templates_path(self):
        try:
            templates_path = config['templates']
            return templates_path
        except Exception as e:
            logging.error(f'获取templates_path失败,message:{e}')


class Ssh:
    """该类执行命令并返回结果"""

    def __init__(self, ip, port, user, password, command, remarks='', ssh_timeout=5, execute_timeout=20):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.command = command
        self.remarks = remarks
        self.ssh_timeout = ssh_timeout
        self.execute_timeout = execute_timeout

    def execute_command(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, self.port, self.user, self.password, timeout=self.ssh_timeout)
            for command, filename in self.command.items():
                stdin, stdout, stderr = ssh.exec_command(command, timeout=self.execute_timeout)
                response_out = stdout.read().decode('utf-8')
                yield response_out, filename
        except paramiko.ssh_exception.AuthenticationException as e:
            logging.error(f'{self.ip},密码验证错误', {e})
        except socket.timeout as e:
            logging.error(f'{self.ip},链接超时,{e}')
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            logging.error(f'{self.ip},端口链接失败,{e}')
        except Exception as e:
            logging.error(f'未知异常,{traceback.print_exc()},{e}')


class Generator_md(Ssh):
    """操作Markdown、控制生成Markdown、Markdown转HTML"""
    def __init__(self, ip, port, user, password, command, target_dir, templates_path, remarks='', ssh_timeout=5,
                 execute_timeout=20):
        super().__init__(ip, port, user, password, command, remarks, ssh_timeout, execute_timeout)
        self.target_dir = target_dir
        self.templates_path = templates_path

    def get_data(self):
        for data, filename in self.execute_command():
            data = re.sub('\n', '<br>', data)
            data = re.sub(' ', '&nbsp;', data)
            self.generator_md(data, filename)

    def generator_md(self, data, filename):
        try:
            status = 0
            if data:
                if not os.path.exists(f'{self.target_dir}/{filename}.md'):
                    if os.path.exists(f'{self.templates_path}/{filename}.md'):
                        shutil.copy(f'{self.templates_path}/{filename}.md', f'{self.target_dir}/{filename}.md')
                        status = 1
                    else:
                        logging.error(f'当前处理ip:{self.ip},从{self.templates_path}获取模板{filename}.md失败')
                else:
                    status = 1
                if status == 1:
                    with open(f'{self.target_dir}/{filename}.md', 'a', encoding='utf-8') as f:
                        data = re.sub('\n', '<br>', data)
                        f.write(f'{self.ip} | {data}' + '\n')
        except Exception as e:
            logging.error(e)

    # def data_parser(self):
    #     if self.filename == self.configfile['judge1']:
    #     diskname = succ.split()
    #     reresu = re.findall('\d{1,3}%', succ)
    #     usedisk = list(map(self.delete_percent, reresu))
    #     if reresu and int(usedisk[0]) > self.configfile['diskthreshold']:
    #         write_disk_name += '{0} : {1}<br>'.format(diskname[-1], diskname[-2])
    #         idx += 1

    def md_to_html(self):
        try:
            exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 'markdown.extensions.tables',
                    'markdown.extensions.toc']
            with open('内存.md', 'r', encoding='utf-8') as f:
                markdownText = f.read()
                h = markdown.markdown(markdownText, output_format='html5', extensions=exts)
                print(h)
                with open('内存.html', 'w', encoding='utf-8') as f1:
                    f1.write(h)
        except Exception as e:
            logging.error(f'Md_to_html异常,{e}')


if __name__ == '__main__':
    start_time = time.time()
    basic_config = Basic_config()
    config = basic_config.get_config()
    out_md_dir = basic_config.get_out_md_dir()
    templates_path = basic_config.get_templates_path()
    command = config['command']
    pcinfo = basic_config.get_pcinfo()
    p = Pool(4)
    for pcinfo in pcinfo:
        pcinfo = pcinfo.split()
        print(pcinfo)
        if len(pcinfo) == 4:
            generator = Generator_md(pcinfo[0], pcinfo[1], pcinfo[2], pcinfo[3], command, out_md_dir, templates_path, remarks=pcinfo[4])
        else:
            generator = Generator_md(pcinfo[0], pcinfo[1], pcinfo[2], pcinfo[3], command, out_md_dir, templates_path)
        p.apply_async(generator.get_data, args=())
        # generator.get_data()
    p.close()
    p.join()
    endtime = time.time()
    print(f'耗时:{start_time - endtime}')

