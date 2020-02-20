# -*- coding: utf-8 -*-


class CSingleTon(object):
    pMgrObj = None
    def __init__(self):
        assert (self.pMgrObj is None) or (not isinstance(self.pMgrObj, self.__class__))

    @classmethod
    def Get(cls):
        if (cls.pMgrObj is None) or (not isinstance(self.pMgrObj, cls)):
            cls.pMgrObj = cls()
        return cls.pMgrObj

    @classmethod
    def Release(cls):
        cls.pMgrObj = None
