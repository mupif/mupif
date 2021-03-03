#
#           MuPIF: Multi-Physics Integration Framework
#               Copyright (C) 2010-2015 Borek Patzak
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
from . import bbox
from . import util
import math
# from . import mesh
# import mupif.mesh
from . import cellgeometrytype
from .dumpable import Dumpable
import numpy as np
import Pyro5

import numpy
import numpy.linalg
# debug flag
debug = 0

# in element tolerance
tolerance = 0.001

import typing
from . import dumpable
from . import mupifobject

@Pyro5.api.expose
class Cell(dumpable.Dumpable):
    #class Config:
    #    frozen=True
    """
    Representation of a computational cell.

    The solution domain is composed of cells (e.g. finite element), whose geometry is defined using vertices (e.g. nodes).
    Cells provide interpolation over their associated volume, based on given vertex values.
    Derived classes will be implemented to support common interpolation cells (finite elements, FD stencils, etc.)

    .. automethod:: __init__
    """
    
    # mesh: typing.Any=None
    number: int
    label: typing.Optional[int]
    vertices: typing.Tuple[int,...]

    def __init__(self,mesh,**kw):
        super().__init__(**kw)
        self.mesh=mesh
        # assign mesh here so that it does not get serialized

    def __hash__(self): return id(self)

    #def __post_init__(self):
    #    self.bbox=None

    def __old_init__(self, mesh, number, label, vertices):
        """
        Initializes the cell.

        :param mesh.Mesh mesh: The mesh to which a cell belongs to
        :param int number: A local cell number. Local numbering should start from 0 and should be continuous.
        :param int label: A cell label. Arbitrary unique number.
        :param tuple vertices: A cell vertices (local numbers)
        """
        self.mesh = mesh
        self.number = number
        self.label = label
        self.vertices = tuple(vertices)

    # static attribute (cache)
    _subclasses = {}

    @staticmethod
    def getClassForCellGeometryType(cgt):
        """
        Return class object (not instance) for given cell geometry type. Does introspection of all subclasses of Cell caches the result.
        """
        if not Cell._subclasses:
            # cache all subclasses (recursive)
            def get_subclasses(cls):
                ret = []
                for sc in cls.__subclasses__():
                    ret.append(sc)
                    ret.extend(get_subclasses(sc))
                return ret
            for sc in get_subclasses(Cell):
                Cell._subclasses[sc.getGeometryType()] = sc
        return Cell._subclasses[cgt]

    def copy(self):
        """
        This will copy the receiver, making a deep copy of all attributes EXCEPT a mesh attribute

        :return: A deep copy of a receiver
        :rtype: Cell
        """
        return self.__class__(mesh=self.mesh, number=self.number, label=self.label, vertices=tuple(self.vertices))

    def getVertices(self):
        """
        :return: The list of cell vertices
        :rtype: tuple
        """
        if all(isinstance(v, (int, np.integer)) for v in self.vertices):
            return [self.mesh.getVertex(i) for i in self.vertices]
        return self.vertices

    def getNumberOfVertices(self):
        """
        :return: Number of vertices
        :rtype: int
        """
        return len(self.vertices)

    def containsPoint(self, point):
        """
        Check if a cell contains a point.

        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if cell contains a given point
        :rtype: bool
        """

    def interpolate(self, point, vertexValues):
        """
        Interpolates given vertex values to a given point.

        :param tuple point: 1D/2D/3D position vector
        :param tuple vertexValues: A tuple containing vertex values
        :return: Interpolated value at a given point
        :rtype: tuple
        """

    @classmethod
    def getGeometryType(cls):
        """
        Returns geometry type of receiver.

        :return: Returns geometry type of receiver
        :rtype: CellGeometryType
        """

    def getBBox(self, relPad=1e-5):
        """
        Return bounding box. The box is by default slightly enlarged via *relPad* to avoid finite-precision issues when testing for a boundary point being inside the box.

        :param float relPad: relative padding of the box; tight (geometrical)  bbox will be enlarged along each axis by *relPad* times size along that axis, in both directions.
        :return: Returns a bounding box of the receiver
        :rtype: BBox
        """

        if hasattr(self,'bbox') and self.bbox is not None: return self.bbox

        # This piece should be rewritten
        init = True
        try:
            for vertex in self.vertices:
                c = self.mesh.getVertex(vertex).coords
                if init:
                    min_coords = list(c)
                    max_coords = list(c)
                    init = False
                else:
                    for i in range(len(c)):
                        min_coords[i] = min(min_coords[i], c[i])
                        max_coords[i] = max(max_coords[i], c[i])
        except IndexError:
            print("getBBox failed: cell-no: ", self.number, "vertices: ", self.vertices, "vertex: ", vertex)
            exit(1)

        if relPad:
            sizes = [max_coords[i]-min_coords[i] for i in (0, 1, 2)]  # compute box sizes (should be all non-negative)
            sizes = [max(sizes) if sizes[i] == 0 else sizes[i] for i in (0, 1, 2)]  # replace zero size by maximum for the purposes of padding
            min_coords = [min_coords[i]-relPad*sizes[i] for i in (0, 1, 2)]  # pad on the negative side
            max_coords = [max_coords[i]+relPad*sizes[i] for i in (0, 1, 2)]  # pad on the positive side

        object.__setattr__(self,'bbox',bbox.BBox(tuple(min_coords), tuple(max_coords)))
        return self.bbox

    def getTransformationJacobian(self, coords):
        """
        Returns the transformation jacobian (the determinant of jacobian) of the receiver

        :param tuple coords: local (parametric) coordinates of the point
        :return: jacobian
        :rtype: float
        """
        # raise apierror.APIError("getTransformationJacobian not implemented")

    def getMeshioGeometryStr(self):
        meshioTypeMap={
            cellgeometrytype.CGT_TRIANGLE_1:'triangle',
            cellgeometrytype.CGT_QUAD:'quad',
            cellgeometrytype.CGT_TETRA:'tetra',
            cellgeometrytype.CGT_HEXAHEDRON:'hexahedron',
            cellgeometrytype.CGT_TRIANGLE_2:'triangle6'
        }
        return meshioTypeMap[self.getGeometryType()]



##############################################################
# Implementation of individual cells follows
##############################################################


@Pyro5.api.expose
class Triangle_2d_lin(Cell):
    """
    Unstructured 2D triangular element with linear interpolation
    Node numbering convention:

    2
    | \
    |  \
    |   \
    |    \
    0-----1

    """
    def __hash__(self): return id(self)

    def copy(self):
        """
        This will copy the receiver, making a deep copy of all atributes EXCEPT mesh attribute.

        :return: A deep copy of a receiver
        :rtype: Cell
        """
        return Triangle_2d_lin(mesh=self.mesh, number=self.number, label=self.label, vertices=tuple(self.vertices))

    @classmethod
    def getGeometryType(cls):
        """
        Returns geometry type of receiver.

        :return: Returns geometry type of receiver
        :rtype: CellGeometryType
        """
        return cellgeometrytype.CGT_TRIANGLE_1

    def glob2loc(self, coords):
        """
        Converts global coordinate to local (area) coordinate.

        :param tuple coords: A coordinate in global system
        :return: local (area) coordinate
        :rtype: tuple
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        x1 = c1[0]; y1 = c1[1]
        x2 = c2[0]; y2 = c2[1]
        x3 = c3[0]; y3 = c3[1]

        area = 0.5 * ( x2 * y3 + x1 * y2 + y1 * x3 - x2 * y1 - x3 * y2 - x1 * y3 )

        l1 = ( ( x2 * y3 - x3 * y2 ) + ( y2 - y3 ) * coords[0] + ( x3 - x2 ) * coords[1] ) / 2. / area
        l2 = ( ( x3 * y1 - x1 * y3 ) + ( y3 - y1 ) * coords[0] + ( x1 - x3 ) * coords[1] ) / 2. / area
        l3 = ( ( x1 * y2 - x2 * y1 ) + ( y1 - y2 ) * coords[0] + ( x2 - x1 ) * coords[1] ) / 2. / area

        return l1, l2, l3

    def loc2glob(self, lc):
        """
        Converts local (parametric) coordinates to global ones.

        :param tuple lc: A local coordinate
        :return: global coordinate
        :rtype: tuple
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        l1 = lc[0]
        l2 = lc[1]
        l3 = 1.-l1-l2
        return l1*c1[0]+l2*c2[0]+l3*c3[0], l1*c1[1]+l2*c2[1]+l3*c3[1]

    def interpolate(self, point, vertexValues):
        """
        Interpolates given vertex values to a given point.

        :param tuple point: 1D/2D/3D position vector
        :param tuple vertexValues: A tuple containing vertex values
        :return: Interpolated value at a given point
        :rtype: tuple
        """
        ac = self.glob2loc(point)
        return tuple([vertexValues[0][i]*ac[0]+vertexValues[1][i]*ac[1]+vertexValues[2][i]*ac[2] for i in range(len(vertexValues[0]))])

    def containsPoint(self, point):
        """
        Check if a cell contains a point.

        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if cell contains a given point
        :rtype: bool
        """
        ac = self.glob2loc(point)

        for li in ac:
            if li < -tolerance or li > 1.0+tolerance:
                return False
        return True

    def getTransformationJacobian(self, coords):
        """
        Returns the transformation jacobian (the determinant of jacobian) of the receiver

        :param tuple coords: local (parametric) coordinates of the point
        :return: jacobian
        :rtype: float
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords

        return c1[0] * (c2[1] - c3[1]) + c2[0] * (-c1[1] + c3[1]) + c3[0] * (c1[1] - c2[1])

    def _evalN(self, lc):
        """
        Evaluates shape functions at given point (given in parametric coordinates).

        :param tuple lc: A local coordinate
        :return: shape function values
        :rtype: tuple
        """
        return lc[0], lc[1], 1.-lc[0]-lc[1]


@Pyro5.api.expose
class Triangle_2d_quad(Cell):
    """
    Unstructured 2D triangular element with quadratic interpolation
    Node numbering convention:

    2
    | \
    |  \
    5   4
    |    \
    |     \
    0--3---1

    """
    def __hash__(self): return id(self)

    def copy(self):
        """
        This will copy the receiver, making a deep copy of all atributes EXCEPT mesh attribute.

        :return: A deep copy of a receiver
        :rtype: Cell
        """
        return Triangle_2d_quad(mesh=self.mesh, number=self.number, label=self.label, vertices=tuple(self.vertices))

    @classmethod
    def getGeometryType(cls):
        """
        Returns geometry type of receiver.

        :return: Returns geometry type of receiver
        :rtype: CellGeometryType
        """
        return cellgeometrytype.CGT_TRIANGLE_2

    def glob2loc(self, coords):
        """
        Converts global coordinate to local (area) coordinate.

        :param tuple coords: A coordinate in global system
        :return: local (area) coordinate
        :rtype: tuple
        """

        convergence_limit = 1.e-6 * math.sqrt(self._evalArea())
        res = np.zeros(2)
        # setup initial guess
        lcoords_guess = [0.0, 0.0]

        error = 0.  # formal initial value

        # apply Newton-Raphson to solve the problem
        for nite in range(10):
            # compute the residual
            guess = self.loc2glob(lcoords_guess)
            res[0] = coords[0] - guess[0]
            res[1] = coords[1] - guess[1]

            # check for convergence
            error = math.sqrt(res[0]*res[0] + res[1]*res[1])
            if error < convergence_limit:
                break

            # compute the corrections
            jac = self._getTransformationJacobianMtrx(lcoords_guess)
            delta = np.linalg.solve(jac.T, res)
            ee = jac.dot(delta)-res

            # update guess
            lcoords_guess[0] = lcoords_guess[0] + delta[0]
            lcoords_guess[1] = lcoords_guess[1] + delta[1]

        if error > convergence_limit:
            # failed convergence
            return None

        return lcoords_guess[0], lcoords_guess[1], 1.0 - lcoords_guess[0] - lcoords_guess[1]

    def loc2glob(self, lc):
        """
        Converts local (parametric) coordinates to global ones.

        :param tuple lc: A local coordinate
        :return: global coordinate
        :rtype: tuple
        """
        x = 0
        y = 0
        n = self._evalN(lc)
        for i in range(6):
            x += n[i] * self.mesh.getVertex(self.vertices[i]).coords[0]
            y += n[i] * self.mesh.getVertex(self.vertices[i]).coords[1]

        return x, y

    def interpolate(self, point, vertexValues):
        """
        Interpolates given vertex values to a given point.

        :param tuple point: 1D/2D/3D position vector
        :param tuple vertexValues: A tuple containing vertex values
        :return: Interpolated value at a given point
        :rtype: tuple
        """
        lc = self.glob2loc(point)
        n = self._evalN(lc)
        return tuple([n[0]*vertexValues[0][i]+n[1]*vertexValues[1][i]+n[2]*vertexValues[2][i]+n[3]*vertexValues[3][i]+n[4]*vertexValues[4][i]+n[5]*vertexValues[5][i] for i in range(len(vertexValues[0]))])

    def containsPoint(self, point):
        """
        Check if a cell contains a point.

        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if cell contains a given point
        :rtype: bool
        """
        ac = self.glob2loc(point)

        for li in ac:
            if li < -tolerance or li > 1.0+tolerance:
                return False
        return True

    def getTransformationJacobian(self, coords):
        """
        Returns the transformation jacobian (the determinant of jacobian) of the receiver

        :param tuple coords: local (parametric) coordinates of the point
        :return: jacobian
        :rtype: float
        """
        return np.linalg.det(self._getTransformationJacobianMtrx(coords))

    def _getTransformationJacobianMtrx(self, lcoords):
        """
        Returns the jacobian matrix  J (x,y)/(ksi,eta)  of the receiver.
        :param tuple lcoords: local (parametric) coordinates of the point
        :return: jacobian matrix
        :rtype: numpy.matrix
        """

        jacobianMatrix = np.zeros((2, 2))

        dn = self._evalDerivatives(lcoords)

        for i in range(dn.shape[0]):
            c = self.mesh.getVertex(self.vertices[i]).coords
            x = c[0]
            y = c[1]

            jacobianMatrix[0][0] += dn[i][0] * x
            jacobianMatrix[0][1] += dn[i][0] * y
            jacobianMatrix[1][0] += dn[i][1] * x
            jacobianMatrix[1][1] += dn[i][1] * y

        return jacobianMatrix

    def _evalN(self, lc):
        """
        Evaluates shape functions at given point (given in parametric coordinates).

        :param tuple lc: A local coordinate
        :return: shape function values
        :rtype: tuple
        """
        # print "lc :",lc
        l1 = lc[0]
        l2 = lc[1]
        l3 = 1.0-l1-l2

        return ((2. * l1 - 1.) * l1,
                (2. * l2 - 1.) * l2,
                (2. * l3 - 1.) * l3,
                4. * l1 * l2,
                4. * l2 * l3,
                4. * l3 * l1)

    def _evalDerivatives(self, lc):
        """
        Evaluates shape function derivatives at given point (given in parametric coordinates).

        :param tuple lc: A local coordinate
        :return: shape function derivatives
        :rtype: numpy.matrix
        """
        l1 = lc[0]
        l2 = lc[1]
        l3 = 1.0 - l1 - l2

        dn = np.zeros((6, 2))

        dn[0][0] = 4.0 * l1 - 1.0
        dn[1][0] = 0.0
        dn[2][0] = -1.0 * (4.0 * l3 - 1.0)
        dn[3][0] = 4.0 * l2
        dn[4][0] = -4.0 * l2
        dn[5][0] = 4.0 * l3 - 4.0 * l1

        dn[0][1] = 0.0
        dn[1][1] = 4.0 * l2 - 1.0
        dn[2][1] = -1.0 * (4.0 * l3 - 1.0)
        dn[3][1] = 4.0 * l1
        dn[4][1] = 4.0 * l3 - 4.0 * l2
        dn[5][1] = -4.0 * l1

        return dn

    def _evalArea(self):
        p = self.mesh.getVertex(self.vertices[0]).coords
        x1 = p[0]
        y1 = p[1]
        p = self.mesh.getVertex(self.vertices[1]).coords
        x2 = p[0]
        y2 = p[1]
        p = self.mesh.getVertex(self.vertices[2]).coords
        x3 = p[0]
        y3 = p[1]
        p = self.mesh.getVertex(self.vertices[3]).coords
        x4 = p[0]
        y4 = p[1]
        p = self.mesh.getVertex(self.vertices[4]).coords
        x5 = p[0]
        y5 = p[1]
        p = self.mesh.getVertex(self.vertices[5]).coords
        x6 = p[0]
        y6 = p[1]

        return math.fabs( ( 4 * ( -( x4 * y1 ) + x6 * y1 + x4 * y2 - x5 * y2 + x5 * y3 - x6 * y3 ) + x2 * ( y1 - y3 - 4 * y4 + 4 * y5 ) +
                            x1 * ( -y2 + y3 + 4 * y4 - 4 * y6 ) + x3 * ( -y1 + y2 - 4 * y5 + 4 * y6 ) ) / 6 )


@Pyro5.api.expose
class Quad_2d_lin(Cell):
    """
    Unstructured 2d quad element with linear interpolation
    """
    def __hash__(self): return id(self)

    def copy(self):
        """
        This will copy the receiver, making deep copy of all atributes EXCEPT mesh attribute.

        :return: A deep copy of a receiver
        :rtype: Cell
        """
        return Quad_2d_lin(mesh=self.mesh, number=self.number, label=self.label, vertices=tuple(self.vertices))

    @classmethod
    def getGeometryType(cls):
        """
        Returns geometry type of receiver.

        :return: Returns geometry type of receiver
        :rtype: CellGeometryType
        """
        return cellgeometrytype.CGT_QUAD

    def _evalN(self, lc):
        """
        Evaluates shape functions at given point (given in parametric coordinates).

        :param tuple lc: A local coordinate
        :return: shape function
        :rtype: float
        """
        # print "lc :",lc

        return (0.25 * ( 1. + lc[0] ) * ( 1. + lc[1] ),
                0.25 * ( 1. - lc[0] ) * ( 1. + lc[1] ),
                0.25 * ( 1. - lc[0] ) * ( 1. - lc[1] ),
                0.25 * ( 1. + lc[0] ) * ( 1. - lc[1] ))

    def glob2loc(self, coords):
        """
        Converts global coordinate to local (area) coordinate.

        :param tuple coords: A coordinate in global system
        :return: local (area) coordinate
        :rtype: tuple
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        c4 = self.mesh.getVertex(self.vertices[3]).coords

        a1 = c1[0]+c2[0]+c3[0]+c4[0]
        a2 = c1[0]-c2[0]-c3[0]+c4[0]
        a3 = c1[0]+c2[0]-c3[0]-c4[0]
        a4 = c1[0]-c2[0]+c3[0]-c4[0]

        b1 = c1[1]+c2[1]+c3[1]+c4[1]
        b2 = c1[1]-c2[1]-c3[1]+c4[1]
        b3 = c1[1]+c2[1]-c3[1]-c4[1]
        b4 = c1[1]-c2[1]+c3[1]-c4[1]

        a = a2 * b4 - b2 * a4
        b = a1 * b4 + a2 * b3 - a3 * b2 - b1 * a4 - b4 * 4.0 * coords[0] + a4 * 4.0 * coords[1]
        c = a1 * b3 - a3 * b1 - 4.0 * coords[0] * b3 + 4.0 * coords[1] * a3

        # solve quadratic equation
        ksi = util.quadratic_real(a, b, c)
        if debug:
            print ("quadratic_real returned ", ksi, "for a,b,c ", a, b, c)
        if len(ksi) == 0:
            return 0, (0., 0.)
        else:
            ksi1 = ksi[0]
            denom = b3+ksi1*b4
            if math.fabs(denom) <= 1.e-10:
                eta1 = (4.0*coords[0]-a1-ksi1*a2)/(a3+ksi1*a4)
            else:
                eta1 = (4.0*coords[1]-b1-ksi1*b2)/denom

        if len(ksi) > 1:
            ksi2 = ksi[1]
            denom = b3 + ksi2*b4

            if math.fabs(denom) <= 1.0e-10:
                if (a3+ksi2*a4) <= 1.e-10:
                    ksi2 = ksi1
                    eta2 = eta1
                else:
                    eta2 = (4.0*coords[0]-a1-ksi2*a2)/(a3+ksi2*a4)
            else:
                eta2 = (4.0*coords[1]-b1-ksi2*b2)/denom

            diff_ksi1 = 0.0
            if ksi1 > 1.0:
                diff_ksi1 = ksi1 - 1.0

            if ksi1 < -1.0:
                diff_ksi1 = ksi1 + 1.0

            diff_eta1 = 0.0
            if eta1 > 1.0:
                diff_eta1 = eta1 - 1.0
            if eta1 < -1.0:
                diff_eta1 = eta1 + 1.0

            diff_ksi2 = 0.0
            if ksi2 > 1.0:
                diff_ksi2 = ksi2 - 1.0

            if ksi2 < -1.0:
                diff_ksi2 = ksi2 + 1.0

            diff_eta2 = 0.0
            if eta2 > 1.0:
                diff_eta2 = eta2 - 1.0
            if eta2 < -1.0:
                diff_eta2 = eta2 + 1.0

            diff1 = diff_ksi1 * diff_ksi1 + diff_eta1 * diff_eta1
            diff2 = diff_ksi2 * diff_ksi2 + diff_eta2 * diff_eta2

            # ksi2, eta2 seems to be closer
            if diff1 > diff2:
                ksi1 = ksi2
                eta1 = eta2

        answer = (ksi1, eta1)
        # test if inside
        inside = True
        for pc in answer:
            if pc < (-1. - tolerance) or pc > (1.+tolerance):
                inside = False
        return inside, answer

    def loc2glob(self, lc):
        """
        Converts local (parametric) coordinates to global ones.

        :param tuple lc: A local coordinate
        :return: global coordinate
        :rtype: tuple
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        c4 = self.mesh.getVertex(self.vertices[3]).coords

        n1 = 0.25*(1.0+lc[0])*(1.0+lc[1])
        n2 = 0.25*(1.0-lc[0])*(1.0+lc[1])
        n3 = 0.25*(1.0-lc[0])*(1.0-lc[1])
        n4 = 0.25*(1.0+lc[0])*(1.0-lc[1])

        if len(c1) == 2:
            return n1*c1[0]+n2*c2[0]+n3*c3[0]+n4*c4[0], n1*c1[1]+n2*c2[1]+n3*c3[1]+n4*c4[1]
        else:
            return n1*c1[0]+n2*c2[0]+n3*c3[0]+n4*c4[0], n1*c1[1]+n2*c2[1]+n3*c3[1]+n4*c4[1], n1*c1[2]+n2*c2[2]+n3*c3[2]+n4*c4[2]

    def interpolate(self, point, vertexValues):
        """
        Interpolates given vertex values to a given point.

        :param tuple point: 1D/2D/3D position vector
        :param tuple vertexValues: A tuple containing vertex values
        :return: Interpolated value at a given point
        :rtype: tuple
        """

        (inside, ac) = self.glob2loc(point)
        # print "glob:",point,"->loc:",ac

        return tuple([(0.25*(1.0+ac[0])*(1.0+ac[1])*vertexValues[0][i] +
                       0.25*(1.0-ac[0])*(1.0+ac[1])*vertexValues[1][i] +
                       0.25*(1.0-ac[0])*(1.0-ac[1])*vertexValues[2][i] +
                       0.25*(1.0+ac[0])*(1.0-ac[1])*vertexValues[3][i]) for i in range(len(vertexValues[0]))])

    def containsPoint(self, point):
        """
        Check if a cell contains a point.

        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if cell contains a given point
        :rtype: bool
        """
        (inside, ac) = self.glob2loc(point)
        return inside

    def getTransformationJacobian(self, coords):
        """
        Returns the transformation jacobian (the determinant of jacobian) of the receiver

        :param tuple coords: local (parametric) coordinates of the point
        :return: jacobian
        :rtype: float
        """
        ksi = coords[0]
        eta = coords[1]
        # dN/dksi
        dnk = (0.25 * (1. + eta ), -0.25 * (1. + eta), -0.25 * (1. - eta), 0.25 * (1. - eta))
        # dN/deta
        dne = (0.25 * (1. + ksi ), 0.25 * (1. - ksi), -0.25 * (1. - ksi), -0.25 * (1. + ksi))

        j11 = 0
        j12 = 0
        j21 = 0
        j22 = 0
        for i in range(4):
            v = self.mesh.getVertex(self.vertices[i])
            x = v.coords[0]
            y = v.coords[1]
            j11 = j11+dnk[i]*x
            j12 = j12+dnk[i]*y
            j21 = j21+dne[i]*x
            j22 = j22+dne[i]*y

        return j11*j22-j12*j21


@Pyro5.api.expose
class Tetrahedron_3d_lin(Cell):
    """
    Unstructured 3d tetrahedral element with linear interpolation.
    """
    def __hash__(self): return id(self)

    def copy(self):
        """
        This will copy the receiver, making a deep copy of all atributes EXCEPT mesh attribute.

        :return: A deep copy of a receiver
        :rtype: Cell
        """
        return Tetrahedron_3d_lin(mesh=self.mesh, number=self.number, label=self.label, vertices=tuple(self.vertices))

    @classmethod
    def getGeometryType(cls):
        """
        Returns geometry type of receiver.

        :return: Returns geometry type of receiver
        :rtype: CellGeometryType
        """
        return cellgeometrytype.CGT_TETRA

    def glob2loc(self, coords):
        """
        Converts global coordinate to local (area) coordinate.

        :param tuple coords: A coordinate in global system
        :return: local (area) coordinate
        :rtype: tuple
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        c4 = self.mesh.getVertex(self.vertices[3]).coords

        x1 = c1[0]; y1 = c1[1]; z1 = c1[2]
        x2 = c2[0]; y2 = c2[1]; z2 = c2[2]
        x3 = c3[0]; y3 = c3[1]; z3 = c3[2]
        x4 = c4[0]; y4 = c4[1]; z4 = c4[2]

        xp = coords[0]; yp = coords[1]; zp = coords[2]

        volume = ( ( x4 - x1 ) * ( y2 - y1 ) * ( z3 - z1 ) - ( x4 - x1 ) * ( y3 - y1 ) * ( z2 - z1 ) +
                   ( x3 - x1 ) * ( y4 - y1 ) * ( z2 - z1 ) - ( x2 - x1 ) * ( y4 - y1 ) * ( z3 - z1 ) +
                   ( x2 - x1 ) * ( y3 - y1 ) * ( z4 - z1 ) - ( x3 - x1 ) * ( y2 - y1 ) * ( z4 - z1 ) ) / 6.

        l1 = ( ( x3 - x2 ) * ( yp - y2 ) * ( z4 - z2 ) - ( xp - x2 ) * ( y3 - y2 ) * ( z4 - z2 ) +
               ( x4 - x2 ) * ( y3 - y2 ) * ( zp - z2 ) - ( x4 - x2 ) * ( yp - y2 ) * ( z3 - z2 ) +
               ( xp - x2 ) * ( y4 - y2 ) * ( z3 - z2 ) - ( x3 - x2 ) * ( y4 - y2 ) * ( zp - z2 ) ) / 6. / volume

        l2 = ( ( x4 - x1 ) * ( yp - y1 ) * ( z3 - z1 ) - ( xp - x1 ) * ( y4 - y1 ) * ( z3 - z1 ) +
               ( x3 - x1 ) * ( y4 - y1 ) * ( zp - z1 ) - ( x3 - x1 ) * ( yp - y1 ) * ( z4 - z1 ) +
               ( xp - x1 ) * ( y3 - y1 ) * ( z4 - z1 ) - ( x4 - x1 ) * ( y3 - y1 ) * ( zp - z1 ) ) / 6. / volume

        l3 = ( ( x2 - x1 ) * ( yp - y1 ) * ( z4 - z1 ) - ( xp - x1 ) * ( y2 - y1 ) * ( z4 - z1 ) +
               ( x4 - x1 ) * ( y2 - y1 ) * ( zp - z1 ) - ( x4 - x1 ) * ( yp - y1 ) * ( z2 - z1 ) +
               ( xp - x1 ) * ( y4 - y1 ) * ( z2 - z1 ) - ( x2 - x1 ) * ( y4 - y1 ) * ( zp - z1 ) ) / 6. / volume

        l4 = 1.0 - l1 - l2 - l3

        return l1, l2, l3, l4

    def loc2glob(self, lc):
        """
        Converts local (parametric) coordinates to global ones

        :param tuple lc: A local coordinate
        :return: global coordinate
        :rtype: tuple
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        c4 = self.mesh.getVertex(self.vertices[3]).coords

        l1 = lc[0]
        l2 = lc[1]
        l3 = lc[2]
        l4 = 1. - l1 - l2 - l3

        return (
            l1*c1[0]+l2*c2[0]+l3*c3[0]+l4*c4[0],
            l1*c1[1]+l2*c2[1]+l3*c3[1]+l4*c4[1],
            l1*c1[2]+l2*c2[2]+l3*c3[2]+l4*c4[2]
        )

    def interpolate(self, point, vertexValues):
        """
        Interpolates given vertex values to a given point.

        :param tuple point: 1D/2D/3D position vector
        :param tuple vertexValues: A tuple containing vertex values
        :return: Interpolated value at a given point
        :rtype: tuple
        """

        ac = self.glob2loc(point)
        return tuple([vertexValues[0][i]*ac[0]+vertexValues[1][i]*ac[1]+vertexValues[2][i]*ac[2]+vertexValues[3][i]*ac[3] for i in range(len(vertexValues[0]))])

    def containsPoint(self, point):
        """
        Check if a cell contains a point.

        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if cell contains a given point
        :rtype: bool
        """
        ac = self.glob2loc(point)

        for li in ac:
            if li < -tolerance or li > 1.0+tolerance:
                return False
        return True

    def getTransformationJacobian(self, coords):
        """
        Returns the transformation jacobian (the determinant of jacobian) of the receiver

        :param tuple coords: local (parametric) coordinates of the point
        :return: jacobian
        :rtype: float
        """
        c1 = self.mesh.getVertex(self.vertices[0]).coords
        c2 = self.mesh.getVertex(self.vertices[1]).coords
        c3 = self.mesh.getVertex(self.vertices[2]).coords
        c4 = self.mesh.getVertex(self.vertices[3]).coords

        return ( ( c4[0] - c1[0] ) * ( c2[1] - c1[1] ) * ( c3[2] - c1[2] ) -
                 ( c4[0] - c1[0] ) * ( c3[1] - c1[1] ) * ( c2[2] - c1[2] ) +
                 ( c3[0] - c1[0] ) * ( c4[1] - c1[1] ) * ( c2[2] - c1[2] ) -
                 ( c2[0] - c1[0] ) * ( c4[1] - c1[1] ) * ( c3[2] - c1[2] ) +
                 ( c2[0] - c1[0] ) * ( c3[1] - c1[1] ) * ( c4[2] - c1[2] ) -
                 ( c3[0] - c1[0] ) * ( c2[1] - c1[1] ) * ( c4[2] - c1[2] ) )


@Pyro5.api.expose
class Brick_3d_lin(Cell):
    """
    Unstructured 3d tetrahedral element with linear interpolation

    .. automethod:: _evalN
    """
    def __hash__(self): return id(self)

    def copy(self):
        """
        This will copy the receiver, making a deep copy of all atributes EXCEPT mesh attribute.

        :return: A deep copy of a receiver
        :rtype: Cell
        """
        return Brick_3d_lin(mesh=self.mesh, number=self.number, label=self.label, vertices=tuple(self.vertices))

    @classmethod
    def getGeometryType(cls):
        """
        Returns geometry type of receiver.

        :return: Returns geometry type of receiver
        :rtype: CellGeometryType
        """
        return cellgeometrytype.CGT_HEXAHEDRON

    def glob2loc(self, coords):
        """
        Converts global coordinate to local (area) coordinate.

        :param tuple coords: A coordinate in global system
        :return: local (area) coordinate
        :rtype: tuple
        """
        x = [0]*8
        y = [0]*8
        z = [0]*8
        for i in range(8):
            c = self.mesh.getVertex(self.vertices[i])
            x[i] = c.coords[0]
            y[i] = c.coords[1]
            z[i] = c.coords[2]

        xp = coords[0]
        yp = coords[1]
        zp = coords[2]

        a1 = +x[0] + x[1] + x[2] + x[3] + x[4] + x[5] + x[6] + x[7]
        a2 = -x[0] - x[1] + x[2] + x[3] - x[4] - x[5] + x[6] + x[7]
        a3 = -x[0] + x[1] + x[2] - x[3] - x[4] + x[5] + x[6] - x[7]
        a4 = +x[0] + x[1] + x[2] + x[3] - x[4] - x[5] - x[6] - x[7]
        a5 = +x[0] - x[1] + x[2] - x[3] + x[4] - x[5] + x[6] - x[7]
        a6 = -x[0] - x[1] + x[2] + x[3] + x[4] + x[5] - x[6] - x[7]
        a7 = -x[0] + x[1] + x[2] - x[3] + x[4] - x[5] - x[6] + x[7]
        a8 = +x[0] - x[1] + x[2] - x[3] - x[4] + x[5] - x[6] + x[7]

        b1 = +y[0] + y[1] + y[2] + y[3] + y[4] + y[5] + y[6] + y[7]
        b2 = -y[0] - y[1] + y[2] + y[3] - y[4] - y[5] + y[6] + y[7]
        b3 = -y[0] + y[1] + y[2] - y[3] - y[4] + y[5] + y[6] - y[7]
        b4 = +y[0] + y[1] + y[2] + y[3] - y[4] - y[5] - y[6] - y[7]
        b5 = +y[0] - y[1] + y[2] - y[3] + y[4] - y[5] + y[6] - y[7]
        b6 = -y[0] - y[1] + y[2] + y[3] + y[4] + y[5] - y[6] - y[7]
        b7 = -y[0] + y[1] + y[2] - y[3] + y[4] - y[5] - y[6] + y[7]
        b8 = +y[0] - y[1] + y[2] - y[3] - y[4] + y[5] - y[6] + y[7]

        c1 = +z[0] + z[1] + z[2] + z[3] + z[4] + z[5] + z[6] + z[7]
        c2 = -z[0] - z[1] + z[2] + z[3] - z[4] - z[5] + z[6] + z[7]
        c3 = -z[0] + z[1] + z[2] - z[3] - z[4] + z[5] + z[6] - z[7]
        c4 = +z[0] + z[1] + z[2] + z[3] - z[4] - z[5] - z[6] - z[7]
        c5 = +z[0] - z[1] + z[2] - z[3] + z[4] - z[5] + z[6] - z[7]
        c6 = -z[0] - z[1] + z[2] + z[3] + z[4] + z[5] - z[6] - z[7]
        c7 = -z[0] + z[1] + z[2] - z[3] + z[4] - z[5] - z[6] + z[7]
        c8 = +z[0] - z[1] + z[2] - z[3] - z[4] + z[5] - z[6] + z[7]

        # setup initial guess
        answer = [0.0]*3
        nite = 0

        # apply Newton-Raphson to solve the problem
        while True:
            nite = nite+1
            if nite > 10:
                if debug:
                    print("Brick_3d_lin :: global2local: no convergence after 10 iterations")
                return 0, (0., 0., 0.)

            u = answer[0]
            v = answer[1]
            w = answer[2]

            # compute the residual
            r = numpy.array([[a1 + u * a2 + v * a3 + w * a4 + u * v * a5 + u * w * a6 + v * w * a7 + u * v * w * a8 - 8.0 * xp],
                            [b1 + u * b2 + v * b3 + w * b4 + u * v * b5 + u * w * b6 + v * w * b7 + u * v * w * b8 - 8.0 * yp],
                            [c1 + u * c2 + v * c3 + w * c4 + u * v * c5 + u * w * c6 + v * w * c7 + u * v * w * c8 - 8.0 * zp]])

            # check for convergence
            rnorm = r[0][0]*r[0][0]+r[1][0]*r[1][0]+r[2][0]*r[2][0]
            if rnorm < 1.e-20:
                break  # sqrt(1.e-20) = 1.e-10

            p = numpy.array([[a2 + v * a5 + w * a6 + v * w * a8, a3 + u * a5 + w * a7 + u * w * a8, a4 + u * a6 + v * a7 + u * v * a8],
                             [b2 + v * b5 + w * b6 + v * w * b8, b3 + u * b5 + w * b7 + u * w * b8, b4 + u * b6 + v * b7 + u * v * b8],
                             [c2 + v * c5 + w * c6 + v * w * c8, c3 + u * c5 + w * c7 + u * w * c8, c4 + u * c6 + v * c7 + u * v * c8]])

            # solve for corrections
            delta = numpy.linalg.solve(p, r)

            # update guess
            answer[0] = answer[0]-delta[0][0]
            answer[1] = answer[1]-delta[1][0]
            answer[2] = answer[2]-delta[2][0]
            # print answer

        # return result
        for i in range(3):
            if answer[i] < (-1. - tolerance):
                return 0, tuple(answer)
            if answer[i] > (1. + tolerance):
                return 0, tuple(answer)
        # inside
        return 1, tuple(answer)

    def _evalN(self, lc):
        """
        Evaluates shape functions at given point (given in parametric coordinates)
        :param tuple lc: A local coordinate
        :return: shape function
        :rtype: tuple of float
        """
        return (0.125 * (1. - lc[0]) * (1. - lc[1]) * (1. + lc[2]),
                0.125 * (1. - lc[0]) * (1. + lc[1]) * (1. + lc[2]),
                0.125 * (1. + lc[0]) * (1. + lc[1]) * (1. + lc[2]),
                0.125 * (1. + lc[0]) * (1. - lc[1]) * (1. + lc[2]),
                0.125 * (1. - lc[0]) * (1. - lc[1]) * (1. - lc[2]),
                0.125 * (1. - lc[0]) * (1. + lc[1]) * (1. - lc[2]),
                0.125 * (1. + lc[0]) * (1. + lc[1]) * (1. - lc[2]),
                0.125 * (1. + lc[0]) * (1. - lc[1]) * (1. - lc[2]))

    def loc2glob(self, lc):
        """
        Converts local (parametric) coordinates to global ones

        :param tuple lc: A local coordinate
        :return: global coordinate
        :rtype: tuple
        """
        n = self._evalN(lc)
        x = 0
        y = 0
        z = 0
        for i in range(8):
            v = self.mesh.getVertex(self.vertices[i])
            x = x+n[i]*v.coords[0]
            y = y+n[i]*v.coords[1]
            z = z+n[i]*v.coords[2]
        return x, y, z

    def interpolate(self, point, vertexValues):
        """
        Interpolates given vertex values to a given point.

        :param tuple point: 1D/2D/3D position vector
        :param tuple vertexValues: A tuple containing vertex values
        :return: Interpolated value at a given point
        :rtype: tuple
        """
        (inside, ac) = self.glob2loc(point)
        n = self._evalN(ac)

        return tuple([n[0]*vertexValues[0][i]+n[1]*vertexValues[1][i]+n[2]*vertexValues[2][i]+n[3]*vertexValues[3][i]+n[4]*vertexValues[4][i]+n[5]*vertexValues[5][i]+n[6]*vertexValues[6][i]+n[7]*vertexValues[7][i] for i in range(len(vertexValues[0]))])

    def containsPoint(self, point):
        """
        Check if a cell contains a point.

        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if cell contains a given point
        :rtype: bool
        """
        (inside, ac) = self.glob2loc(point)
        return inside

    def getTransformationJacobian(self, coords):
        """
        Returns the transformation jacobian (the determinant of jacobian) of the receiver

        :param tuple coords: local (parametric) coordinates of the point
        :return: jacobian
        :rtype: float
        """
        u = coords[0]
        v = coords[1]
        w = coords[2]
        # dN/dksi
        dnu = (-0.125 * (1. - v) * (1. + w),
               -0.125 * (1. + v) * (1. + w),
               0.125 * (1. + v) * (1. + w),
               0.125 * (1. - v) * (1. + w),
               -0.125 * (1. - v) * (1. - w),
               -0.125 * (1. + v) * (1. - w),
               0.125 * (1. + v) * (1. - w),
               0.125 * (1. - v) * (1. - w))

        dnv = (-0.125 * (1. - u) * (1. + w),
               0.125 * (1. - u) * (1. + w),
               0.125 * (1. + u) * (1. + w),
               -0.125 * (1. + u) * (1. + w),
               -0.125 * (1. - u) * (1. - w),
               0.125 * (1. - u) * (1. - w),
               0.125 * (1. + u) * (1. - w),
               -0.125 * (1. + u) * (1. - w))

        dnw = (0.125 * (1. - u) * (1. - v),
               0.125 * (1. - u) * (1. + v),
               0.125 * (1. + u) * (1. + v),
               0.125 * (1. + u) * (1. - v),
               -0.125 * (1. - u) * (1. - v),
               -0.125 * (1. - u) * (1. + v),
               -0.125 * (1. + u) * (1. + v),
               -0.125 * (1. + u) * (1. - v))

        j11 = 0
        j12 = 0
        j13 = 0
        j21 = 0
        j22 = 0
        j23 = 0
        j31 = 0
        j32 = 0
        j33 = 0
        for i in range(8):
            v = self.mesh.getVertex(self.vertices[i])
            x = v.coords[0]
            y = v.coords[1]
            z = v.coords[2]
            j11 = j11+dnu[i]*x
            j12 = j12+dnu[i]*y
            j13 = j13+dnu[i]*z
            j21 = j21+dnv[i]*x
            j22 = j22+dnv[i]*y
            j23 = j23+dnv[i]*z
            j31 = j31+dnw[i]*x
            j32 = j32+dnw[i]*y
            j33 = j33+dnw[i]*z

        return j11*j22*j33+j21*j32*j13+j31*j12*j23-j13*j22*j31-j23*j32*j11-j33*j12*j21
