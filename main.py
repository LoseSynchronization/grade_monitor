import pprint
import threading
import time
from logging import Logger

import yaml

from monitor import GradeMonitor
from notice import MailNotice
from utils import mylogger
from utils.BaiduOcr import BaiduOcr

userList = [{
    'stu_code': '1520182520',
    'vpn_password': 'wsq.20001005.pq.3Q',
    'email': '754523314@qq.com'
}, {
    'stu_code': '1520182524',
    'vpn_password': '000000',
    'email': '1156604022@qq.com'
}]

LOGGER: Logger = mylogger.Logger("main").get_log()


class MonitorThread(threading.Thread):
    def __init__(self, monitor: GradeMonitor, interval, user_id):
        super().__init__()
        self.__interval = interval
        self.setName("GradeMonitor({})".format(user_id))
        self.__monitor: GradeMonitor = monitor
        self.__count = 0

    def run(self) -> None:
        while True:
            self.__count += 1
            LOGGER.info("{}: 开始执行第{}次任务".format(self.getName(), self.__count))
            try:
                self.__monitor.check_grade()
                LOGGER.info("{}: 第{}次任务结束".format(self.getName(), self.__count))
            except Exception as ex:
                LOGGER.error("{}: 执行第{}次任务期间发生异常:{}".format(self.getName(), self.__count, ex))
                LOGGER.exception(ex)
            finally:
                time.sleep(self.__interval)


def start_monitor(user: dict, config: dict):
    user.update({'config': config})
    monitor = GradeMonitor(**user)
    monitor_thread = MonitorThread(monitor, config['monitor']['interval'], user['id'])
    monitor_thread.start()
    return monitor_thread, user['id']


def read_config() -> dict:
    LOGGER.info("读取配置文件config.yaml")
    with open("./config.yaml", 'rb') as f:
        data = yaml.safe_load_all(f)
        return list(data)[0]
    pass


def init_email(config):
    LOGGER.info("初始化邮箱服务")
    email = MailNotice(sender=config['mail']['sender'],
                       server=config['mail']['server'],
                       sender_name=config['mail']['senderName'],
                       port=config['mail']['port'],
                       secret=config['mail']['secret'])
    config['mail'] = email
    pass


def init_ocr(config):
    LOGGER.info("初始百度ocr")
    ocr = BaiduOcr(api_key=config['ocr']['apiKey'],
                   secret_key=config['ocr']['secretKey'])
    del ocr
    pass


def main():
    monitor_threads = {}
    config: dict = read_config()
    LOGGER.info("当前配置:")
    LOGGER.info('\n' + pprint.pformat(config))

    init_email(config)
    init_ocr(config)

    LOGGER.info("读取用户信息")
    for user in config['users']:
        monitor_thread, user_id = start_monitor(user['user'], config)
        LOGGER.info("用户{}任务线程已启动".format(user_id))
        monitor_threads[user_id] = monitor_thread

    LOGGER.info("程序初始化完成，程序正常运行中")
    while True:
        pass


if __name__ == "__main__":
    main()
