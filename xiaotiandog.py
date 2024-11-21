# coding:utf8
import argparse
import base64
import logging
import threading
import time
import mmh3
import openpyxl
import requests

from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

from Important import Important
from JSExtractor import JSExtractor
from config import conf
from config.load import load_finger, load_jsfinger
from fingerprint import Fingerprint
from output import csv_output

lock = threading.Lock()

logging.basicConfig(level=logging.INFO, format='%(asctime)s- %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Scanner:
    def __init__(self, url, ):
        """初始化信息"""
        self.fingerprint = Fingerprint()  # 加载指纹识别模块
        self.important = Important()  # 加载敏感信息识别模块
        self.headers = conf.requests_headers()  # 获取请求头

        self.url = url
        self.header = {}
        self.title = ''
        self.status = 0
        self.length = 0
        self.content = ''
        self.icon = ''

        self.finger = []  # 指纹
        self.result = []  # 重要信息
        self.js_result = []  # js中的敏感信息

    def get_content(self):
        return self.content

    def get_body(self):
        """获取 head头 ,content内容 ,title"""
        try:
            requests.packages.urllib3.disable_warnings()  # 处理证书警告
            rqs = requests.get(url=self.url, headers=self.headers, verify=False, timeout=6, allow_redirects=False)

            # 如果状态码是302，则手动获取重定向的 URL
            if rqs.status_code == 302:
                redirect_url = rqs.headers.get('Location')
                # print(f"302跳转到: {redirect_url}")
                # 处理跳转后的URL
                return self.get_redirected_body(redirect_url)

            if rqs.encoding is None or rqs.encoding.lower() == 'iso-8859-1':
                rqs.encoding = rqs.apparent_encoding

            content = rqs.text
            self.content = content
            self.headers = rqs.headers
            self.status = rqs.status_code
            self.length = len(content)
            if not content:
                raise ValueError("响应内容为空")
            try:
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    self.title = soup.title.string
            except Exception as e:
                logger.debug(f"{e},{self.url}")
                # print(f"BeautifulSoup解析错误: {e,self.url}")
        except Exception as e:
            logger.debug(f"{e}")
            # print(f"请求或解析错误: {e,self.url}")

    def get_redirected_body(self, redirect_url):
        """
        处理跳转后的URL，发起请求获取跳转后的 header 和 body
        :param redirect_url: 跳转后的 URL
        :return: 跳转后的 header 和 body 内容
        """
        try:
            # print(f"正在请求跳转 URL: {redirect_url}")
            rqs = requests.get(url=redirect_url, headers=self.headers, verify=False, timeout=6)

            if rqs.encoding is None or rqs.encoding.lower() == 'iso-8859-1':
                rqs.encoding = rqs.apparent_encoding
            content = rqs.text
            self.content = content
            self.headers = rqs.headers
            self.status = rqs.status_code
            self.url = redirect_url
            self.length = len(content)
            if not content:
                raise ValueError("响应内容为空")
            # 获取跳转后的页面的标题和内容
            soup = BeautifulSoup(content, 'html.parser')
            self.title = soup.title.string
            # print(f"跳转后的标题: {self.title}")
            # print(f"跳转后的状态码: {self.status}")
        except Exception as e:
            pass
            # print(f"跳转请求或解析错误: {e}")

    def get_icon_hash(self):
        """
        获取网页icon
        :return:
        """
        try:
            requests.packages.urllib3.disable_warnings()
            url = self.url + '/favicon.ico'
            rsp = requests.get(url=url, headers=self.headers, verify=False, timeout=6)
            r2 = base64.encodebytes(rsp.content)
            self.icon = str(mmh3.hash(r2))
        except Exception as e:
            # print(f"获取 favicon 失败: {e}")
            self.icon = ''

    def runFinger(self):
        """运行指纹识别模块"""

        result = load_finger()  # 获取指纹列表
        self.get_icon_hash()
        self.get_body()

        # print("如果有内容")
        if self.status is not None and self.status != 0:
            threads = []
            for rule in result:
                t = threading.Thread(target=self.fingerprint.handle,
                                     args=(rule, self.header, self.content, self.title, self.icon))
                threads.append(t)
                t.start()

            # 等待所有线程完成
            for t in threads:
                t.join()
            self.finger.extend(self.fingerprint.finger)

    def run_find_important(self):
        """运行 JS 指纹扫描"""
        if self.important is None:
            return

        threads = []
        jsresult = load_jsfinger()
        result = jsresult['fingerprint'][0:-3]

        content = str(self.header) + str(self.content)
        for rule in result:
            t = threading.Thread(target=self.important.process_fingerprint, args=(rule, content))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.result.extend(self.important.result)

    def run_find_js(self):
        """查找js里的敏感信息"""

        js = JSExtractor(self.url, content=self.content)
        important_data = js.find_important()
        self.js_result = important_data
        return self.js_result

    def printFinger(self):
        if self.status is not None and self.status != 0:
            logger.info(
            f"url: {self.url}\t title: {self.title}\tlength:{self.length} \ticon:{self.icon}\tstatus: {self.status},指纹:{self.finger}")
        else:
            logger.info(f"url: {self.url}, 访问失败 ")
        if self.result:
            for rule in self.result:
                logger.info(f'敏感信息 -> {rule["type"]}-{rule["describe"]}: {rule["hit"]}')
        if self.js_result:
            for rule in self.js_result:
                for hit in rule['result']:
                    logger.info(f'js链接：{rule['url']} ->{hit["type"]}-{hit["describe"]}: {hit["hit"]}')


def banner():
    print(f"""                                                                                                          
                     iiii                                          tttt           iiii                                   
                    i::::i                                      ttt:::t          i::::i                                  
                     iiii                                       t:::::t           iiii                                   
                                                                t:::::t                                                  
xxxxxxx      xxxxxxiiiiiii  aaaaaaaaaaaaa    ooooooooooo  ttttttt:::::ttttttt   iiiiiii  aaaaaaaaaaaaa nnnn  nnnnnnnn    
 x:::::x    x:::::xi:::::i  a::::::::::::a oo:::::::::::oot:::::::::::::::::t   i:::::i  a::::::::::::an:::nn::::::::nn  
  x:::::x  x:::::x  i::::i  aaaaaaaaa:::::o:::::::::::::::t:::::::::::::::::t    i::::i  aaaaaaaaa:::::n::::::::::::::nn 
   x:::::xx:::::x   i::::i           a::::o:::::ooooo:::::tttttt:::::::tttttt    i::::i           a::::nn:::::::::::::::n
    x::::::::::x    i::::i    aaaaaaa:::::o::::o     o::::o     t:::::t          i::::i    aaaaaaa:::::a n:::::nnnn:::::n
     x::::::::x     i::::i  aa::::::::::::o::::o     o::::o     t:::::t          i::::i  aa::::::::::::a n::::n    n::::n
     x::::::::x     i::::i a::::aaaa::::::o::::o     o::::o     t:::::t          i::::i a::::aaaa::::::a n::::n    n::::n
    x::::::::::x    i::::ia::::a    a:::::o::::o     o::::o     t:::::t    tttttti::::ia::::a    a:::::a n::::n    n::::n
   x:::::xx:::::x  i::::::a::::a    a:::::o:::::ooooo:::::o     t::::::tttt:::::i::::::a::::a    a:::::a n::::n    n::::n
  x:::::x  x:::::x i::::::a:::::aaaa::::::o:::::::::::::::o     tt::::::::::::::i::::::a:::::aaaa::::::a n::::n    n::::n
 x:::::x    x:::::xi::::::ia::::::::::aa:::oo:::::::::::oo        tt:::::::::::ti::::::ia::::::::::aa:::an::::n    n::::n
xxxxxxx      xxxxxxiiiiiiii aaaaaaaaaa  aaaa ooooooooooo            ttttttttttt iiiiiiii aaaaaaaaaa  aaaannnnnn    nnnnnn

指纹识别工具：哮天犬  --version: 0.1  指纹数量:{ len(load_finger())}     --author: tgllsy-CatXicure      使用 -h 获取帮助                                                                                
    """)


def process_url(url: str, finger: bool = False, fingejs: bool = False, workbook=None):
    """处理单个 URL"""

    scanner = Scanner(url)
    scanner.runFinger()
    if finger:
        scanner.run_find_important()
    if fingejs:
        scanner.run_find_js()
    scanner.printFinger()
    if workbook is not None:
        csv_output(scanner, workbook)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u', '--url', help='从url读取')
    group.add_argument('-f', '--file', help='从文件读取')
    parser.add_argument('-i', '--important', action='store_true', help='获取重要信息')
    parser.add_argument('-j', '--js', action='store_true', help='从js中获取重要信息')
    parser.add_argument('-o', '--output', action='store_true', help='输出excel文件')
    args = parser.parse_args()

    print("目前指纹条数：", len(load_finger()))

    if args.url:
        process_url(args.url, args.important, args.js)
        exit()
    #
    if args.file:
        with open(args.file, encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
            print(f"当前url数量{len(urls)} \n")

        # 定义需要传递的布尔参数
        finger = args.important  # 是否执行指纹重要性识别
        fingejs = args.js  # 是否执行 JS 文件指纹扫描

        workbook = openpyxl.Workbook() if args.output else None  # 是否保存数据

        with ThreadPoolExecutor(max_workers=100) as executor:
            # 使用 submit 方法传递多个参数
            futures = [
                executor.submit(process_url, url, finger, fingejs, workbook)
                for url in urls
            ]

        if args.output:
            # 如果选择了输出Excel，保存工作簿
            outfile = f'result\指纹识别-{time.strftime("%Y-%m-%d-%H-%M", time.localtime(time.time()))}.xlsx'
            workbook.save(outfile)
            print(f"所有 URL 处理完毕，数据已成功导出为 Excel 文件: {outfile}")
            exit()
        print("所有 URL 处理完毕！")
        exit()
    else:
        banner()
        exit()
