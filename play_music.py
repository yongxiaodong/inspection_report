# -*- coding: utf-8 -*-
import os
from random import choice
from time import sleep
from pygame import mixer
from mutagen.mp3 import MP3
import logging
import yaml

logging.basicConfig(filename='./debug.txt', format='[%(levelname)s %(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO,filemode='a')
def basic_config(config='config.yml'):
    if not os.path.exists(config):
        with open(config,w,encoding='utf-8') as f:
            f.write('file_path: E:\CloudMusic')
    else:
        with open(config,'r',encoding='utf-8') as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
            return config
def get_music(file_path):
    try:
        music = []
        if os.path.exists(file_path):
            for dirpath, dirnames, filenames in os.walk(file_path):
                for filename in filenames:
                    if os.path.splitext(filename)[1] == '.mp3':
                        filepath = os.path.join(dirpath, filename)
                        music.append(filepath)
                        return music
        else:
            raise Exception(f'{file_path}目录不存在')
    except Exception as e:
        logging.error(f'读取music失败,message:{e}')
def random_play(music):
    try:
        if music:
            random_music = choice(music)
            mixer.init()
            T = MP3(random_music).info.length
            logging.info(f'即将播放歌曲:{random_music},歌曲时长:{T}')
            mixer.music.load(random_music)
            mixer.music.play(loops=0, start=0.0)
            sleep(int(T))
            logging.info(f'播放歌曲结束:{random_music}')
        else:
            raise Exception('Music Not Found,没有找到.mp3的音乐')
    except Exception as e:
        logging.error(f'播放失败,message:{e}')
if __name__ == '__main__':
    config = basic_config()
    print(config)
    music = get_music('E:\CloudMusic\/')
    random_play(music)
