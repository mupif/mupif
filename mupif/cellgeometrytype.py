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


"""
Enumeration defining the supported cell geometries
"""
CGT_TRIANGLE_1 = 5  # linear triangle
CGT_QUAD = 9  # linear quad
CGT_TETRA = 10  # linear terahedra
CGT_HEXAHEDRON = 12  # linear hexahedron
CGT_TRIANGLE_2 = 22  # Quadratic triangle

cgt2numVerts = {CGT_TRIANGLE_1: 3, CGT_QUAD: 4, CGT_TETRA: 4, CGT_HEXAHEDRON: 8, CGT_TRIANGLE_2: 6}
# from: https://github.com/nschloe/meshio/blob/a6175e0d9dfb2aa274392d1cd396e991f0487cbc/src/meshio/xdmf/common.py#L71
cgt2xdmfIndex = {CGT_TRIANGLE_1: 0x04, CGT_QUAD: 0x05, CGT_TETRA: 0x06, CGT_HEXAHEDRON: 0x09, CGT_TRIANGLE_2: 0x24}
xdmfIndex2cgt = {v: k for k, v in cgt2xdmfIndex.items()}

meshioName2cgt = {'triangle': CGT_TRIANGLE_1, 'quad': CGT_QUAD, 'tetra': CGT_TETRA, 'hexahedron': CGT_HEXAHEDRON, 'triangle6': CGT_TRIANGLE_2}
