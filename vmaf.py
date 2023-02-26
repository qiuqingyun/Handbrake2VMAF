import argparse, subprocess, signal, os, smtplib, toml, traceback, sys, logging, time
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr


def main(args):
    global path_workdir
    path_reference = args.reference
    path_distorted = args.distorted
    filename = os.path.basename(path_distorted)
    logger.info('Video "' + filename + '"')
    logger.info("Reference path: " + path_reference)
    logger.info("Distorted path: " + path_distorted)
    create_config_file()
    try:
        # 启动子程序，stdout和stderr被重定向到管道
        cmd = [
            os.path.join(path_workdir, "ab-av1.exe"),
            "vmaf",
            "--reference",
            path_reference,
            "--distorted",
            path_distorted,
        ]
        logger.debug('Execute command "' + " ".join(str(x) for x in cmd) + '"')
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info("Inspection start")
        start_time = time.time()
        # 等待子进程完成并获取stdout和stderr的输出
        stdout, stderr = process.communicate()
        end_time = time.time()
        logger.info("Inspection complete")
        # 将输出存储在变量中
        output = stdout.decode().strip()
        # 计算花费的时间
        run_time = end_time - start_time

        # 输出结果
        logger.info("VMAF: " + output)
        logger.info("Took " + str(run_time) + " s")
        subject = "VMAF | 视频 " + filename + " 检测完毕，" + score_to_quality(float(output))
        text = """
        VMAF结果: {0}
        检测用时: {1}
        输入路径: {2}
        输出路径: {3}
        """.format(
            output,
            format_duration(run_time),
            path_reference,
            path_distorted,
        )
        # 发送邮件
        send_email(subject, text)
    except KeyboardInterrupt:
        process.send_signal(signal.CTRL_BREAK_EVENT)
        logger.info("Interrupted manually by the user")
        input("The process has been terminated, press Enter to exit the script...")
    except Exception as e:
        # 处理异常
        logger.exception(e)
        logger.info("Inspection failed")
        input("The process has been terminated, press Enter to exit the script...")
    finally:
        logger.info("========================")

# 发送邮件
def send_email(subject, text):
    global path_workdir
    # 从 TOML 配置文件中读取 SMTP 服务器的参数
    with open(os.path.join(path_workdir, "config.toml"), "r") as f:
        config = toml.load(f)
    enable = config["smtp"]["enable"]
    smtp_server = config["smtp"]["server"]
    smtp_port = config["smtp"]["port"]
    sender = config["smtp"]["sender"]
    password = config["smtp"]["password"]
    receiver = config["smtp"]["receiver"]
    name_sender = config["smtp"]["name_sender"]
    name_receiver = config["smtp"]["name_receiver"]
    # 判断是否填写了关键信息
    if (
        not enable
        or len(smtp_server) == 0
        or len(sender) == 0
        or len(password) == 0
        or len(receiver) == 0
    ):
        logger.info("Email not sent")
        return

    # 构造 MIMEText 对象
    message = MIMEText(text, "plain", "utf-8")
    message["From"] = formataddr((Header(name_sender, "utf-8").encode(), sender))
    message["To"] = formataddr((Header(name_receiver, "utf-8").encode(), receiver))
    message["Subject"] = Header(subject, "utf-8")

    # 连接邮件服务器
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)

    # 发送邮件
    server.sendmail(sender, receiver, message.as_string())

    # 关闭连接
    server.quit()

    logger.info("Email sent")


# 格式化分数
def score_to_quality(score):
    if score >= 98:
        return "质量完美"
    elif score >= 95:
        return "质量很好"
    elif score >= 90:
        return "质量不错"
    elif score >= 80:
        return "质量一般"
    else:
        return "质量较差"


# 获取脚本所在的路径
def get_script_path():
    if getattr(sys, "frozen", False):  # 检查是否已经打包成exe
        # 如果已经打包成exe，则返回exe所在的路径
        return os.path.dirname(sys.executable)
    else:
        # 如果没有打包成exe，则返回脚本所在的路径
        return os.path.dirname(os.path.realpath(__file__))


# 格式化时间
def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    if hours:
        if minutes and seconds:
            return f"{hours}小时{minutes:02d}分钟{seconds:02d}秒"
        elif seconds:
            return f"{hours}小时{seconds:02d}秒"
        elif minutes:
            return f"{hours}小时{minutes:02d}分钟"
        else:
            return f"{hours}小时"
    elif minutes:
        if seconds:
            return f"{minutes}分钟{seconds:02d}秒"
        else:
            return f"{minutes}分钟"
    else:
        return f"{seconds}秒"


# 检查配置文件
def create_config_file():
    global path_workdir
    config_file = os.path.join(path_workdir, "config.toml")
    if not os.path.exists(config_file):
        config = {
            "smtp": {
                "server": "",
                "port": 25,
                "sender": "",
                "password": "",
                "receiver": "",
                "name_sender": "",
                "name_receiver": "",
            }
        }
        with open(config_file, "w") as f:
            f.write(toml.dumps(config))


# 脚本的工作目录
path_workdir = os.path.abspath(get_script_path())

# 日志设置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 创建一个控制台输出handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# 创建一个文件输出handler
path_log_dir = os.path.join(path_workdir, "log")
if not os.path.exists(path_log_dir):
    os.makedirs(path_log_dir)
path_log_file = os.path.join(
    path_log_dir, datetime.today().strftime("%Y_%m_%d") + ".log"
)
file_handler = logging.FileHandler(
    path_log_file,
    encoding="utf-8",
    mode="a",
)
file_handler.setLevel(logging.INFO)
# 设置日志输出格式
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
# 将handler添加到logger中
logger.addHandler(console_handler)
logger.addHandler(file_handler)


if __name__ == "__main__":
    # 创建解析器对象
    parser = argparse.ArgumentParser()
    # 添加参数
    parser.add_argument(
        "-r", "--reference", help="the path of the reference video", required=True
    )
    parser.add_argument(
        "-d", "--distorted", help="the path of the distorted video", required=True
    )
    # 解析参数
    args = parser.parse_args()
    main(args)
