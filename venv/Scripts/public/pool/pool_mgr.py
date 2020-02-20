# -*- coding: utf-8 -*-

g_PoolMgr = None
def GetPoolMgr():
	global g_PoolMgr
	if not g_PoolMgr:
		g_PoolMgr = CViewPoolMgr()
	return g_PoolMgr

def TryGetPool(sType, key):
	return GetPoolMgr().TryGetPool(sType, key)

def GetPool(sType, key, dctConfig = None):
	return GetPoolMgr().GetPool(sType, key, dctConfig)

def CycleAll():
	GetPoolMgr().CycleAll()



# 缓存管理器
class CViewPoolMgr(object):
	def __init__(self):
		self.m_dctPool = {}

	def GetPool(self, sType, key, dctConfig):
		# 获取某个缓存池，不存在则创建
		if sType not in self.m_dctPool:
			self.m_dctPool[sType] = {}
		if not key in self.m_dctPool[sType]:
			self.NewPool(sType, key, configure)
		return self.m_dctPool[sType][key]

	def TryGetPool(self, sType, key):
		# 尝试获取某个缓存池，不存在不创建
		if sType not in self.m_dctPool:
			return None
		if key not in self.m_dctPool[sType]:
			return None
		return self.m_dctPool[sType][key]

	def GetPoolType(self, sType):
		return self.m_dctPool.get(sType, {})

	def NewPool(self, sType, key, configure):
		if not dctConfig:
			return None
		pCreator = dctConfig["Creator"]
		iInitNum = dctConfig.get("InitNum", 3)
		iExtendNum = dctConfig.get("ExtendNum", max(iInitNum / 5 + 1))
		self.m_dctPool[sType][key] = CPool(pCreator, iInitNum, iExtendNum)

	def CycleAll(self):
		#　回收全部缓存
		for dctCellPool in self.m_dctPool.values():
			for oCellPool in dctCellPool.values():
				lstCell = oCellPool.GetPoolList()
				pParent = None
				for oCell in lstCell:
					if not pParent:
						pParent = oCell.GetParent()
					if oCell.GetUsed():
						oCell.Cycle()
				if pParent and hasattr(pParent, "ClearCite"):
					pParent.ClearCite()

	def DestroyPool(self, sType, key):
		# 销毁缓存池
		dctPool = self.m_dctPool.get(sType, {})
		if key in dctPool:
			del self.m_dctPool[sType][key]

	def DelFreeObj(self):
		#　删除空闲对象，但会保留至少初始的个数
		for dctCellPool in self.m_dctPool.values():
			for oCellPool in dctCellPool.itervalues():
				oCellPool.DelFreeObj()

	def ClearPool(self):
		# 清空所有缓存池
		self.CycleAll()
		self.m_dctPool = {}


class CPool(object):
	'''
	缓存池对象
	'''
	def __init__(self, pCreator, iInitNum, iExtendNum):
		self.m_pCreator = pCreator  # 生成对象工厂
		self.m_lstPoolObj = []  # 缓存列表
		self.m_iFreePointer = -1  #空闲对象指针
		self.m_iInitNum = iInitNum  #初始化数目
		self.m_iExtendNum = iExtendNum  # 池不够大时扩展数目
		self.Extend(iInitNum)

	def GetPoolList(self):
		return self.m_lstPoolObj

	def New(self):
		# 获取下一个空闲对象
		if self.m_iFreePointer == -1:
			self.Extend(self.m_iExtendNum)  # 扩展
		pObj = self.m_lstPoolObj[self.m_iFreePointer]
		pObj.SetUsed(True)  # 设置被使用
		self.m_iFreePointer = pObj.GetNextFreeIndex()  #　下一个空闲对象指针
		return pObj

	def Cycle(self, pObj):
		# 回收一个对象
		if not pObj.GetUsed():
			return
		pObj.SetNextFreeIndex(self.m_iFreePointer)
		pObj.SetUsed(False)
		self.m_iFreePointer = pObj.GetIndex()

	def Extend(self, iExtendNum):
		# 扩展缓存池
		if iExtendNum <= 0:
			return
		iCurLen = len(self.m_lstPoolObj)
		if iCurLen > 0:
			iStartIdx = iCurLen
		else:
			iStartIdx = 0
		pPre = None  # 上一个空闲对象
		for idx in xrange(iExtendNum):
			iNowIdx = i + iStartIdx
			if not pPre is None:
				pPre.SetNextFreeIndex(iNowIdx)  #　上一个空闲对象指向当前空闲对象
			pObj = self.m_pCreator()
			pObj.SetBelongPool(self)
			pObj.SetIndex(iNowIdx)
			self.m_lstPoolObj.append(pObj)
			pPre = pObj
		if not pPre is None:
			pPre.SetNextFreeIndex(self.m_iFreePointer)  #　最后一个空闲对象，指向旧指针所在的空闲对象
			self.m_iNextFreeIndex = iStartIdx  #更新空闲指针

	def DelFreeObj(self):
		# 删除未使用对象
		lstUsedTemp = []
		for pObj in self.m_lstPoolObj:
			if not pObj.GetUsed():
				continue
			lstUsedTemp.append(pObj)

		# 全部空闲时保留初始化时的个数
		if not lstUsedTemp:
			lstUsedTemp = self.m_lstPoolObj[:self.m_iInitNum]
		self.m_lstPoolObj = lstUsedTemp

		# 设置新的关联关系
		iLen = len(self.m_lstPoolObj)
		for iIdx, pObj in enumerate(self.m_lstPoolObj):
			pObj.SetIndex(iIdx)
			if iIdx + 1 >= iLen:
				iNext = -1
			else:
				iNext = iIdx + 1
			pObj.SetNextFreeIndex(iNext)
		self.m_iFreePointer = -1
