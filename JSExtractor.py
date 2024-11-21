# coding:utf8
import re
import threading

import requests
from bs4 import BeautifulSoup

from Important import Important
from config import conf
from config.load import load_jsfinger


class JSExtractor:
    def __init__(self, url, content=None):
        """
        初始化 JSExtractor 对象
        :param url: 要分析的网页 URL
        :param content: 可选的网页 HTML 内容
        """
        self.url = url
        self.content = content
        self.js_paths = []
        self.headers = conf.requests_headers()
        self.js_files = []
        self.important = Important()
        self.result = []

    # def extract_URL(self,JS):
    #     print(JS)
    #     pattern_raw = r"""
    # 	  (?:"|')                               # Start newline delimiter
    # 	  (
    # 	    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    # 	    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    # 	    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
    # 	    |
    # 	    ((?:/|\.\./|\./)                    # Start with /,../,./
    # 	    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    # 	    [^"'><,;|()]{1,})                   # Rest of the characters can't be
    # 	    |
    # 	    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    # 	    [a-zA-Z0-9_\-/]{1,}                 # Resource name
    # 	    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    # 	    (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
    # 	    |
    # 	    ([a-zA-Z0-9_\-]{1,}                 # filename
    # 	    \.(?:php|asp|aspx|jsp|json|
    # 	         action|html|js|txt|xml)             # . + extension
    # 	    (?:\?[^"|']{0,}|))                  # ? mark with parameters
    # 	  )
    # 	  (?:"|')                               # End newline delimiter
    # 	"""
    #     pattern = re.compile(pattern_raw, re.VERBOSE)
    #     result = re.finditer(pattern, str(JS))
    #     if result == None:
    #         return None
    #     js_url = []
    #     print("日志 ：")
    #
    #     listaaa = [match.group().strip('"').strip("'") for match in result
    #                if match.group() not in js_url]
    #     print(listaaa)
    #     return listaaa

    def fetch_content(self):
        """ 获取网页内容
            如果不是初始化传进来的content，则可调用此方法get body。
        """
        try:
            requests.packages.urllib3.disable_warnings()  # 处理证书警告
            response = requests.get(self.url, headers=self.headers, verify=False, timeout=6)
            if response.status_code == 200:
                self.content = response.text
                # print(self.content)
        except Exception as e:
            pass
            # print(f"获取内容失败: {e}")

    def get_js_paths(self):
        """
        提取页面中的所有 JavaScript 文件路径
        """
        if not self.content:
            self.fetch_content()

        if not self.content:
            return []

        soup = BeautifulSoup(self.content, 'html.parser')
        # print(soup)
        # 提取 <script> 标签中的 src 属性，只保留 .js 文件
        script_tags = soup.find_all('script', src=True)
        js_paths = [script['src'] for script in script_tags if script['src'].endswith('.js')]

        # 提取 <link> 标签中的 href 属性，只保留 .js 文件，忽略 .css 文件
        link_tags = soup.find_all('link', href=True)
        js_links = [
            link['href'] for link in link_tags
            if link['href'].endswith('.js') and 'rel' in link.attrs and
               ('preload' in link['rel'] or 'prefetch' in link['rel'] or 'module' in link['rel'])
        ]
        js_paths.extend(js_links)

        # 使用正则表达式在整个页面内容中查找内联 JS 文件路径，只保留 .js 文件
        pattern = re.compile(r'(?:src|href)=["\']([^"\']+\.js)["\']', re.IGNORECASE)
        inline_js_paths = pattern.findall(self.content)
        js_paths.extend(inline_js_paths)

        # 去重并转换相对路径为绝对路径
        self.js_paths = list(set(self.make_full_url(path) for path in js_paths if path))
        # print(self.js_paths)
        return self.js_paths

    def make_full_url(self, src):
        """
        将相对路径转换为绝对路径
        """
        if src.startswith(('http://', 'https://')):
            return src
        elif src.startswith('/'):
            return f"{self.url.rstrip('/')}{src}"
        else:
            return f"{self.url.rstrip('/')}/{src}"

    def print_js_paths(self):
        """
        打印提取到的 JavaScript 文件路径
        """
        js_paths = self.get_js_paths()
        # print(js_paths)
        if js_paths:
            print("发现以下 JavaScript 文件路径:")
            for path in js_paths:
                print(path)
        else:
            print("未找到 JavaScript 文件路径")

    def fetch_js_content(self, js_url):
        """下载 JavaScript 文件的内容"""
        try:
            requests.packages.urllib3.disable_warnings()  # 处理证书警告
            response = requests.get(js_url, headers=self.headers, timeout=6, verify=False)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            pass
            # logger.error(f"下载 JS 文件失败: {js_url}, 错误: {e}")
        return None

    def process_js_files(self):
        """获取 JS 文件并运行指纹识别"""
        # 提取 JS 文件路径
        try:
            if self.content is None:
                return

            js_paths = self.get_js_paths()
            if not js_paths:
                # logger.info("未找到 JavaScript 文件")
                return

            # 下载所有 JS 文件内容
            for js_path in js_paths:
                content = self.fetch_js_content(js_path)
                if content:
                    dicts = {
                        'url': js_path,
                        'content': content
                    }

                    self.js_files.append(dicts)
        except Exception as e:
            return None

    def find_important(self):

        jsresult = load_jsfinger()
        result = jsresult['fingerprint'][0:-3]

        self.process_js_files()
        # print("读取成功了吗")
        # print(self.js_files)
        if not self.js_files:
            return []

        threads = []
        for js in self.js_files:
            content = js['content']
            for rule in result:
                # 匹配指纹，成功则返回
                t = threading.Thread(target=self.important.process_fingerprint,
                                     args=(rule, content))
                threads.append(t)
                t.start()

            # 等待所有线程完成
            for t in threads:
                t.join()

            if self.important.result:
                self.result.append({'url': js['url'], 'result': self.important.result.copy()})
            self.important.result.clear()
        # print(self.result)
        return self.result


if __name__ == '__main__':
    url = "https://r.zelo.facebeacon.com/"
    jsresult = load_jsfinger()
    result = jsresult['fingerprint'][0:-3]

    js = JSExtractor(url)
    js.fetch_content()
    # for j in js.js_paths:
    #     js.extract_URL(js.js_paths)

    aaa = js.find_important()

    for line in aaa:
        print(line['url'])
        for rule in line.get('result', []):
            print(f'{rule["type"]}-{rule["describe"]}:{rule["hit"]}')

    # for x in js.js_paths:
    #
    #     js.extract_URL(x)
