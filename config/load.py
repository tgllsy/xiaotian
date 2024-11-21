import json

from . import conf
import os
finger_file = conf.finger_file
js_file = conf.js_file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def load_finger():
    """加载指纹文件"""
    try:
        with open(BASE_DIR+finger_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("指纹文件不存在")
    except json.JSONDecodeError as e:
        print(f"指纹文件格式错误: {e}")
        exit()

def load_jsfinger():
    """加载js指纹文件"""
    try:
        with open(BASE_DIR+js_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("指纹文件不存在")
    except json.JSONDecodeError as e:
        print(f"指纹文件格式错误: {e}")
        exit()