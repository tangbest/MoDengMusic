# -*- coding: utf-8 -*-

'''
缓存池
'''

'''
例子
'''
def GetItem(iItemID):
	dctConfig = {
		"Creater": util.Functor(CItem, iItemID),
		"InitNum": 10,
		"Extend": 3,
	}
	oCellPool = GetPool("UIItem", "item", dctConfig)  # 这一步初始化了很多对象
	# 获取新的
	oCell = oCellPool.New()
	oCell.Refresh(iItemID)
	return oCell

class CItem(IPoolObj):
	def __init__(self, iItemID):
		pass

	def Refresh(self, iItemID):
		pass

	def Cycle(self):
		#　回收调用
		IPoolObj.Cycle(self)

