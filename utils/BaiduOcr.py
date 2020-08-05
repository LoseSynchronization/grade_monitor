import base64

import requests


class BaiduOcr:
    __TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'

    __OCR_URL = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'

    def __init__(self, api_key, secret_key):
        """百度orc初始化

        :param api_key: api_key 百度ai控制台可获取
        :param secret_key: secret_key 百度ai控制台可获取
        """

        param = {'grant_type': 'client_credentials', 'client_id': api_key, 'client_secret': secret_key}
        # 发送post请求获取token
        response = requests.post(self.__TOKEN_URL, param)
        if response:
            self.__token = dict(response.json())['access_token']

    def general_ocr(self, image_path):
        f = open(image_path, 'rb')
        img = base64.b64encode(f.read())
        params = {"image": img}

        request_url = self.__OCR_URL + "?access_token=" + self.__token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        if response:
            return dict(response.json())['words_result'][0]['words']


# 测试
if __name__ == '__main__':
    api_key = 'DkP6PhZxIzSt1Y2h5QH25iRE'
    secret_key = '88bdoGnYFAnt8cUgOQV6rBrPg7pe1BAf'
    ocr = BaiduOcr(api_key, secret_key)
    print(ocr.general_ocr('tmp_captcha.png'))
