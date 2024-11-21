#coding:utf8
import re
import threading


class Important:
    def __init__(self):
        self.lock = threading.Lock()
        self.result = []

    def extract_context(self, content, pattern, context_range_before=10, context_range_after=20):
        """
        使用正则表达式提取匹配的上下文。
        :param content: 要匹配的内容
        :param pattern: 正则表达式
        :param context_range_before: 匹配前获取的字符数
        :param context_range_after: 匹配后获取的字符数
        :return: 匹配的上下文列表
        """
        context_list = []
        try:
            matches = re.finditer(pattern, content)
            for match in matches:
                # start, end = match.span()
                # before = content[max(0, start - context_range_before):start]
                # after = content[end:end + context_range_after]
                # context = f"{before}{match.group(0)}{after}"
                context = match.group(0)
                context_list.append(context)
        except re.error as e:
            print(f"无效的正则表达式: {pattern}, 错误: {e}")
        return context_list

    def check_regular_match(self, key, content):
        """检查正则匹配（body location 和 regular match）。"""
        context_list = []
        for pattern in key['keyword']:
            context_list.extend(self.extract_context(content, pattern))
        return context_list

    def check_keyword_match(self, key, content):
        """检查关键字匹配（body location 和 keyword match）。"""
        context_list = []
        if all(re.search(re.escape(k), content) for k in key['keyword']):
            for k in key['keyword']:
                match = re.search(re.escape(k), content)
                if match:
                    # start, end = match.span()
                    # before = content[max(0, start - 10):start]
                    # after = content[end:end + 30]
                    # context = f"{before}{k}{after}"
                    context = k
                    context_list.append(context)
        return context_list


    def check_rule(self, key, content):
        """
        根据规则匹配类型返回匹配结果。
        :param key: 匹配规则
        :param content: 内容（header + body）
        :return: 匹配的上下文列表
        """
        context_list = []
        if key['location'] == "body":
            if key['match'] == "regular":
                context_list = self.check_regular_match(key, content)
            elif key['match'] == "keyword":
                context_list = self.check_keyword_match(key, content)
        return context_list

    def process_fingerprint(self, result,content):

        """执行指纹识别"""

        with self.lock:
            line = self.check_rule(result, content)
            if line:
                result['hit'] = line
                self.result.append(result)

