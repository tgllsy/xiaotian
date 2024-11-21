# coding:utf8


def csv_output(scanner, workbook):
    # 表1：指纹识别
    sheet1 = workbook.active
    sheet1.title = "指纹识别"
    if sheet1.max_row == 1:
        headers = ['URL', 'Title', 'Status','Length', 'Icon', 'Finger']
        sheet1.append(headers)

    # 将指纹列表拼接成字符串
    finger = ",\n".join(scanner.finger)
    row = [scanner.url, scanner.title, scanner.status,scanner.length, scanner.icon, finger]
    sheet1.append(row)

    #
    # 检查 "重要信息" 工作表是否已存在，若不存在则创建
    if "重要信息" not in workbook.sheetnames:
        sheet2 = workbook.create_sheet("重要信息")
        headers2 = ["URL", "类型", "描述", "命中"]
        sheet2.append(headers2)
    else:
        sheet2 = workbook["重要信息"]

    if scanner.result:
        for rule in scanner.result:
            # hit_text = "\n".join(rule["hit"])
            for hit_text in rule["hit"]:
                row2 = [scanner.url, rule["type"], rule["describe"], hit_text]
                sheet2.append(row2)

    # 检查 "JS文件重要信息" 工作表是否已存在，若不存在则创建
    if "JS文件重要信息" not in workbook.sheetnames:
        sheet3 = workbook.create_sheet("JS文件重要信息")
        headers3 = ["URL", "JSpath", "类型", "描述", "命中"]
        sheet3.append(headers3)
    else:
        sheet3 = workbook["JS文件重要信息"]

    if scanner.js_result:
        for rule in scanner.js_result:
            jspath = rule['url']
            for _ in rule['result']:
                type = _["type"]
                describe = _["describe"]
                # hit = '\n'.join(_["hit"])
                for hit_text in _["hit"]:

                    row3 = [scanner.url, jspath, type, describe, hit_text]
                    sheet3.append(row3)
    return workbook
