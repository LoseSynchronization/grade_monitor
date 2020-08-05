# grade_monitor
使用python实现的一个实时监控教务成绩并进行提示的小脚本，**仅供江西理工大学学生使用，其他学校不适用**

> **运行必须环境：python3**

## 1、使用方法
 1. 安装所需依赖

    ```
    pip install -r requirements.txt
    ```
 2. 配置config.yaml

    ```yaml
    ocr:  # 用于识别验证码，使用的是百度识图接口 可以自己去百度AI申请，或者使用默认的
      apiKey: DkP6PhZxIzSt1Y2h5QH25iRE
      secretKey: 88bdoGnYFAnt8cUgOQV6rBrPg7pe1BAf
    
    mail:  # 邮箱服务器配置，用于给用户发送通知, 默认为QQ邮箱
      sender: 123456789@qq.com  # 发件人(email为发件人邮箱)
      senderName: Monitor # 发件人名称
      server: smtp.qq.com  # 邮箱服务器地址
      port: 465  # 服务器端口
      secret: xxxxx  # 服务器密钥，密钥不知道怎么弄的可以百度
    
    users:  # 需要监控的用户，有几个用户就写几个
      - user: # 这是一个用户
          id: 123456789  # 学号，必须唯一
          password: 123456789 # 密码，用于登录webVPN的密码，设置前请先确认密码可用
          email: 123456789@qq.com # 用户的邮箱，用于向用户发送通知
    
    monitor:
      interval: 1800 # 监控间隔，单位s，不建议太短
    ```

    > **注意：yaml文件中，同级间缩进必须一致，不然无法解析**
    >
    > web vpn 地址：https://authserver.webvpn.jxust.edu.cn/authserver/login
    >
    > 登录web vpn后测试教务系统：https://jw.webvpn.jxust.edu.cn/jsxsd/framework/xsMain.jsp

 3. 运行

    ```
    python main.py
    ```

    > 可以后台运行，日志会同时输出到控制台和文件当中

## 2、目录结构

- logs/	存放日志，运行后会生成
- monitor/  监控程序
- notice/ 发送通知的程序
- temp/  存放一些临时文件，比如验证码图片和成绩信息存档(请勿随意删除)
- utils/ 存放一些工具类，比如日志程序和OCR程序
- main.py  主运行程序
- requirements.txt 依赖列表

> 有问题或者建议可以提issue哈！
