
# 哮天犬
一款使用python开发的可以识别web指纹和获取页面及js重要信息的工具。

至于为啥不支持跑js路径和api接口的功能，我感觉市面上比我写的成熟的工具多的是，git上就有一大堆，不重复造轮子

## 使用
开发环境： python3.13 ，旧版本可能有bug

```shell
帮助
python.exe .\xiaotiandog.py -h 
usage: xiaotiandog.py [-h] [-u URL | -f FILE] [-i] [-j] [-o]

options:
  -h, --help       show this help message and exit
  -u, --url URL    从url读取
  -f, --file FILE  从文件读取
  -i, --important  获取重要信息
  -j, --js         从js中获取重要信息
  -o, --output     输出excel文件

只扫描指纹
python.exe .\xiaotiandog.py -u http://xxx.com/ 

扫描指纹和body中的重要信息
python.exe .\xiaotiandog.py -u http://xxx.com/ -i

扫描指纹，body和js中的重要信息
python.exe .\xiaotiandog.py -u http://xxx.com/ -i -j 

保存文件

python.exe .\xiaotiandog.py -f 1.txt  -o 
python.exe .\xiaotiandog.py -f 1.txt  -o -i -j 

```
不需要跑指纹，只需要跑js的只要运行`JSExtractor.py` 文件便可


![](\image\1.png)

## 已知问题
1. 未采用线程队列Queue处理结果，可能会出现一些问题，~~大概、也许可能吧。~~
2. 字典直接搬来用的，误报，错误，不匹配等问题很常见，还没做优化。
3. 从文件里获取url跑js匹配，如果量太大（实测1w条url）的话一天都跑不完。虽然能批量跑，但是还是建议不要跑太多条

## 下一步
1. 改造成分布式工具，以提高性能（不一定）
2. 增加对vue 里的 chunk.*.js 的识别并自动扫描

# 参考

指纹1：https://github.com/0x727/FingerprintHub?tab=readme-ov-file

重要信息指纹： https://github.com/shuanx/BurpAPIFinder/blob/main/src/main/resources/conf/finger-important.json

https://github.com/TideSec/TideFinger


