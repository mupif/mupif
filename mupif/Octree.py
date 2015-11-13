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
from __future__ import print_function, division
from builtins import str, range, object

import math, itertools
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

        * data: Container storing the indexed objects (cells, vertices, etc)
        * children: Container storing the children octants (if not terminal). 
        * octree: Link to octree object 
        * parent: Link to parent Octant
        * origin: Coordinates of Octant lower left corner
        * size: Dimension of Octant

        :param Octree octree: Link to octree object 
        :param Octree parent: Link to parent Octant
        :param tuple origin: lower left corner octant coordinates
        :param float size: Size (dimension) of receiver
        """
        self.data=[]
        self.children=[]
        self.octree = octree
        self.parent = parent
        self.origin = origin
        self.size   = size
        self.bbox=None
        if debug: print ("Octree init: origin:", origin, "size:", size)


    def childrenIJK(self):
        """
        :return: iterator over 3-tuples with child indices; functionally equivalent to 3 nested loops, a bit faster and more readable.
        """
        return itertools.product(range(self.octree.mask[0]+1),range(self.octree.mask[1]+1),range(self.octree.mask[2]+1))


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
        if self.bbox: return self.bbox
        # create self bbox
        cc = [0,0,0]
        for i in range(3):
            if (self.octree.mask[i]):
                cc[i] = self.origin[i]+self.size
            else:
                cc[i]=self.origin[i]
        self.bbox=BBox.BBox (self.origin, tuple(cc)) # create self bbox
        return self.bbox

    def containsBBox (self, _bbox):
        """ 
        :return: True if BBox contains or intersects the receiver.
        """
        return self.giveMyBBox().intersects(_bbox)

    def insert (self, item, itemBBox=None):
        """
        Insert given object into receiver container. 
        Object is inserted only when its bounding box intersects the bounding box of the receiver.

        :param object item: object to insert
        :param BBox itemBBox: Optional parameter determining the  BBox of the object
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
                        for i,j,k in self.childrenIJK():
                            self.children[i][j][k].insert(item2)
                    # empty item list (items already inserted into its childrenren)
                    self.data = []

            else:
                for i,j,k in self.childrenIJK():
                    self.children[i][j][k].insert(item, itemBBox)

    def delete (self, item, itemBBox=None):
        """
        Deletes given object from receiver

        :param object item: object to remove
        :param BBox itemBBox: Optional parameter to specify bounding box of the object to be removed
        """
        if itemBBox is None:
            itemBBox = item.getBBox()
        if self.containsBBox(itemBBox):
            if self.isTerminal():
                self.data.remove(item)
            else:
                for i,j,k in self.childrenIJK():
                    self.children[i][j][k].remove(item, itemBBox)

    def giveItemsInBBox (self, itemList, bbox):
        """ 
        Returns the list of objects inside the given bounding box. 
        Note: an object can be included several times, as can be assigned to several octants.

        :param list itemList: list containing the objects matching the criteria
        :param BBox bbox: target bounding box 
        """ 
        if debug: tab='  '*int(math.ceil ( math.log( self.octree.root.size / self.size) / math.log(2.0)))
        if self.containsBBox(bbox):
            if self.isTerminal():
                if debug: print (tab,"Terminal containing bbox found....", self.giveMyBBox(), "nitems:", len(self.data))
                for i in self.data:
                    if debug: 
                        print (tab,"checking ...", i)
                        print (str(i.getBBox()), str(bbox))
                        
                    if i.getBBox().intersects(bbox):
                        if isinstance(itemList, set):
                            itemList.add(i)
                        else:
                            itemList.append(i)
            else:
                if debug: print (tab,"Parent containing bbox found ....", self.giveMyBBox())
                for i,j,k in self.childrenIJK():
                    if debug: print (tab,"  Checking child .....", self.children[i][j][k].giveMyBBox())
                    self.children[i][j][k].giveItemsInBBox(itemList, bbox)


    def evaluate (self, functor):
        """ 
        Evaluate the given functor on all containing objects.
        The functor should define getBBox() function to return bounding box. Only the objects within this bouding box will be processed.
        Functor should also define evaluate method accepting object as a parameter.

        :param object functor: Functor
        """
        if self.containsBBox(functor.getBBox()):
            if self.isTerminal():
                for i in self.data:
                    functor.evaluate(i)
            else:
                for i,j,k in self.childrenIJK():
                    self.children[i][j][k].evaluate(functor)

    def giveDepth (self):
        """
        :return: Returns the depth (the subdivision level) of the receiver (and its children)
        """
        depth = math.ceil ( math.log( self.octree.root.size / self.size) / math.log(2.0))
        if not isTerminal():
            for i,j,k in self.childrenIJK():
                depth=max(depth, self.children[i][j][k].giveDepth(itemList, bbox))
        return depth

class Octree(Localizer.Localizer):
    """
    An octree is used to partition space by recursively subdividing the root cell (square or cube) into octants.
    Octants can be terminal (containing the data) or can be further subdivided into children octants.
    Each terminal octant contains the objects with bounding box within the octant.
    Each object that can be inserted and is assumed to provide giveBBox() which returns its bounding box.

    Octree mask is a tuple containing 0 or 1 values. 
    If corresponding mask value is nonzero, receiver is subdivided in corresponding coordinate direction. 
    The mask allows to create ocrtrees for various 2D and 1D settings.
    
    .. automethod:: __init__
    """
    def __init__ (self, origin, size, mask):
        """
        The constructor.
        
        :param tuple origin: coordinates of lower left corner of the root octant.
        :param float size: dimension (size) of the root octant
        :param tuple mask: boolean tuple, where true values determine the coordinate indices in which octree octants are subdivided
        """
        self.mask = mask
        import sys
        # c++ fast implementation does not use mask; issue a warning to see if someone needs it at all
        # if we support it, it will be stored in every octant, since we don't store Octree pointer there
        if min(mask)==0 and 'mupif.fastOctant' in sys.modules:
            # print('WARN: mupif.fastOctant.Octant assumes non-zero octree mask everywhere (mask='+str(mask)+').')
            log.info('mupif.fastOctant.Octant not yet implemented for 2D and 1D (mask=%s), falling back to the python implementation.'%(str(mask)))
            self.root=Octant_Python(self,None,origin,size)
        else:
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


try:
    from . import fastOctant
    # keep the old implementation when masks are used
    Octant_Python=Octant
    # replace with the c++ implementation
    Octant=fastOctant.Octant
    print('mupif.fast: using mupif.fastOctant')
except ImportError:
    pass
    # print('mupif.fast: NOT using mupif.fastOctant')
