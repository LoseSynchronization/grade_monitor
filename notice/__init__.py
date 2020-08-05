import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from utils import mylogger


class MailNotice:
    """
        邮箱通知
        使用邮箱服务器发送通知
    """

    def __init__(self, sender, server, secret, sender_name="monitor", port="465"):
        """初始化

        :param sender: 邮件发送者地址
        :param server: 邮件服务器
        :param secret: 邮件发送者SMTP密钥
        :param sender_name: 邮件发送者名称
        :param port: 邮件服务器端口
        """
        self.__server = smtplib.SMTP_SSL(server, port)
        self.__server.login(sender, secret)
        self.__sender = sender
        self.__sender_name = sender_name
        self.__logger = mylogger.Logger("{}({})".format(sender, server, port)).get_log()

    def send_notice(self, title, receiver_addr, receiver_name, content, content_type="plain", encode="utf-8"):
        """向指定邮箱发送一份邮件

        :param title: 邮件的标题
        :param receiver_addr: 收信者地址
        :param receiver_name: 收信者名称
        :param content: 邮件内容
        :param content_type: 邮件内容类型，默认为plain纯文本
        :param encode: 邮件编码，默认为utf-8
        :return:
        """
        ret = True
        try:
            msg = MIMEText(content, content_type, encode)
            msg['From'] = formataddr([self.__sender_name, self.__sender])
            msg['To'] = formataddr([receiver_name, receiver_addr])
            msg['Subject'] = title  # 邮件的主题，也可以说是标题

            server = self.__server
            server.sendmail(self.__sender, [receiver_addr, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            self.__logger.info("发送邮件: [{}] {}({})->{}({})"
                               .format(title, self.__sender_name, self.__sender, receiver_name, receiver_addr))
        except Exception as ex:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
            self.__logger.error(ex)
            self.__logger.exception(ex)
            ret = False
        return ret
