######################################################################
# Copyright (c)
#   John Holland <john@zoner.org>
# All rights reserved.
#
# This software is licensed as described in the file LICENSE.txt, which
# you should have received as part of this distribution.
#
######################################################################

"""
Parses an x12 path

An x12 path is comprised of a sequence of loop identifiers, a segment
identifier, and element position, and a composite position.

The last loop id might be a segment id.

/LOOP_1/LOOP_2
/LOOP_1/LOOP_2/SEG
/LOOP_1/LOOP_2/SEG02
/LOOP_1/LOOP_2/SEG[424]02-1
SEG[434]02-1
02-1
02

"""

import re
import logging as logger
from pyx12.errors import X12PathError

re_seg_id       = r'(?P<seg_id>[A-Z][A-Z0-9]{1,2})?'
re_id_val       = r'(\[(?P<id_val>[A-Z0-9]+)\])?'
re_ele_idx      = r'(?P<ele_idx>[0-9]{2})?'
re_subele_idx   = r'(-(?P<subele_idx>[0-9]+))?'
re_str          = r'^%s%s%s%s$' % (re_seg_id, re_id_val, re_ele_idx, re_subele_idx)
RX_PATH         = re.compile(re_str, re.S)


class X12Path(object):
    """
    Interface to an x12 path
    """

    @property
    def loop_list(self):
        return self._loop_list

    @loop_list.setter
    def loop_list(self, value):
        self._dirty = True
        self._loop_list = value

    @property
    def seg_id(self):
        return self._seg_id

    @property
    def id_val(self):
        return self._id_val

    @property
    def ele_idx(self):
        return self._ele_idx

    @property
    def subele_idx(self):
        return self._subele_idx

    @property
    def relative(self):
        return self._relative

    @seg_id.setter
    def seg_id(self, value):
        self._dirty = True
        self._seg_id = value

    @id_val.setter
    def id_val(self, value):
        self._dirty = True
        self._id_val = value

    @ele_idx.setter
    def ele_idx(self, value):
        self._dirty = True
        self._ele_idx = value

    @subele_idx.setter
    def subele_idx(self, value):
        self._dirty = True
        self._subele_idx = value

    @relative.setter
    def relative(self, value):
        self._dirty = True
        self._relative = value

    def __init__(self, path_str):
        """
        @param path_str:
        @type path_str: string

        """
        self._seg_id = None
        self._id_val = None
        self._ele_idx = None
        self._subele_idx = None
        self._relative = None
        self._path_str = path_str
        self._dirty = False
        self._loop_list = tuple()

        if path_str == '':
            self._relative = True
            return

        if path_str[0] == '/':
            self._relative = False
            self._loop_list = tuple(path_str[1:].split('/'))
        else:
            self._relative = True
            self._loop_list = tuple(path_str.split('/'))

        if len(self._loop_list) == 0:
            return

        if len(self._loop_list) > 0 and self._loop_list[-1] == '':
            # Ended in a /, so no segment
            self._path_str = path_str[:-1]
            self._loop_list = self._loop_list[:-1]
            return

        if len(self._loop_list) > 0:
            seg_str = self._loop_list[-1]
            m = RX_PATH.search(seg_str)
            if m is not None:
                self._loop_list = self._loop_list[:-1]

                self._seg_str = seg_str
                self._seg_id = m.group('seg_id')
                self._id_val = m.group('id_val')
                if m.group('ele_idx') is not None:
                    self._ele_idx = int(m.group('ele_idx'))

                subele_idx = m.group('subele_idx')
                if subele_idx is not None:
                    self._subele_idx = int(subele_idx)

                if self._seg_id is None and self._id_val is not None:
                    raise X12PathError(
                        'Path "%s" is invalid. Must specify a segment identifier with a qualifier' % (path_str))
                if (
                    self._seg_id is None and
                    (self._ele_idx is not None or self._subele_idx is not None) and
                    len(self._loop_list) > 0
                ):
                    raise X12PathError('Path "%s" is invalid. Must specify a segment identifier' % (path_str))
            else:
                self._seg_id = None

    def is_match(self, path_str):
        pass

    def append(self, loop):
        self._loop_list = self._loop_list + tuple(loop.split('/'))
        self._dirty = True

    def empty(self):
        """
        Is the path empty?
        @return: True if contains no path data
        @rtype: boolean
        """
        return self._relative is True and len(self._loop_list) == 0 and self._seg_id is None and self._ele_idx is None

    def _is_child_path(self, root_path, child_path):
        """
        Is the child path really a child of the root path?
        @type root_path: string
        @type child_path: string
        @return: True if a child
        @rtype: boolean
        """
        return len(child_path) > len(root_path) and child_path.find(root_path) == 0
        # root = root_path.split('/')
        # child = child_path.split('/')
        # if len(root) >= len(child):
        #     return False
        # for i in range(len(root)):
        #     if root[i] != child[i]:
        #         return False
        # return True

    def __eq__(self, other):
        if isinstance(other, X12Path):
            return self._loop_list == other.loop_list and self._seg_id == other._seg_id \
                and self._id_val == other._id_val and self._ele_idx == other.ele_idx \
                and self._subele_idx == other.subele_idx and self._relative == other.relative
        return NotImplemented

    def __ne__(self, other):
        res = type(self).__eq__(self, other)
        if res is NotImplemented:
            return res
        return not res

    def __lt__(self, other):
        return NotImplemented

    __le__ = __lt__
    __le__ = __lt__
    __gt__ = __lt__
    __ge__ = __lt__

#    def __len__(self):
#        """
#        @rtype: int
#        """
#        return 1

    def __repr__(self):
        """
        @return: Formatted path
        @rtype: string
        """
        return self.format()

    def __hash__(self):
        return self.__repr__().__hash__()

    def format(self):
        if self._dirty:
            self.fm_path()
        return self._path_str

    def pop_loop(self):
        if len(self._loop_list) > 0:
            loop, self._loop_list = self._loop_list[0], self._loop_list[1:]
        self._path_str = self._path_str.replace(loop + '/', '')
        return loop

    def fm_path(self):
        """
        @rtype: string
        """
        # return self.path_str
        ret = ''
        if not self._relative:
            ret += '/'
        ret += '/'.join(self._loop_list)
        if self._seg_id and ret != '' and ret != '/':
            ret += '/'
        ret += self.fm_refdes()
        self._path_str = ret
        self._dirty = False
        return ret

    def fm_refdes(self):
        ret = ''
        if self._seg_id:
            ret += self._seg_id
            if self._id_val:
                ret += '[%s]' % self._id_val
        if self._ele_idx:
            ret += '%02i' % (self._ele_idx)
            if self._subele_idx:
                ret += '-%i' % self._subele_idx
        self._seg_str = ret
        return ret

    def format_refdes(self):
        if self._dirty:
            self.fm_path()
        return self._seg_str

    def is_child_path(self, child_path):
        """
        Is the child path a child of this path?
        @type child_path: string
        @return: True if a child
        @rtype: boolean
        """
        root_path = self.format()
        return len(child_path) > len(root_path) and child_path.find(root_path) == 0

        # root = self.format().split('/')
        # child = child_path.split('/')
        # if len(root) >= len(child):
        #     return False
        # for i in range(len(root)):
        #     if root[i] != child[i]:
        #         return False
        # return True
