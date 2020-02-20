#!/usr/bin/env python
# -*-coding:utf-8-*-
import requests
import random
import time
from PyQt5.QtCore import QThread, pyqtSignal
import contextlib


def getUrlText(url, headers = None, params = None, timeout = 5):
    import requests
    if not headers:
        headers = {}
    if not params:
        params = {}
    base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
    }
    base_headers.update(headers)

    base_params = {

    }
    base_params.update(params)

    try:
        html = requests.get(url, params=base_params, headers=base_headers, timeout = timeout)
        dctResult = {}
        dctResult["json"] = html.json()
        dctResult["text"] = html.text
        return dctResult

    except BaseException:
        print('request error')
        return None


# 访问url,获取数据
class CVisitUrlThread(QThread):
    oSignalFinish = pyqtSignal(dict)  # 下载结束信号
    def __init__(self, sUrl):
        super(CVisitUrlThread, self).__init__()
        self.m_sUrl = sUrl
        self.m_dctHeader = {}

    def setHeader(self, dctHeader):
        self.m_dctHeader = {}

    def getHeader(self):
        dctHeaders = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
            'Referer': "",
        }
        return self.m_dctHeader.update(dctHeaders)

    def run(self):
        dctHeaders = self.getHeader()
        with contextlib.closing(requests.post(self.m_sUrl, headers = dctHeaders, timeout = 5)) as oRequest:
            print("状态码: ", oRequest.status_code)
            if oRequest.status_code != 200:
                print("状态码有误")
                return
            #iContentSize = int(oRequest.headers['content-length']) # 内容体总大小
            #oRequest.json()
            #oRequest.text
            self.oSignalFinish.emit({"json": oRequest.json(), "text": oRequest.text})
