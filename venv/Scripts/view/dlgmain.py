#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QHeaderView, QTableWidgetItem, \
    QAbstractItemView, QProgressBar, QFileDialog
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal

import contextlib
import requests
import pprint
import re

from public import tools_dlgbase
from widgets import ui_main
from view import downthread
from public import tools_url

def openMainDlg():
    import sys
    app = QApplication(sys.argv)
    w = CMainDlg()
    sys.exit(app.exec_())

class CMainDlg(tools_dlgbase.CDlgBase, QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self):
        super(CMainDlg, self).__init__()
        self.setupUi(self)
        self.Center()
        self.initData()
        self.initLayer()
        self.initEvent()
        self.show()

    def initData(self):
        self.m_dctMusicType = {
            "QQ": "QQ",
            "酷我": "kuwo",
            "小米": "xiaomi",
            "百度": "baidu",
        }
        self.m_sCurSearchInfo = ""  # 当前搜索的信息
        self.m_sCurSearchType = ""  # 哪个平台的
        self.m_oThreadSearch = downthread.CSearchThread()  # 搜索线程
        self.m_oThreadDetail = downthread.CMusicDetailThread()  # 音乐详细信息线程
        self.m_lstSearchData = []  # 搜索的结果
        self.m_lstDownloadMusicID = []  # 加入下载列表的ID
        self.m_lstMusicDetal = []  # 下载列表详细的数据
        self.m_lstDownloadByUrlThread = []  # 根据url下载的线程

    def initLayer(self):
        self.initMusicFromType()
        self.initSearchTitle()
        self.leInput.setFocus(True)

    def initSearchTitle(self):
        lstTableHeader = ['序号', '来源', '歌曲名字', '歌手', '唱片']
        twInfo = self.twInfo
        #otwInfo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        twInfo.verticalHeader().hide()
        twInfo.setSelectionBehavior(QAbstractItemView.SelectRows)
        twInfo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        twInfo.horizontalHeader().setStretchLastSection(QHeaderView.Stretch)
        twInfo.setColumnCount(len(lstTableHeader))
        twInfo.setHorizontalHeaderLabels(lstTableHeader)
        twInfo.horizontalHeader().setVisible(True)
        twInfo.setColumnWidth(0, 50)
        twInfo.setColumnWidth(1, 50)
        twInfo.setColumnWidth(2, 200)
        twInfo.setColumnWidth(3, 150)

    def initMusicFromType(self):
        lstType = ["QQ", "酷我", "小米", "百度", "网易"]
        self.cbMusicFrom.addItems(lstType)

    @pyqtSlot(int)
    def on_cbMusicFrom_currentIndexChanged(self, iIndex):
        print("当前音乐来源...", iIndex, self.cbMusicFrom.itemText(iIndex))

    @pyqtSlot()
    def on_pbSearch_clicked(self):
        print("点击了搜索按钮")
        sData = self.leInput.text()
        if not sData:
            return
        sSearchType = self.cbMusicFrom.currentText()
        if sData == self.m_sCurSearchInfo and sSearchType == self.m_sCurSearchType:
            print("当前已经在搜索了...")
            return
        print("搜索内容: {Data}, 搜索类型: {Type}".format(Data = sData, Type = sSearchType))
        self.m_oThreadSearch.setMusicFromType(sSearchType)
        self.m_oThreadSearch.setSearchText(sData)
        self.m_oThreadSearch.start()
        self.statusBar().showMessage("搜索中...")

    @pyqtSlot()
    def on_pbAdd_clicked(self):
        print("点击了加入下载列表按钮...")
        lstSelRow = []
        for iRow in range(self.twInfo.rowCount()):
            if self.twInfo.item(iRow, 0).isSelected():
                lstSelRow.append(iRow)
        if not lstSelRow:
            QMessageBox.warning(self, "提示", "请选中要下载的歌曲", QMessageBox.Ok)
            return
        #print("选中的行数", lstSelRow)
        lstFromType = []
        lstCurSongID = []
        for iRow in lstSelRow:
            dctData = self.m_lstSearchData[iRow]
            #pprint.pprint(dctData)
            iSongMid = dctData["SongMid"]
            if iSongMid in self.m_lstDownloadMusicID:
                print("该歌曲已经在下载列表中了", iSongMid, dctData)
                continue
            self.m_lstDownloadMusicID.append(iSongMid)
            lstFromType.append(dctData["FromType"])
            lstCurSongID.append(iSongMid)
        self.m_oThreadDetail.setMusicData(lstCurSongID, lstFromType)
        self.m_oThreadDetail.start()


    def initEvent(self):
        self.m_oThreadSearch.oSingleSearchError.connect(self.onSearchError)
        self.m_oThreadSearch.oSingleSearchFinish.connect(self.onSearchFinish)
        self.m_oThreadDetail.oSingleSearchFinish.connect(self.onSearchDetailFinish)

    def onSearchDetailFinish(self, dctResult):
        print("搜索详细信息结果")
        pprint.pprint(dctResult)
        twDownload = self.twDownload
        iRow = twDownload.rowCount()
        twDownload.insertRow(iRow)
        iSongID = dctResult.get("id", 0)
        sSongName = dctResult.get("song", "")
        sSingerName = dctResult.get("singer", "")
        twDownload.setItem(iRow, 0, QTableWidgetItem(sSongName))
        twDownload.setItem(iRow, 1, QTableWidgetItem(sSingerName))
        #sBaseUrl = "https://moresound.tk/music/"
        dctUrl = dctResult["url"]
        sCoverUrl = dctUrl.get("专辑封面", "")
        sMvUrl = dctUrl.get("MV", "")
        sMp3Url = dctUrl.get("128MP3", "")
        twDownload.setItem(iRow, 2, QTableWidgetItem(sCoverUrl))
        twDownload.setItem(iRow, 3, QTableWidgetItem(sMvUrl))
        twDownload.setItem(iRow, 4, QTableWidgetItem(sMp3Url))
        pItem = QProgressBar()
        pItem.setValue(0)
        twDownload.setCellWidget(iRow, 5, pItem)

    def visitUrlEnd(self, cbFun):
        pass
        
    @pyqtSlot()
    def on_pbDownload_clicked(self):
        from public import tools_download
        sUrl = self.leInputUrl.text()
        if not sUrl:
            return
        sFileName, sFileType = QFileDialog.getSaveFileName(self, "Save File", ".",
                                                           "All files(*.*)")
        oThreadByUrl = tools_download.CDownloaderBase(sFileName, sUrl)
        oThreadByUrl.start()
        self.m_lstDownloadByUrlThread.append(oThreadByUrl)

    def onSearchFinish(self, lstSong):
        print("搜索结果...")
        #pprint.pprint(lstSong)
        self.twInfo.clearContents()
        self.twInfo.setRowCount(0)
        self.m_lstSearchData = list(lstSong)
        self.statusBar().showMessage(f'找到歌曲{len(lstSong)}首')
        for dctSong in lstSong:
            twInfo = self.twInfo
            iRow = twInfo.rowCount()
            twInfo.insertRow(iRow)
            twInfo.setItem(iRow, 0, QTableWidgetItem(str(iRow + 1)))
            twInfo.setItem(iRow, 1, QTableWidgetItem(dctSong["FromType"]))
            twInfo.setItem(iRow, 2, QTableWidgetItem(dctSong["SongName"]))
            twInfo.setItem(iRow, 3, QTableWidgetItem(dctSong["SingerName"]))
            twInfo.setItem(iRow, 4, QTableWidgetItem(dctSong["Albumname"]))

    def onSearchError(self):
        QMessageBox.warning(self, "提示", "网络延迟或网址崩溃了,再试试!", QMessageBox.Ok)


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
                iTotalNum = dctRequest["totalnum"]
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




