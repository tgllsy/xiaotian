# coding:utf8
import re
import threading


class Fingerprint:
    def __init__(self):
        self.finger = []
        self.lock = threading.Lock()

    def check_rule(self, key, header, body, title, icon):
        """检查指纹规则是否匹配"""
        try:
            if key['match'] == "icon_hash" and icon == key['content']:
                return True
            elif key['match'] == "title" and re.search(re.escape(key['content']), title):
                return True
            elif key['match'] == "body" and re.search(re.escape(key['content']), body):
                return True
            elif key['match'] == 'header' and re.search(re.escape(key['content']), str(header)):
                return True
        except Exception as e:
            # print(f"规则匹配出错: {e}")
            pass
        return False

    def handle(self, key, header, body, title, icon):
        """执行指纹识别"""
        try:
            name = key['name']
            for r in key['rules']:
                if isinstance(r, list):
                    if all(self.check_rule(line, header, body, title, icon) for line in r):
                        # 存在列表说明要匹配多个，且都成功
                        # 所有结果都对才证明指纹存在
                        # print("调试：匹配中指纹：{}，匹配规则：{} ".format(name, rule))
                        with self.lock:
                            self.finger.append(name)
                        return
                elif isinstance(r, dict) and self.check_rule(r, header, body, title, icon):
                    # 存在字典说明列表只需要命中一个即可成功
                    # self.finger.append(name)
                    # # print("调试：匹配中指纹：{}，匹配规则：{} ".format(name,rule))
                    # break
                    with self.lock:
                        self.finger.append(name)
                    return
        except Exception as e:
            print("处理出错了")
