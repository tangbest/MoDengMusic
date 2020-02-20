#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal, QThread
import requests
import contextlib
import re
import threading

from public import tools_url

# 搜索线程
class CSearchThread(QThread):
    oSingleSearchFinish = pyqtSignal(list)
    oSingleSearchError = pyqtSignal()
    def __init__(self,):
        super(CSearchThread, self).__init__()
        self.initData()

    def initData(self):
        self.m_dctMusicType = {
            "QQ": "qq",
            "酷我": "kw",
            "小米": "xm",
            "百度": "bd",
            "网易": "wy",
        }
        self.m_dctHeader = {}
        self.m_sMusicFromType = ""
        self.m_sSearchText = ""

    def setMusicFromType(self, sType):
        self.m_sMusicFromType = sType

    def setSearchText(self, sText):
        self.m_sSearchText = sText

    def setHeader(self, dctHeader):
        self.m_dctHeader = {}

    def getHeader(self):
        dctHeaders = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            # 'Origin':'https://www.bilibili.com',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
            'Referer': "",
        }
        return self.m_dctHeader.update(dctHeaders)

    def run(self):
        dctHeaders = self.getHeader()
        dctData = {
            'p': 1,
            'w': self.m_sSearchText,  # 搜索的数据
            'n': 20
        }
        sUrl = f'https://moresound.tk/music/api.php?search={self.m_dctMusicType[self.m_sMusicFromType]}'
        lstAllSongData = []
        try:
            with contextlib.closing(requests.post(sUrl, data=dctData, headers = dctHeaders, timeout = 10)) as oRequest:
                print("状态码: ", oRequest.status_code)
                if oRequest.status_code != 200:
                    print("状态码有误")
                    return
                dctRequest = oRequest.json()
                #pprint.pprint(dctRequest)
                lstSong = dctRequest["song_list"]
                for dctData in lstSong:
                    dctOneSong = {}
                    dctOneSong["SongMid"] = dctData["songmid"]
                    sSongName = dctData["songname"].replace("\n", "").replace(" ", "")
                    dctOneSong["SongName"] = re.sub('<.*>', "", sSongName)
                    lstSinger = dctData["singer"]
                    if len(lstSinger) > 1:
                        dctOneSong["SingerName"] = ' - '.join(d["name"] for d in lstSinger)
                    else:
                        dctOneSong["SingerName"] = lstSinger[0]["name"]
                    dctOneSong["Albumname"] = dctData["albumname"]
                    dctOneSong["FromType"] = self.m_sMusicFromType
                    lstAllSongData.append(dctOneSong)
                    #pprint.pprint(lstAllSongData)
        except Exception as e:
            print(e)
            self.oSingleSearchError.emit()
            return
        self.oSingleSearchFinish.emit(lstAllSongData)


class CMusicDetailThread(QThread):
    '''获取歌曲信息'''
    oSingleSearchFinish = pyqtSignal(dict)
    oSingleError = pyqtSignal()
    def __init__(self):
        super(CMusicDetailThread, self).__init__()
        self.initData()

    def initData(self):
        self.m_dctMusicType = {
            "QQ": "qq",
            "酷我": "kw",
            "小米": "xm",
            "百度": "bd",
            "网易": "wy",
        }
        self.m_lstMusicMid = []
        self.m_lstFromType = []
        self.m_lstThread = []

    def getHeader(self):
        dctHeaders = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            # 'Origin':'https://www.bilibili.com',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
            'Referer': "",
        }
        return dctHeaders

    def setMusicData(self, lstMusicMid, lstFromType):
        self.m_lstMusicMid = lstMusicMid
        self.m_lstFromType = lstFromType

    def run(self):
        lstThreads = []
        for iIndex, j in enumerate(range(len(self.m_lstMusicMid))):
            sMusicMid = self.m_lstMusicMid[iIndex]
            sRealFromType = self.m_dctMusicType[self.m_lstFromType[iIndex]]
            oThread = threading.Thread(target=self.getLink, args=(sMusicMid, sRealFromType), name=sMusicMid)
            lstThreads.append(oThread)
            self.m_lstThread.append(oThread)

        for oThread in lstThreads:
            oThread.start()

    def getLink(self, sMusicMid, sFromType):
        import pprint
        sUrl = f'https://moresound.tk/music/api.php?get_song={sFromType}'
        print("link", sMusicMid, sFromType, sUrl)
        dctData = {
            'mid': sMusicMid
        }
        try:
            with contextlib.closing(requests.post(sUrl, data=dctData, headers=self.getHeader(), timeout=10)) as oRequest:
                print("状态码: ", oRequest.status_code)
                if oRequest.status_code != 200:
                    print("状态码有误")
                    return
                dctRequest = oRequest.json()
                #pprint.pprint(dctRequest)
                sMvUrl = dctRequest["url"].get("MV", "")
                sBaseUrl = "https://moresound.tk/music/"
                if sMvUrl:
                    sMvUrl = sBaseUrl + sMvUrl
                    dctData = tools_url.getUrlText(sMvUrl)

                    if dctData and dctData["json"].get("url"):
                        sUrl = dctData["json"].get("url")
                        if "https" not in sUrl:
                            sUrl = sUrl.replace("http", "https")
                        dctRequest["url"]["MV"] = sUrl
                    else:
                        dctRequest["url"]["MV"] = "未找到合适地址"
                sMp3Url = dctRequest["url"].get("128MP3", "")
                if sMp3Url:
                    sMp3Url = sBaseUrl + sMp3Url
                    dctData = tools_url.getUrlText(sMp3Url)
                    print("mp3-dctdata", dctData)
                    if dctData and dctData["json"].get("url"):
                        sUrl = dctData["json"].get("url")
                        if "https" not in sUrl:
                            sUrl = sUrl.replace("http", "https")
                        dctRequest["url"]["128MP3"] = sUrl
                    else:
                        dctRequest["url"]["128MP3"] = "未找到合适地址"
                self.oSingleSearchFinish.emit(dctRequest)
        except Exception as e:
            print("发生了错误", e.args[0])
            self.oSingleError.emit()
