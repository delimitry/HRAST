# -*- coding: utf-8 -*-

import idaapi
idaapi.require("Patterns.__init__")
idaapi.require("Patterns.Pattern")
from Patterns.Pattern import *


class SavedObj(object):

    def __init__(self, typ, addr):
        self.addr = addr
        self.type = typ


class SavedVar(object):

    def __init__(self, idx, typ, mba):
        self.idx = idx
        self.typ = typ
        self.mba = mba


class SavedMemRef(object):

    def __init__(self, ea, offset):
        self.ea = ea
        self.offset = offset


class SavedCTX(object):
    """Class which holds all collected context"""
    def __init__(self, fcn):
        self.names = fcn.lvars
        self.obj = {}
        self.vars = {}
        self.memref = {}

    def save_obj(self, key, ea, type):
        self.obj[key] = SavedObj(type, ea)

    def save_memref(self, key, ea, offset):
        self.memref[key] = SavedMemRef(ea, offset)

    def save_var(self, idx, val, typ, mb):
        # val is index in fcn.lvars
        self.vars[idx] = SavedVar(val, typ, mb)

    def get_var_name(self, idx):
        return self.names[idx].name

    def has_var(self, idx):
        return idx in self.vars
        
    def get_var(self, idx):
        return self.vars[idx]

    def get_memref(self, key):
        return self.memref[key]

    def get_obj(self, key):
        return self.obj[key]

    def has_obj(self, key):
        return key in self.obj

    def has_memref(self, key):
        return key in self.memref

    def clear_ctx(self):
        self.obj = {}
        self.vars = {}
        self.memref = {}


class Matcher(object):

    def __init__(self, fcn, pattern):

        self.pattern = pattern 
        self.node = 0
        self.replacer = None    
        self.cnt = None   
        self.ctx = SavedCTX(fcn)
        self.chain = False
        self.fcn = fcn

    def set_pattern(self, patt):
        self.pattern = patt

    def check(self, expr):
        self.ctx.clear_ctx()
        return self.pattern.check(expr, self)

    def check_chain(self, node):
        ret = self.pattern.check(node, self)
        if ret is False:
            self.ctx.clear_ctx()
        else:
            if self.is_finished():
                pass
        return ret
    
    def set_node(self, node):
        self.node = node

    def set_cblk_and_node(self, blk, node):
        self.blk = blk
        self.node = node

    def save_cnt(self, val):
        self.cnt = val
        
    def finish_cblock(self):
        if self.is_chain():
            self.pattern.pos = 0

    def is_chain(self):
        return self.chain

    def is_finished(self):
        return self.cnt is not None

    def replace_if_need(self):

        cnt = self.cnt
        self.cnt = None
        if self.replacer is not None:
            if not self.is_chain():
                # we're replacing single instruction
                self.replacer(self.node, self.ctx)
            else:
                # we're replacing chain
                size = len(self.blk.cblock)
                idx = None
                # print self.node.opname
                for i in range(size):
                    # print self.blk.cblock.at(i).opname
                    if self.blk.cblock.at(i) == self.node:
                        idx = i
                        break
                # idx = idx - cnt
                while cnt != 1:
                    self.blk.cblock.remove(self.blk.cblock.at(idx))
                    # idaapi.qswap(self.blk.cblock.at(idx), inst)
                    # del inst
                    idx -= 1
                    cnt -= 1
                self.replacer(self.blk.cblock.at(idx), self.ctx)
        self.ctx.clear_ctx()
