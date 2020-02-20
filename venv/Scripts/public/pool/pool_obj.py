# -*- coding: utf-8 -*-

'''
缓存池
'''


class IPoolObj(object):
    '''
    缓存对象接口
    '''
    def __init__(self):
        self.m_iIndex = None  # 对象所在缓存池的索引
        self.m_iNextFreeIndex = -1  # 下一个空闲对象的索引
        self.m_bUsed = False  # 当前对象是否空闲
        self.m_wrPool = None  # 归属的某个缓存池

    def GetIndex(self):
        # 当前索引
        return self.m_iIndex

    def SetIndex(self, iIdnex):
        # 设置索引
        self.m_iIndex = iIdnex

    def SetUsed(self, bUsed):
        # 设置是否使用
        self.m_bUsed = bUsed

    def GetUsed(self):
        # 是否使用
        return self.m_bUsed

    def GetNextFreeIndex(self):
        # 获取下个空闲索引
        return self.m_iNextFreeIndex

    def SetNextFreeIndex(self, iIndex):
        # 设置下个空闲索引
        self.m_iNextFreeIndex = iIndex

    def SetBelongPool(self, pPool):
        # 设置所属缓存池
        import weakref
        self.m_wrPool = weakref.ref(pPool)

    def Cycle(self):
        # 回收自己
        if self.m_wrPool and self.m_wrPool():
            self.m_wrPool().Cycle(self)

