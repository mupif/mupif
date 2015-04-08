# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import math
from . import BBox
from . import Localizer

debug = 0
refineLimit = 400 # refine cell if number of items exceeds this treshold value

class Octant(object):
    """
    Defines Octree Octant: a cell containing either terminal data or its child octants.

    .. automethod:: __init__
    """

    def __init__(self, octree, parent, origin, size):
        """
        The contructor. Octant class contains:

        * data: Container??
        * children: Container??
        * octree: ??
        * parent: ??
        * origin: ??
        * size: ??

        :param Octree octree:
        :param Octree parent:
        :param ?? origin:
        :param ?? size:
        """
        self.data=[]
        self.children=[]
        self.octree = octree
        self.parent = parent
        self.origin = origin
        self.size   = size
        if debug: print ("Octree init: origin:", origin, "size:", size)

    def isTerminal (self):
        """
        :return: True if octree is the terminal cell
        """
        return (len(self.children) == 0)

    def divide (self):
        """
        Divides receiver locally.
        """
        if debug: print ("Dividing locally: self ", self.giveMyBBox(), " mask:", self.octree.mask)
        if not self.isTerminal(): assert("Could not divide non terminal octant")
        self.children=[]
        for i in range(self.octree.mask[0]+1):
            self.children.append([])
            for j in range(self.octree.mask[1]+1):
                self.children[i].append([])
                for k in range(self.octree.mask[2]+1):
                    origin=(self.origin[0]+i*self.size/2.,self.origin[1]+j*self.size/2., self.origin[2]+k*self.size/2.) 
                    self.children[i][j].append(Octant (self.octree, self, origin, self.size/2.))
                    if debug: print ("  Children: ", self.children[i][j][k].giveMyBBox())


    def giveMyBBox(self):
        """ 
        :return: Receiver's BBox
        :rtype: BBox
        """
        # create self bbox
        cc = [0,0,0]
        for i in range(3):
            if (self.octree.mask[i]):
                cc[i] = self.origin[i]+self.size
            else:
                cc[i]=self.origin[i]
        return BBox.BBox (self.origin, tuple(cc)) # create self bbox

    def containsBBox (self, _bbox):
        """ 
        :return: True if BBox contains or intersects the receiver.
        """
        return self.giveMyBBox().intersects(_bbox)

    def insert (self, item, itemBBox=None):
        """
        Insert given object into receiver's list only when the BBox contains and item.

        :param object item: ??
        :param BBox itemBBox: Optional parameter to specify other BBox than that of an item
        """
        if itemBBox is None:
            itemBBox = item.getBBox()
        if self.containsBBox(itemBBox):
            if self.isTerminal():
                self.data.append(item)
                if (len(self.data) > refineLimit):
                    if debug: print ("Octant insert: data limit reached, subdivision")
                    self.divide()
                    for item2 in self.data:
                        for i in range(self.octree.mask[0]+1):
                            for j in range(self.octree.mask[1]+1):
                                for k in range(self.octree.mask[2]+1):
                                    self.children[i][j][k].insert(item2)
                    # empty item list (items already inserted into its childrenren)
                    self.data = []

            else:
                for i in range(self.octree.mask[0]+1):
                    for j in range(self.octree.mask[1]+1):
                        for k in range(self.octree.mask[2]+1):
                            self.children[i][j][k].insert(item, itemBBox)

    def delete (self, item, itemBBox=None):
        """
        Deletes given object from receiver data

        :param object item: ??
        :param BBox itemBBox: Optional parameter to specify other BBox than that of an item
        """
        if itemBBox is None:
            itemBBox = item.getBBox()
        if self.containsBBox(itemBBox):
            if self.isTerminal():
                self.data.remove(item)
            else:
                for i in range(self.octree.mask[0]+1):
                    for j in range(self.octree.mask[1]+1):
                        for k in range(self.octree.mask[2]+1):
                            self.children[i][j][k].remove(item, itemBBox)

    def giveItemsInBBox (self, itemList, bbox):
        """ 
        Adds those managed object into itemList which BBox intersects with given bbox. Note: an object can be included several times, as can be assigned to several octants.
        :param tuple itemList:??
        :param BBox bbox:??
        """ 
        if debug: tab='  '*int(math.ceil ( math.log( self.octree.root.size / self.size) / math.log(2.0)))
        if self.containsBBox(bbox):
            if self.isTerminal():
                if debug: print (tab,"Terminal containing bbox found....", self.giveMyBBox(), "nitems:", len(self.data))
                for i in self.data:
                    if debug: 
                        print (tab,"checking ...", i)
                        print (i.getBBox(), bbox)
                    if i.getBBox().intersects(bbox):
                        if isinstance(itemList, set):
                            itemList.add(i)
                        else:
                            itemList.append(i)
            else:
                if debug: print (tab,"Parent containing bbox found ....", self.giveMyBBox())
                for i in range(self.octree.mask[0]+1):
                    for j in range(self.octree.mask[1]+1):
                        for k in range(self.octree.mask[2]+1):
                            if debug: print (tab,"  Checking child .....", self.children[i][j][k].giveMyBBox())
                            self.children[i][j][k].giveItemsInBBox(itemList, bbox)


    def evaluate (self, functor):
        """ 
        Adds those managed objects into itemList for which functor.evaluate returned Trues. The functor should also provide its BBox to exclude remote octants from the search.

        :param object functor: Functor
        """
        if self.containsBBox(functor.getBBox()):
            if self.isTerminal():
                for i in self.data:
                    functor.evaluate(i)
            else:
                for i in range(self.octree.mask[0]+1):
                    for j in range(self.octree.mask[1]+1):
                        for k in range(self.octree.mask[2]+1):
                            self.children[i][j][k].evaluate(functor)

    def giveDepth (self):
        """
        :return: Depth of ??
        """
        depth = math.ceil ( math.log( self.octree.root.size / self.size) / math.log(2.0))
        if not isTerminal():
            for i in range(self.octree.mask[0]+1):
                for j in range(self.octree.mask[1]+1):
                    for k in range(self.octree.mask[2]+1):
                        depth=max(depth, self.children[i][j][k].giveDepth(itemList, bbox))
        return depth

class Octree(Localizer.Localizer):
    """
    An octree is used to partition space by recursively subdividing the root cell (square or cube) into octants.
    Each terminal octant contains the objects within the octant. Each object that can be inserted and is assumed to provide giveBBox() which returns its bounding box.

    Octree mask is a tuple containing 0 or 1 values. If corresponding mask value is nonzero, receiver is subdivided in corresponding direction. The mask allows to create ocrtrees for various 2D and 1D settings.
    
    .. automethod:: __init__
    """
    def __init__ (self, origin, size, mask):
        """
        The constructor.
        
        :param ?? origin:
        :param ?? size:
        :param ?? mask:
        """
        self.mask = mask
        self.root = Octant (self, None, origin, size)

    def insert (self, item):
        """
        See :func:`Octant.insert`
        """
        self.root.insert(item)

    def delete (self, item):
        """
        See :func:`Octant.delete`
        """
        self.root.delete(item)

    def giveItemsInBBox (self, bbox):
        """
        See :func:`Octant.giveItemsInBBox`
        """
        answer=set()
        # answer = []
        if debug: print ("Octree: Looking for items containing bbox:", bbox)
        self.root.giveItemsInBBox(answer,bbox)
        if debug: print ("Octree: Items found:", answer)
        return answer

    def evaluate(self, functor):
        """
        See :func:`Octant.evaluate`
        """
        self.root.evaluate(functor)

    def giveDepth(self):
        """
        See :func:`Octant.giveDepth`
        """
        return self.root.giveDepth()


