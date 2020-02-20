#!/usr/bin/env python
# -*-coding:utf-8-*-

'''
定时器
补帧定时器 CTimer
不补帧定时器 CPyTimer
'''

import types
import function
import weakref
import traceback

g_AllTimer = []  # 所有定时器对象
g_fCurTime = GetLastLoopStartTime()  # 上一次每帧Loop的起始时间

def OnRestartClear():
    global g_AllTimer, g_fCurTime
    g_AllTimer = []
    g_fCurTime = GetLastLoopStartTime()

def Loop():
    # 每帧循环调用
    global g_fCurTime
    fCurTime = GetLastLoopStartTime()

    g_fCurTime = fCurTime
    # 遍历所有定时器
    for oTimer in g_AllTimer:
        oTimer.Check()


def Timer(fDelayTime, pCallFunc, iRepeat = 0, pRelayObj = None):
    # 生成一个一定时间后执行的对象
    # fDelayTime： 时间间隔， pCallFunc： 调用对象，iRepeat: 0 只调用一次 -1：指定时间间隔不断重复调用， pRelayObj: 依赖对象
    global g_AllTimer
    oTimer = CTimer(fDelayTime, pCallFunc, iRepeat, pRelayObj)
    g_AllTimer.append(oTimer)
    return oTimer

def RmTimer(oTimer):
    # 删除定时器
    global g_AllTimer
    if oTimer not in g_AllTimer:
        return
    g_AllTimer.remove(oTimer)


# 定时器对象
class CTimer(object):
    def __init__(self, fDelayTime, pCallFunc, iRepeat = 0, pRelayObj = None):
        fRealCurTime = GetLastLoopStartTime()
        self.m_fCallTime = fRealCurTime + fDelayTime  # 下次调用时间
        self.m_iInterval = fDelayTime  # 时间间隔
        if type(pCallFunc) is types.MethodType:  # 如果是对象方法，用Functor包一层，弱引用保存函数
            pCallFunc = function.Functor(pCallFunc)
        self.m_pCallFunc = pCallFunc  # 调用对象
        self.m_iRepeat = iRepeat  # 0 只调用一次 -1：指定时间间隔不断重复调用，其它调用指定次数
        if pRelayObj != None:
            pRelayObj = weakref.ref(pRelayObj)
        self.m_wrRelayObj = pRelayObj

    def Check(self):
        #　检查是否要调用
        if self.m_pCallFunc is None:
            return
        if isinstance(self.m_pCallFunc, function.CFuntor) and not self.m_pCallFunc.IsActive():
            self.Release()
            return
        # 检测是否执行
        if g_fCurTime >= self.m_fCallTime:
            bRelease = self.m_wrRelayObj != None and self.m_wrRelayObj() == None
            if not bRelease:
                try:
                    self.m_pCallFunc()
                except:
                    traceback.print_exc()
            if self.m_iRepeat == 0 or bRelease:
                # 结束循环
                self.Release()
                return
            else:
                self.m_fCallTime = self.m_iInterval + self.m_fCallTime
                # 这里应该可以做跳帧处理变成不补帧定时器？未经过测试
                # iStep = int((fCurTime - self.m_fCallTime) / self.m_iInterval) + 1
                # self.m_fCallTime += iStep * self.m_iInterval
                if self.m_iRepeat > 0:
                    self.m_iRepeat -= 1

        return

    def Release(self):
        self.m_pCallFunc = None  #　释放后设为None防止异常调用
        RmTimer(self)


# 不补帧定时器
class CPyTimerMgr(SingleTon):
	def __init__(self):
		self.m_lstAllTimer = []

	def CreatePyCommand(self, fDelayTime, pCallFunc, *args, **kwargs):
		fCurTime = GetLastLoopStartTime()
		oTimer = CPyTimer(self, fCurTime, fDelayTime, pCallFunc, *args, **kwargs)
		self.m_lstAllTimer.append(oTimer)
		return oTimer

	def DeletePyCommand(self, oTimer):
		if oTimer not in self.m_lstAllTimer:
			return
		self.m_lstAllTimer.remove(oTimer)

	def TimeLoop(self):
		# 遍历所有定时器
		for oTimer in self.m_lstAllTimer:
			iCheckState = oTimer.CheckCall(GetLastLoopStartTime())
			if iCheckState == CPyTimer.RET_STOP_CALL:
				self.DeletePyCommand(oTimer)


class CPyTimer(object):
    RET_NOTHING = 0  #　什么都不做
    RET_LOOP_CALL = 1  # 循环调用
    RET_STOP_CALL = 2  # 停止调用
    def __init__(self, oMgr, fCurTime, fDelayTime, pCallFunc, *args, **kwargs):
        self.m_fCallTime = fCurTime + fDelayTime  # 调用时间
        self.m_iInterval = fDelayTime  # 间隔时间
        if type(pCallFunc) is types.MethodType:  # 如果是对象方法，用Functor包一层，弱引用保存函数
            pCallFunc = function.Functor(pCallFunc)
        self.m_pCallFunc = pCallFunc  # 调用对象
        self.m_Args = args
        self.m_Kw = kwargs
        self.m_wrMgr = weakref.ref(oMgr)
        self.m_wrRelayObj = None

    def CheckCall(self, fCurTime):
        if fCurTime >= self.m_fCallTime:
            if self.IsCanRelease():
                return self.RET_STOP_CALL
            fIntervalTime = fCurTime - self.m_fCallTime + self.m_iInterval
            if self.m_pCallFunc(fIntervalTime, *self.m_Args, **self.m_Kw):
                if abs(self.m_iInterval) < 0.000001:
                    # 固定没帧执行,用当前帧作为需要调用的时间
                    self.m_fCallTime = fCurTime
                else:
                    # 跳帧到下一个应该执行的时刻
                    iStep = int((fCurTime - self.m_fCallTime) / self.m_iInterval) + 1
                    self.m_fCallTime += iStep * self.m_iInterval
                return CPyTimer.RET_LOOP_CALL
            else:
                return CPyTimer.RET_STOP_CALL
        else:
            return CPyTimer.RET_NOTHING

    def Release(self):
        oMgr = self.m_wrMgr()
        oMgr.DeletePyCommand(self)

    def SetRelayObj(self, pRelayObj):
     	if pRelayObj:
     		self.m_wrRelayObj = weakref.ref(pRelayObj)
     	else:
     		self.m_wrRelayObj = None

    def IsCanRelease(self):
     	if self.m_wrRelayObj and not self.m_wrRelayObj():
     		return True
     	return False
