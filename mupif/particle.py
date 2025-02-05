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
import Pyro5
from . import data
from . import DataID

import typing
import pydantic


@Pyro5.api.expose
class Particle(data.Data):
    """
    Representation of particle. Particle is is object characterized by its position and other attributes.
    Particles are typically managed by ParticleSet. Particle class is convinience mapping to ParticleSet.
    """
    
    set: 'ParticleSet'  #: master particle set
    num: int  #: particle index

    def getPosition(self):
        """
        Returns particle position
        """
        return self.set.xc[self.num], self.set.yc[self.num], self.set.zc[self.num]

    def setPosition(self, position):
        """
        Sets particle position
        @param tuple position: position vector (x,y,z)
        """
        self.set.xc[self.num] = position[0]
        self.set.yc[self.num] = position[1]
        self.set.zc[self.num] = position[2]

    def getAttributes(self):
        """
        Returns attributes attached to particle
        @return dictionary of particle attributes
        """
        ans = {}
        for key in self.set.attributes:
            ans[key] = self.set.attributes[key][self.num]
        return ans

    def getAttribute(self, key):
        """
        Returns attribute identified by key
        @param str key: attribute key
        @raturn value associated with key, if not key present KeyError is raised
        """
        if key in self.set.attributes:
            return self.set.attributes[key][self.num]
        else:
            raise KeyError("No such attribute available")
    

@Pyro5.api.expose
class ParticleSet(data.Data):
    """
    Class representing a collection of Particles. The set stores particle data (positions) and attributes efficiently in the form of vectors.
    ParticleSet keeps position vector for each particle and optional attributes (user defined) identified by key for each particle.
    """

    id: DataID
    size: int                    #: number of particles in the set
    xc: typing.List[float] = []  #: array of particle x coordinates
    yc: typing.List[float] = []  #: array of particle y coordinates
    zc: typing.List[float] = []  #: array of particle z coordinates
    rvesize: float = 0
    inclusionsize: float = 0
    attributes: dict = pydantic.Field(default_factory=dict)  #: optional keyword arguments to define additional particle attributes, if type of values should be arrays with attribute values for each particle

    def getParticle(self, i):
        """
        Returns representation of i-th particle in the set
        """
        if i < self.size:
            return Particle(set=self, num=i)
        else:
            raise IndexError("Particle index out of range")

    def getID(self):
        return self.id

    def getParticlePositions(self):
        """
        Returns tuple containing position vectors of particles.
        """
        return self.xc, self.yc, self.zc

    def getParticleAttributes(self):
        """
        Returns dictionary of set attributes
        """
        return self.attributes

    def getParticleAttribute(self, key):
        """
        Returns array (tuple) of values corresponding to attribute identified by key
        """
        if key in self.attributes:
            return self.attributes[key]
        else:
            raise KeyError("No such attribute available")

    def getRveSize(self):
        """
        Returns RVE size of particle set
        """
        return self.rvesize

    def getInclusionSize(self):
        """
        Returns inclusion size of particle set
        """
        return self.inclusionsize
    

Particle.model_rebuild()


if __name__ == "__main__":
    ps = ParticleSet(1, 5, (0, 1, 2, 3, 4), (1, 2, 3, 4, 5), (2, 3, 4, 5, 6), alpha=(10, 11, 12, 13, 14))
    p2 = ps.getParticle(2)
    print(p2.getPosition())
    print(p2.getAttribute('alpha'))
