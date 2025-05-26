# meta_human

## 设置开发环境
创建虚拟环境，以免把自己电脑里面的配置搞乱，使用`python3 -m venv .`命令。
`-m`的意思是调用某某python模块，`venv`就是生成virtual environment的功能模块，`.`表示在当前目录生成，当然也可以写其他的目录。

## 进入虚拟环境
`source bin/activate`，可能在Windows上略有区别

## 安装依赖
进入虚拟环境后，`pip install -r requirements.txt`即可，如果遇到网络问题，就加入一个参数`-i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`调用清华源来下载。

## 退出虚拟环境
`deactivate`命令即可，Windows上可能略有区别