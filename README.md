# Handbrake2VMAF

平日里有使用[Handbrake](https://handbrake.fr/)转码视频的需求，但是靠肉眼很难区分转码效果的好坏。[VMAF](https://github.com/Netflix/vmaf)是由Netflix开发的感知视频质量评估算法，它是通过预训练模型对视频进行主观质量评价的。VMAF评估结束后会给出一个0到100的分数，95分以上可以认为和原片观感一样，而98分以上可以认为和原片几乎无法区分。

因此我编写了这个脚本，让Handbrake在转码结束后自动调用这个脚本，分析输出文件的质量，并通过Email提醒我结果。

本脚本基于[ab-av1](https://github.com/alexheretic/ab-av1)项目，这是一个使用Rust编写的视频编码工具，其主要用途是将视频重编码为av1格式，但是它也拥有计算VMAF分数的功能，且具有自动识别视频分辨率等方便的功能，用起来很方便。

## 功能列表

本脚本具有以下功能：
- 以VMAF值的形式评估视频转码效果。
- 通过Email的形式通知用户评估结果。
- 作为Handbrake的后处理脚本，自动对转码完成的视频进行评估。

## 快速开始

### 安装依赖

1. Python 3.6+
2. `pip install -r requirements.txt`
3. FFmpeg([下载链接](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z))，下载完成需将FFmpeg的执行路径加入环境变量

### 运行示例

运行示例：
```
python ./vmaf.py -r ${源视频路径} -d ${转码后视频路径}
```

Windows可以下载打包好的可执行文件，运行示例：
```
./vmaf.exe -r ${源视频路径} -d ${转码后视频路径}
```

### 配置文件

配置文件`config.toml`目前只用于配置smtp服务相关信息，格式如下：
```toml
[smtp]
enable = false      # smtp服务启动开关，默认为false,，启动请改为true
server = ""         # smtp服务器地址，如smtp.163.com
port = 25           # smtp服务器端口
sender = ""         # 发件人账号，如12345678#163.com
password = ""       # 发件人密码，详见服务提供商文档
receiver = ""       # 收件人账号，如87654321#163.com
name_sender = ""    # 发件人名称，对人类友好的称呼，如管理员
name_receiver = ""  # 收件人名称，对人类友好的称呼，如系统用户
```
如需开启邮件提醒，请将`enable`的值修改为`true`，并将内容填写完整。

### 配置HandBrake
以打包好的可执行文件为例。

打开`工具 - 首选项 - 当完成时`，在右侧的**编码完成**部分勾选`发送文件至`，并点击`浏览`按钮，找到并选择`vmaf.exe`可执行文件，最后在下方的参数栏中输入`-r {source} -d {destination}`即可。

## 碎碎念
说到底在确定了一个转码参数后，生成的文件效果都大差不差，因此这个脚本没有太大的日常使用价值，更多的应该是适用于调试转码参数，或者强迫症吧（逃

以及这个脚本大部分内容都是ChatGPT生成的（悲
