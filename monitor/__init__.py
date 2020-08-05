import json
import os
import sys
import time
from os.path import dirname
from time import sleep

import requests
from PIL import Image
from bs4 import BeautifulSoup

from utils.BaiduOcr import BaiduOcr
from utils.mylogger import Logger


class GradeMonitor:
    # 登录页面Url
    __LOGIN_URL = 'https://authserver.webvpn.jxust.edu.cn/authserver/login?' \
                  'service=https%3A%2F%2Fjw.webvpn.jxust.edu.cn%2Fjsxsd%2Fframework%2FxsMain.jsp'

    # 查询成绩接口
    __GRADE_URL = 'https://jw.webvpn.jxust.edu.cn/jsxsd/kscj/cjcx_list'

    # 获取验证码接口
    __CAPTCHA_URL = 'https://authserver.webvpn.jxust.edu.cn/authserver/captcha.html'

    # 登录最大重试次数
    __MAX_LOGIN_RET = 5

    # 获取成绩最大重试次数
    __MAX_GRADE_RET = 5

    def __init__(self, id, password, email, config):
        """初始化

        :param id: 学号
        :param password: webVPN密码
        :param email: 通知邮箱
        :param config: 配置
        """
        sys.setrecursionlimit(10000)
        self.__stu_code: str = str(id)
        self.__vpn_password = password
        self.__mail_notice = config['mail']
        self.__logger = Logger('GradeMonitor({})'.format(id)).get_log()
        self.__ocr = BaiduOcr(api_key=config['ocr']['apiKey'],
                              secret_key=config['ocr']['secretKey'])

        self.__session = requests.session()
        self.__email = email
        self.start = False
        header = {
            'User-Agent':
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/83.0.4103.116 Safari/537.36",
        }
        self.__session.headers.update(header)
        self.__logger.info("初始化完成！")

    def __login(self) -> bool:
        """
        登录Web VPN
        :return: 是否登录成功
        """
        login = False
        logger = self.__logger
        logger.info("开始登陆web vpn。。。")

        ret = self.__MAX_LOGIN_RET
        while ret:
            ret -= 1
            try:
                session = self.__session
                params = {
                    'username': self.__stu_code,
                    'password': self.__vpn_password
                }

                # 访问登录页面
                response = session.get(self.__LOGIN_URL)

                # 解析网页
                soup = BeautifulSoup(response.text, 'lxml')

                # 获取隐藏参数
                login_form = soup.find('form', id='casLoginForm')
                if login_form:
                    hidden_inputs = login_form.find_all('input', type='hidden')
                    for hidden_input in hidden_inputs:
                        params[hidden_input['name']] = hidden_input['value']

                    # 验证码
                    params['captchaResponse'] = self.__get_captcha_code()

                    # post请求登录
                    response = session.post(self.__LOGIN_URL, params=params)

                # 测试是否登录成功
                if response.url.endswith('framework/xsMain.jsp'):
                    logger.info("登录成功")
                    login = True
                    return login
                else:
                    msg = BeautifulSoup(response.text, 'lxml').find('span', id='msg')
                    if msg:
                        logger.error("登录失败: {}".format(msg.contents[0]))
            except Exception as ex:
                logger.error("登录时发生异常:{}".format(ex))
                logger.exception(ex)
            logger.info("1s后尝试第{}次重试登录...".format((self.__MAX_LOGIN_RET - ret)))
            time.sleep(1)
        else:
            logger.error("登录次数已达到最大重试次数:{}, 本次登录取消！".format(self.__MAX_LOGIN_RET))

        return login

    def __send_notice(self, info: dict):
        """发送通知

        :param info: 通知的内容
        :return: 发送是否成功
        """
        logger = self.__logger
        logger.info("发送通知。。。")
        mail_notice = self.__mail_notice

        title = "新通知"
        notice_content = '你有新的成绩！\n'
        head = '|{1:{0}^20}|{2:{0}^6}|\n'.format(chr(12288), '课程', '成绩')
        notice_content += head

        for k, v in info.items():
            notice_content += "|{1:{0}^20}|{2:{0}^6}|\n".format(chr(12288), k, v)

        return mail_notice.send_notice(title, self.__email, self.__stu_code, notice_content)

    def __get_captcha_code(self):
        logger = self.__logger
        session = self.__session
        ocr = self.__ocr
        image_path = self.__get_temp_path('captcha{}.png'.format(self.__stu_code))

        logger.info("获取验证码。。。")
        while True:
            # 验证码
            captcha_response = session.get(self.__CAPTCHA_URL)
            open(image_path, 'wb').write(captcha_response.content)
            # 处理验证码
            img = Image.open(image_path)
            img = img.convert('L')  # P模式转换为L模式(灰度模式默认阈值127)
            count = 127  # 设定阈值
            table = []
            for i in range(256):
                if i < count:
                    table.append(0)
                else:
                    table.append(1)

            img = img.point(table, '1')
            img.save(image_path)  # 保存处理后的验证码
            captcha_code = ocr.general_ocr(image_path).replace(' ', '')
            logger.info("验证码: {}".format(captcha_code))
            if len(captcha_code) == 4:
                return captcha_code
            else:
                logger.error("验证码长度非法，尝试重新获取")
            sleep(0.5)

    def check_grade(self):
        logger = self.__logger
        logger.info("检查成绩。。。")
        # 读取旧成绩
        grade_file_path = self.__get_temp_path('grades-{}'.format(self.__stu_code))
        old_grades = {}
        if os.path.exists(grade_file_path) and os.path.getsize(grade_file_path):
            f = open(grade_file_path, 'r')
            old_grades = json.load(f)

        # 登录
        if self.__login():
            ret = self.__MAX_GRADE_RET
            while ret:
                ret -= 1
                try:
                    # 查询成绩
                    response = self.__session.get(self.__GRADE_URL)

                    soup = BeautifulSoup(response.text, 'lxml')
                    table = soup.find('table', id='dataList')
                    if table:
                        trs = table.find_all('tr')[1:]
                        new_grades = {}

                        for tr in trs:
                            course_name = tr.find_all('td')[3].contents[0]
                            score = tr.find_all('td')[5].contents[0].strip()
                            if course_name not in old_grades:
                                new_grades[course_name] = score

                        # 通知新成绩
                        if new_grades and len(new_grades) > 0:
                            # 发送通知
                            if self.__send_notice(new_grades):
                                logger.info("通知发送成功")
                            # 保存新的成绩
                            old_grades.update(new_grades)
                            if old_grades:
                                with open(grade_file_path, 'w') as f:
                                    json.dump(old_grades, f, indent=1)
                        else:
                            logger.info("无新成绩")
                        return
                    else:
                        logger.error("读取成绩信息页面失败")
                        logger.info("页面内容:\n{}".format(response.text))
                except Exception as ex:
                    logger.error("获取成绩时出现异常:{}".format(ex))
                    logger.exception(ex)
                logger.info("1s后开始第{}次重试".format((self.__MAX_GRADE_RET - ret)))
                time.sleep(1)
            else:
                logger.error("重试次数已达到最大重试次数:{}, 本次任务取消！".format(self.__MAX_GRADE_RET))
        else:
            logger.error("登录失败，任务取消")

    def __get_temp_path(self, filename) -> str:
        return os.path.join(dirname(dirname(__file__)), 'temp', filename)