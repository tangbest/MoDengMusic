# -*- coding: utf-8 -*-
import weakref
import types

# 弱引用对象
class Functor(object):
  def __init__(self, func, *args, **kw):
    if type(func) is types.MethodType:
      self.m_wrObj = weakref.ref(func.im_self)  # 方法对应实例弱引用
      self.m_Func = func.im_func  #方法对象
    else:
      self.m_wrObj = None
      self.m_Func = func
    self.m_Args = args
    self.m_Kw = kw

  # 是否激活状态
  def IsActive(self):
    bCallable = callable(self.m_Func)
    if not self.m_wrObj:
      return bCallable
    else:
      return bCallable and self.m_wrObj()

  def __call__(self, *args, **kw):
    curKw = dict(self.m_Kw)
    curKw.update(kw)
    if not self.m_wrObj:
      # 不是实例方法
      curArgs = self.m_Args + args
      return self.m_Func(*curArgs, **curKw)
    else:
      realObj = self.m_wrObj()
    if realObj is None:
      return None
    curArgs = (realObj,)+self.m_Args+args
    return self.m_Func(*curArgs, **curKw)

  def GetKey(self):
    # 返回key值，(对象ID，函数体，args参数hash)
    if self.m_wrObj:
      pObj = self.m_wrObj()
      try:
        iHash = hash(self.m_Args)
      except:
        iHash = 0
      if not pObj:
        key = (0, self.m_Func, iHash)
      else:
        key = (id(pObj), self.m_Func, iHash)
    else:
      key = (0, self.m_Func, hash(self.m_Args))
    return key

  def __cmp__(self, other):
    return cmp(self.GetKey(), other.GetKey())