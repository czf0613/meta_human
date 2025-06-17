class User:
    id: int
    username: str
    password: str

# SQL Alchemy
# /path/to/your/file.txt
# /path/to/file.mp3
# 实际上在文件系统里，这俩玩意丢一块都没问题，甚至连名字叫啥都不要紧
# 非结构化的对象存储的实现

# 列出文件夹内的文件，字符串前缀为/path/to/
# ...
#    your/
#        file.txt
#    file.mp3
# 
# 实际上，存储的文件是平面的，只不过它的所谓的“key”可以通过斜杠来拆分而已