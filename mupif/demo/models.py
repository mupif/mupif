import os
import mupif
import mupif as mp
import Pyro5
import math
import numpy as np
import time as timeTime
import logging
import uuid

log = logging.getLogger('demo-models')


def getline(f):
    while True:
        line = f.readline()
        if line == '':
            raise mupif.apierror.APIError('Error: EOF reached in input file')
        elif line[0] != '#':
            return line


@Pyro5.api.expose
class ThermalModel(mupif.model.Model,extra='allow'):
    """ Simple stationary heat transport solver on rectangular domains"""

    def __init__(self, metadata=None):
        super().__init__(metadata=metadata)
        if metadata is None:
            MD = {
                "Name": "Stationary thermal problem",
                "ID": "Thermo-1",
                "Description": "Stationary heat conduction using finite elements on rectangular domain",
                "Version_date": "1.0.0, Feb 2019",
                "Geometry": "2D rectangle",
                "Boundary_conditions": "Dirichlet, Neumann",
                "Inputs": [
                    {
                        "Name": "edge temperature",
                        "Type": "mupif.Property",
                        "Required": False,
                        "Type_ID": "mupif.DataID.PID_Temperature",
                        "Units": "deg_C",
                        "Obj_ID": [
                            "Cauchy top",
                            "Cauchy bottom",
                            "Cauchy left",
                            "Cauchy right",
                            "Dirichlet top",
                            "Dirichlet bottom",
                            "Dirichlet left",
                            "Dirichlet right"
                        ],
                        "Set_at": "timestep",
                        "ValueType": "Scalar"
                    },
                    {
                        "Name": "Input file",
                        "Type": "mupif.PyroFile",
                        "Required": False,
                        "Type_ID": "mupif.DataID.ID_InputFile",
                        "Obj_ID": "input_file_thermal",
                        "Set_at": "initialization",
                        "Units": "",
                        "ValueType": "",
                    }
                ],
                "Outputs": [
                    {
                        "Name": "temperature",
                        "Type_ID": "mupif.DataID.FID_Temperature",
                        "Type": "mupif.Field",
                        "Units": "deg_C",
                        "ValueType": "Scalar"
                    },
                    {
                        "Name": "temperatureVTK",
                        "Type_ID": "mupif.DataID.ID_VTKFile",
                        "Type": "mupif.PyroFile",
                        "Units": "",
                        "ValueType": "",
                    },
                    {
                        "Name": "temperatureImage",
                        "Type_ID": "mupif.DataID.ID_Image",
                        "Type": "mupif.PyroFile",
                        "Units": "",
                        "ValueType": "",
                    }
                ],
                "Solver": {
                    "Software": "own",
                    "Type": "Finite elements",
                    "Accuracy": "Medium",
                    "Sensitivity": "Low",
                    "Complexity": "Low",
                    "Robustness": "High",
                    "Estim_time_step_s": 1,
                    "Estim_comp_time_s": 10.,
                    "Estim_execution_cost_EUR": 0.01,
                    "Estim_personnel_cost_EUR": 0.01,
                    "Required_expertise": "None",
                    "Language": "Python",
                    "License": "LGPL",
                    "Creator": "Borek Patzak",
                    "Version_date": "1.0.0, Feb 2019",
                    "Documentation": "Felippa: Introduction to finite element methods, 2004",
                },
                "Physics": {
                    "Type": "Continuum",
                    "Entity": "Finite volume",
                    "Equation": ["Heat balance"],
                    "Equation_quantities": ["Heat flow"],
                    "Relation_description": ["Fick's first law"],
                    "Relation_formulation": ["Flow induced by thermal gradient on isotropic material"],
                    "Representation": "Finite volumes"
                }
            }
            self.updateMetadata(MD)
        self.mesh = None
        self.morphologyType = None
        self.conductivity = mupif.property.ConstantProperty(
            value=1.,
            propID=mupif.DataID.PID_effective_conductivity,
            valueType=mupif.ValueType.Scalar,
            unit=mupif.U['W/(m K)']
        )
        self.tria = False

        self.tria = False
        self.dirichletModelEdges = []
        self.convectionModelEdges = []

        self.xl = 5
        self.yl = 1
        self.nx = 10
        self.ny = 4

        self.dirichletBCs = None
        self.convectionBC = None

        self.loc = None
        self.neq = 0  # number of unknowns
        self.pneq = 0  # number of prescribed equations (Dirichlet b.c.)

        self.volume = 0.0
        self.integral = 0.0

        self.T = None
        self.scaleInclusion = None
        self.r = None
        self.b = None
        self.bp = None

        self.input_file = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def readInput(self, filename, tria=False):
        self.tria = tria
        self.dirichletModelEdges = []
        self.convectionModelEdges = []

        lines = []
        try:
            for line in open(filename, 'r'):
                if not line.startswith('#'):
                    lines.append(line)
        except Exception as e:
            log.info('Current working directory is %s' % self.workDir)
            log.exception(e)
            raise

        line = lines.pop(0)
        size = line.split()
        self.xl = float(size[0])
        self.yl = float(size[1])
        log.info("Thermal problem's dimensions: (%g, %g)" % (self.xl, self.yl))
        line = lines.pop(0)
        ne = line.split()
        self.nx = int(ne[0])
        self.ny = int(ne[1])

        for iedge in range(4):
            line = lines.pop(0)
            # print (line)
            rec = line.split()
            edge = int(rec[0])
            code = rec[1] if len(rec) > 1 else ''
            temperature = float(rec[2]) if len(rec) > 2 else None
            if code == 'D':
                self.dirichletModelEdges.append((edge, temperature))
            elif code == 'C':
                h = float(rec[3])
                self.convectionModelEdges.append((edge, temperature, h))

        # print (self.convectionModelEdges)

        line = lines.pop(0)
        rec = line.split()
        if len(rec) > 0:
            if rec[0] == 'Inclusion':
                self.morphologyType = 'Inclusion'
                self.scaleInclusion = float(rec[1])

    def prepareTask(self):
        self.mesh = mupif.mesh.UnstructuredMesh()
        # generate a simple mesh here, either triangles or rectangles
        # self.xl = 0.5 # domain (0..xl)(0..yl)
        # self.yl = 0.3
        # self.nx = 10 # number of elements in x direction
        # self.ny = 10 # number of elements in y direction
        # self.dx = self.xl / self.nx
        # self.dy = self.yl / self.ny
        self.mesh = mupif.demo.meshgen((0., 0.), (self.xl, self.yl), self.nx, self.ny, self.tria)

        #
        # Model edges
        #     ----------3----------
        #     |                   |
        #     4                   2
        #     |                   |
        #     ----------1---------
        #

        # self.dirichletModelEdges=(3,4,1)#
        self.dirichletBCs = {}  # key is node number, value is prescribed temperature
        for (ide, value) in self.dirichletModelEdges:
            # print ("Dirichlet", ide)
            if ide == 1:
                for i in range(self.nx + 1):
                    self.dirichletBCs[i * (self.ny + 1)] = value
            elif ide == 2:
                for i in range(self.ny + 1):
                    self.dirichletBCs[(self.ny + 1) * self.nx + i] = value
            elif ide == 3:
                for i in range(self.nx + 1):
                    self.dirichletBCs[self.ny + (self.ny + 1) * i] = value
            elif ide == 4:
                for i in range(self.ny + 1):
                    self.dirichletBCs[i] = value

        # self.convectionModelEdges=(2,)
        self.convectionBC = []
        for (ice, value, h) in self.convectionModelEdges:
            # print ("Convection", ice)
            if ice == 1:
                for i in range(self.nx):
                    if self.tria:
                        self.convectionBC.append((2 * self.ny * i, 0, h, value))
                    else:
                        self.convectionBC.append((self.ny * i, 0, h, value))
            elif ice == 2:
                for i in range(self.ny):
                    if self.tria:
                        self.convectionBC.append(((self.nx - 1) * 2 * self.ny + 2 * i, 1, h, value))
                    else:
                        self.convectionBC.append(((self.nx - 1) * self.ny + i, 1, h, value))
            elif ice == 3:
                for i in range(self.nx):
                    if self.tria:
                        self.convectionBC.append((2 * self.ny * (i + 1) - 1, 1, h, value))
                    else:
                        self.convectionBC.append((self.ny * (i + 1) - 1, 2, h, value))
            elif ice == 4:
                for i in range(self.ny):
                    if self.tria:
                        self.convectionBC.append((2 * i + 1, 2, h, value))
                    else:
                        self.convectionBC.append((i, 3, h, value))

        self.loc = np.zeros(self.mesh.getNumberOfVertices(), dtype=np.int32)
        self.neq = 0  # number of unknowns
        self.pneq = 0  # number of prescribed equations (Dirichlet b.c.)
        # print (self.mesh.getNumberOfVertices())
        for i in range(self.mesh.getNumberOfVertices()):
            # print(i)
            if i in self.dirichletBCs:
                self.pneq += 1
            else:
                self.neq += 1
        # print ("Neq", self.neq, "Pneq", self.pneq)
        # print(self.loc)
        ineq = 0  # unknowns numbering starts from 0..neq-1
        ipneq = self.neq  # prescribed unknowns numbering starts neq..neq+pneq-1

        for i in range(self.mesh.getNumberOfVertices()):
            if i in self.dirichletBCs:
                self.loc[i] = ipneq
                ipneq += 1
            else:
                self.loc[i] = ineq
                ineq += 1
        # print (self.loc)

    def get(self, objectTypeID, time=None, objectID=""):
        # Field
        if objectTypeID == mupif.DataID.FID_Temperature or objectTypeID == mupif.DataID.ID_VTKFile or objectTypeID == mupif.DataID.ID_Image:
            values = []
            for i in range(self.mesh.getNumberOfVertices()):
                if time.getValue() == 0.0:  # put zeros everywhere
                    values.append((0.,))
                else:
                    values.append((self.T[self.loc[i]],))
            return_field = mupif.field.Field(
                mesh=self.mesh,
                fieldID=mupif.DataID.FID_Temperature,
                valueType=mupif.ValueType.Scalar,
                unit=mupif.U.deg_C,
                time=time,
                value=values
            )
            if objectTypeID == mupif.DataID.FID_Temperature:
                return return_field
            if objectTypeID == mupif.DataID.ID_VTKFile:
                meshiofield = mupif.Field.manyToMeshioMesh([return_field])
                fn = './field_' + str(uuid.uuid4()) + '.vtk'
                meshiofield.write(fn)
                field_file = mp.PyroFile(filename=fn, mode="rb", dataID=mp.DataID.ID_VTKFile)
                if hasattr(self,'_pyroDaemon'): self._pyroDaemon.register(field_file)
                return field_file
            if objectTypeID == mupif.DataID.ID_Image:
                fn = './field_' + str(uuid.uuid4()) + '.png'
                return_field.plot2D(fileName=fn)
                field_file = mp.PyroFile(filename=fn, mode="rb", dataID=mp.DataID.ID_Image)
                if hasattr(self,'_pyroDaemon'): self._pyroDaemon.register(field_file)
                return field_file

        # Field
        elif objectTypeID == mupif.DataID.FID_Material_number:
            values = []
            for e in self.mesh.cells():
                if self.isInclusion(e) and self.morphologyType == 'Inclusion':
                    values.append((1,))
                else:
                    values.append((0,))
            # print (values)
            return mupif.field.Field(
                mesh=self.mesh,
                fieldID=mupif.DataID.FID_Material_number,
                valueType=mupif.ValueType.Scalar,
                unit=mp.U.none,
                time=time,
                value=values,
                fieldType=mupif.field.FieldType.FT_cellBased
            )

        # Property
        elif objectTypeID == mupif.DataID.PID_effective_conductivity:
            # average reactions from solution - use nodes on edge 4 (coordinate x==0.)
            sumQ = 0.
            for i in range(self.mesh.getNumberOfVertices()):
                coord = (self.mesh.getVertex(i).getCoordinates())
                if coord[0] < 1.e-6:
                    ipneq = self.loc[i]
                    if ipneq >= self.neq:
                        sumQ -= self.r[ipneq - self.neq]
            eff_conductivity = sumQ / self.yl * self.xl / (
                        self.dirichletBCs[(self.ny + 1) * (self.nx + 1) - 1] - self.dirichletBCs[0])
            return mupif.property.ConstantProperty(
                value=eff_conductivity,
                propID=mupif.DataID.PID_effective_conductivity,
                valueType=mupif.ValueType.Scalar,
                unit=mp.U['W/(m K)'],
                time=time
            )

        else:
            raise mupif.APIError('Unknown DataID')

    def isInclusion(self, e):
        vertices = e.getVertices()
        c1 = vertices[0].coords
        c2 = vertices[1].coords
        c3 = vertices[2].coords
        c4 = vertices[3].coords
        xCell = (c1[0] + c2[0] + c3[0] + c4[0]) / 4.  # vertex center
        yCell = (c1[1] + c2[1] + c3[1] + c4[1]) / 4.  # vertex center
        radius = min(self.xl, self.yl) * self.scaleInclusion
        xCenter = self.xl / 2.  # domain center
        yCenter = self.yl / 2.  # domain center
        if math.sqrt((xCell - xCenter) * (xCell - xCenter) + (yCell - yCenter) * (yCell - yCenter)) < radius:
            return True
            # print (xCell,yCell)
        return False

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.prepareTask()
        mesh = self.mesh
        self.volume = 0.0
        self.integral = 0.0

        # numNodes = mesh.getNumberOfVertices()
        numElements = mesh.getNumberOfCells()
        ndofs = 4

        # print numNodes
        # print numElements
        # print ndofs

        start = timeTime.time()
        log.info(self.getApplicationSignature())
        log.info("Number of equations: %d" % self.neq)

        # connectivity
        c = np.zeros((numElements, 4), dtype=np.int32)
        for e in range(0, numElements):
            for i in range(0, 4):
                c[e, i] = self.mesh.getVertex(mesh.getCell(e).vertices[i]).label
        # print "connectivity :",c

        # Global matrix and global vector
        kuu = np.zeros((self.neq, self.neq))
        kpp = np.zeros((self.pneq, self.pneq))
        kup = np.zeros((self.neq, self.pneq))
        # A = np.zeros((self.neq, self.neq ))
        b = np.zeros(self.neq)
        # solution vector
        self.T = np.zeros(self.neq + self.pneq)  # vector of temperatures

        # initialize prescribed Temperatures in current solution vector (T):
        for i in range(self.mesh.getNumberOfVertices()):
            if i in self.dirichletBCs:
                ii = self.loc[i]
                self.T[ii] = self.dirichletBCs[i]  # assign temperature

        log.info("Assembling ...")
        for e in mesh.cells():
            A_e = self.compute_elem_conductivity(e, self.conductivity.getValue(tstep.getTime()))

            # Assemble
            for i in range(ndofs):  # loop of dofs
                ii = self.loc[c[e.number - 1, i]]  # code number
                if ii < self.neq:  # unknown to be solved
                    for j in range(ndofs):
                        jj = self.loc[c[e.number - 1, j]]
                        if jj < self.neq:
                            kuu[ii, jj] += A_e[i, j]
                        else:
                            kup[ii, jj - self.neq] += A_e[i, j]
                else:  # prescribed value
                    for j in range(ndofs):
                        jj = self.loc[c[e.number - 1, j]]
                        if jj >= self.neq:
                            kpp[ii - self.neq, jj - self.neq] += A_e[i, j]

        # print (A)
        # print (b)

        # add boundary terms
        # print ('Convection BC', self.convectionBC)
        for i in self.convectionBC:
            # print "Processing bc:", i
            elem = mesh.getCell(i[0])
            side = i[1]
            h = i[2]
            Te = i[3]
            # print ("h:%f Te:%f" % (h, Te))

            n1 = elem.getVertices()[side]
            # print n1
            if side == 3:
                n2 = elem.getVertices()[0]
            else:
                n2 = elem.getVertices()[side + 1]

            length = math.sqrt((n2.coords[0] - n1.coords[0]) * (n2.coords[0] - n1.coords[0]) +
                               (n2.coords[1] - n1.coords[1]) * (n2.coords[1] - n1.coords[1]))

            # print h, Te, length

            # boundary_lhs=h*(np.dot(N.T,N))
            boundary_lhs = np.zeros((2, 2))
            if self.tria:
                boundary_lhs[0, 0] = h * (1. / 4.) * length
                boundary_lhs[0, 1] = h * (1. / 4.) * length
                boundary_lhs[1, 0] = h * (1. / 4.) * length
                boundary_lhs[1, 1] = h * (1. / 4.) * length
            else:
                boundary_lhs[0, 0] = h * (1. / 3.) * length
                boundary_lhs[0, 1] = h * (1. / 6.) * length
                boundary_lhs[1, 0] = h * (1. / 6.) * length
                boundary_lhs[1, 1] = h * (1. / 3.) * length

            # boundary_rhs=h*Te*N.T
            boundary_rhs = np.zeros((2, 1))
            boundary_rhs[0] = h * (1. / 2.) * length * Te
            boundary_rhs[1] = h * (1. / 2.) * length * Te

            # #Assemble
            loci = [n1.number, n2.number]
            # print loci
            for i_i in range(2):  # loop nb of dofs
                ii = self.loc[loci[i_i]]
                if ii < self.neq:
                    for j in range(2):
                        jj = self.loc[loci[j]]
                        if jj < self.neq:
                            # print "Assembling bc ", ii, jj, boundary_lhs[i,j]
                            kuu[ii, jj] += boundary_lhs[i_i, j]
                    b[ii] += boundary_rhs[i_i]

        self.r = np.zeros(self.pneq)  # reactions

        # solve linear system
        log.info("Solving thermal problem")

        rhs = b - np.dot(kup, self.T[self.neq:self.neq + self.pneq])
        self.T[:self.neq] = np.linalg.solve(kuu, rhs)
        self.r = np.dot(kup.transpose(), self.T[:self.neq]) + np.dot(kpp, self.T[self.neq:self.neq + self.pneq])
        # print (self.r)

        log.info("Done")
        log.info("Time consumed %f s" % (timeTime.time() - start))

    def compute_B(self, elem, lc):
        # computes gradients of shape functions of given element
        vertices = elem.getVertices()
        dNdksi = None
        B = np.zeros((2, 2))

        if isinstance(elem, mupif.cell.Quad_2d_lin):
            c1 = vertices[0].coords
            c2 = vertices[1].coords
            c3 = vertices[2].coords
            c4 = vertices[3].coords

            B11 = 0.25 * (c1[0] - c2[0] - c3[0] + c4[0])
            B12 = 0.25 * (c1[0] + c2[0] - c3[0] - c4[0])
            B21 = 0.25 * (c1[1] - c2[1] - c3[1] + c4[1])
            B22 = 0.25 * (c1[1] + c2[1] - c3[1] - c4[1])

            C11 = 0.25 * (c1[0] - c2[0] + c3[0] - c4[0])
            C12 = 0.25 * (c1[0] - c2[0] + c3[0] - c4[0])
            C21 = 0.25 * (c1[1] - c2[1] + c3[1] - c4[1])
            C22 = 0.25 * (c1[1] - c2[1] + c3[1] - c4[1])

            # local coords
            ksi = lc[0]
            eta = lc[1]

            B[0, 0] = (1. / elem.getTransformationJacobian(lc)) * (B22 + ksi * C22)
            B[0, 1] = (1. / elem.getTransformationJacobian(lc)) * (-B21 - eta * C21)
            B[1, 0] = (1. / elem.getTransformationJacobian(lc)) * (-B12 - ksi * C12)
            B[1, 1] = (1. / elem.getTransformationJacobian(lc)) * (B11 + eta * C11)

            dNdksi = np.zeros((2, 4))
            dNdksi[0, 0] = 0.25 * (1. + eta)
            dNdksi[0, 1] = -0.25 * (1. + eta)
            dNdksi[0, 2] = -0.25 * (1. - eta)
            dNdksi[0, 3] = 0.25 * (1. - eta)
            dNdksi[1, 0] = 0.25 * (1. + ksi)
            dNdksi[1, 1] = 0.25 * (1. - ksi)
            dNdksi[1, 2] = -0.25 * (1. - ksi)
            dNdksi[1, 3] = -0.25 * (1. + ksi)

        elif isinstance(elem, mupif.cell.Triangle_2d_lin):
            c1 = vertices[0].coords
            c2 = vertices[1].coords
            c3 = vertices[2].coords
            # local coords
            # ksi = lc[0]
            # eta = lc[1]

            B[0, 0] = (1. / elem.getTransformationJacobian(lc)) * (c2[1] - c3[1])
            B[0, 1] = (1. / elem.getTransformationJacobian(lc)) * (-c1[1] + c3[1])
            B[1, 0] = (1. / elem.getTransformationJacobian(lc)) * (-c2[0] + c3[0])
            B[1, 1] = (1. / elem.getTransformationJacobian(lc)) * (c1[0] - c3[0])
            dNdksi = np.zeros((2, 3))
            dNdksi[0, 0] = 1  # N1=ksi, N2=eta, N3=1-ksi-eta
            dNdksi[0, 1] = 0
            dNdksi[0, 2] = -1
            dNdksi[1, 0] = 0
            dNdksi[1, 1] = 1
            dNdksi[1, 2] = -1

        Grad = np.dot(B, dNdksi)
        # print Grad
        return Grad

    def compute_elem_conductivity(self, e, k):
        # compute element conductivity matrix
        numVert = e.getNumberOfVertices()
        A_e = np.zeros((numVert, numVert))
        # b_e = np.zeros((numVert, 1))
        rule = mupif.integrationrule.GaussIntegrationRule()

        ngp = rule.getRequiredNumberOfPoints(e.getGeometryType(), 2)
        pnts = rule.getIntegrationPoints(e.getGeometryType(), ngp)

        # print "e : ",e.number-1
        # print "ngp :",ngp
        # print "pnts :",pnts

        for p in pnts:  # loop over ips
            detJ = e.getTransformationJacobian(p[0])
            # print "Jacobian: ",detJ

            dv = detJ * p[1]
            # print "dv :",dv

            # N = np.zeros((1, numVert))
            # tmp = e._evalN(p[0])
            # N = np.asarray(tmp)
            # print "N :",N

            # x = e.loc2glob(p[0])
            # print "global coords :", x

            # conductivity
            # k=self.conductivity.getValue()
            if self.morphologyType == 'Inclusion':
                if self.isInclusion(e):
                    k = 0.001

            # Grad = np.zeros((2, numVert))
            Grad = self.compute_B(e, p[0])
            # print "Grad :",Grad
            K = k * dv * (np.dot(Grad.T, Grad))

            # Conductivity matrix
            for i in range(numVert):  # loop dofs
                for j in range(numVert):
                    A_e[i, j] += K[i, j]
        return A_e

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.PyroFile):
            if obj.getDataID() == mp.DataID.ID_InputFile:
                print("Downloading the input file..")
                mp.PyroFile.copy(obj, self.workDir + os.path.sep + 'tmin.in')
                print("Download finished.")
                self.readInput(self.workDir + os.path.sep + 'tmin.in')

        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mupif.DataID.PID_effective_conductivity:
                # remember the mapped value
                self.conductivity = obj.inUnitsOf('W/(m K)')
                # log.info("Assigning effective conductivity %f" % self.conductivity.getValue() )

            elif obj.getPropertyID() == mupif.DataID.PID_Temperature:

                # convection
                edge_ids = ['Cauchy bottom', 'Cauchy right', 'Cauchy top', 'Cauchy left']
                for edge_id in edge_ids:
                    if objectID == edge_id:
                        edge_index = edge_ids.index(edge_id)+1
                        edge_found = False
                        for edge in self.convectionModelEdges:
                            if edge[0] == edge_index:
                                idx = self.convectionModelEdges.index(edge)
                                self.convectionModelEdges[idx] = (edge_index, obj.getValue(), edge[2])
                                edge_found = True
                        if not edge_found:
                            self.convectionModelEdges.append((edge_index, obj.getValue(), 1.))

                # Dirichlet
                edge_ids = ['Dirichlet bottom', 'Dirichlet right', 'Dirichlet top', 'Dirichlet left']
                for edge_id in edge_ids:
                    if objectID == edge_id:
                        edge_index = edge_ids.index(edge_id)+1
                        edge_found = False
                        for edge in self.dirichletModelEdges:
                            if edge[0] == edge_index:
                                idx = self.dirichletModelEdges.index(edge)
                                self.dirichletModelEdges[idx] = (edge_index, obj.getValue())
                                edge_found = True
                        if not edge_found:
                            self.dirichletModelEdges.append((edge_index, obj.getValue()))

            else:
                raise mupif.apierror.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return 100*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Stationary thermal-demo-solver, ver 1.0"


@Pyro5.api.expose
class ThermalNonstatModel(ThermalModel,extra='allow'):
    """ Simple non-stationary (transient) heat transport solver on rectangular domains"""

    def __init__(self):
        metadata = {
            "Name": "Non-stationary thermal problem",
            "ID": "NonStatThermo-1",
            "Description": "Non-stationary heat conduction using finite elements on a rectangular domain",
            "Version_date": "1.0.0, Feb 2019",
            "Representation": "Finite volumes",
            "Geometry": "2D rectangle",
            "Boundary_conditions": "Dirichlet, Neumann",
            "Inputs": [
                {
                    "Name": "edge temperature",
                    "Type": "mupif.Property",
                    "Required": False,
                    "Type_ID": "mupif.DataID.PID_Temperature",
                    "Units": "deg_C",
                    "Obj_ID": [
                        "Cauchy top",
                        "Cauchy bottom",
                        "Cauchy left",
                        "Cauchy right",
                        "Dirichlet top",
                        "Dirichlet bottom",
                        "Dirichlet left",
                        "Dirichlet right"
                    ],
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                },
                {
                    "Name": "Input file",
                    "Type": "mupif.PyroFile",
                    "Required": False,
                    "Type_ID": "mupif.DataID.ID_InputFile",
                    "Obj_ID": "input_file_thermal_nonstat",
                    "Set_at": "initialization",
                    "Units": "",
                    "ValueType": "",
                }
            ],
            "Outputs": [
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "deg_C",
                    "ValueType": "Scalar"
                },
                {
                    "Name": "temperatureVTK",
                    "Type_ID": "mupif.DataID.ID_VTKFile",
                    "Type": "mupif.PyroFile",
                    "Units": "",
                    "ValueType": "",
                },
                {
                    "Name": "temperatureImage",
                    "Type_ID": "mupif.DataID.ID_Image",
                    "Type": "mupif.PyroFile",
                    "Units": "",
                    "ValueType": "",
                }
            ],
            "Solver": {
                "Software": "own",
                "Type": "Finite elements",
                "Accuracy": "Medium",
                "Sensitivity": "Low",
                "Complexity": "Low",
                "Robustness": "High",
                "Estim_time_step_s": 1,
                "Estim_comp_time_s": 100.,
                "Estim_execution_cost_EUR": 0.01,
                "Estim_personnel_cost_EUR": 0.01,
                "Required_expertise": "None",
                "Language": "Python",
                "License": "LGPL",
                "Creator": "Borek Patzak",
                "Version_date": "1.0.0, Feb 2019",
                "Documentation": "Felippa: Introduction to finite element methods, 2004",
            },
            "Physics": {
                "Type": "Continuum",
                "Entity": "Finite volume",
                "Equation": ["Heat balance"],
                "Equation_quantities": ["Heat flow"],
                "Relation_description": ["Fick's first law"],
                "Relation_formulation": ["Flow induced by thermal gradient on isotropic material"],
                "Representation": "Finite volumes"
            },
            "Execution": {
                'ID': '0',
                'Use_case_ID': '0',
                'Task_ID': '0'
            }
        }
        super().__init__(metadata=metadata)
        self.mesh = None
        self.capacity = 1.0  # J/kg/K
        self.density = 1.0
        self.Tau = 0.5
        self.init = True
        self.kuu = None
        self.kpp = None
        self.kup = None
        self.P = None
        self.Tp = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def getApplicationSignature(self):
        return "Nonstat-Thermal-demo-solver, ver 1.0"

    def finishStep(self, tstep):
        return

    def getCriticalTimeStep(self):
        return 100*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime() - tstep.getTimeIncrement() * self.Tau

    def compute_elem_capacity(self, e):
        # compute element capacity matrix
        numVert = e.getNumberOfVertices()
        A_e = np.zeros((numVert, numVert))
        rule = mupif.integrationrule.GaussIntegrationRule()

        ngp = rule.getRequiredNumberOfPoints(e.getGeometryType(), 2)
        pnts = rule.getIntegrationPoints(e.getGeometryType(), ngp)

        # print "e : ",e.number-1
        # print "ngp :",ngp
        # print "pnts :",pnts

        for p in pnts:  # loop over ips
            detJ = e.getTransformationJacobian(p[0])
            # print "Jacobian: ",detJ

            dv = detJ * p[1]
            # print "dv :",dv

            # N = np.zeros((1, numVert))
            tmp = e._evalN(p[0])
            N = np.asarray(tmp)
            # print "N :",N

            c = self.capacity * self.density
            if self.morphologyType == 'Inclusion':
                if self.isInclusion(e):
                    c = 0.001

            # C = np.zeros((numVert, numVert))
            C = c * dv * (np.dot(N.T, N))

            # Conductivity matrix
            A_e = np.add(A_e, C)
        return A_e

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.prepareTask()
        mesh = self.mesh
        self.volume = 0.0
        self.integral = 0.0
        dt = tstep.getTimeIncrement().inUnitsOf(mupif.U.s).getValue()

        if tstep.getNumber() == 0:  # assign mesh only for 0th time step
            return

        # numNodes = mesh.getNumberOfVertices()
        numElements = mesh.getNumberOfCells()

        ndofs = 3 if self.tria else 4

        # print numNodes
        # print numElements
        # print ndofs

        start = timeTime.time()
        log.info(self.getApplicationSignature())
        log.info("Number of equations: %d" % self.neq)
        # connectivity
        c = np.zeros((numElements, ndofs), dtype=np.int32)
        c.fill(-1)
        for e in range(0, numElements):
            numVert = self.mesh.getCell(e).getNumberOfVertices()
            for i in range(0, numVert):
                c[e, i] = self.mesh.getVertex(mesh.getCell(e).vertices[i]).label
        # print ('connectivity :',c)

        if self.init:  # do only once
            # Global matrix and global vector -> assuming constant time step size
            self.kuu = np.zeros((self.neq, self.neq))
            self.kpp = np.zeros((self.pneq, self.pneq))
            self.kup = np.zeros((self.neq, self.pneq))
            self.P = np.zeros((self.neq + self.pneq, self.neq + self.pneq))
            self.init = False

            log.info("Assembling ...")
            for e in mesh.cells():
                K_e = self.compute_elem_conductivity(e, self.conductivity.getValue(tstep.getTime()))
                C_e = self.compute_elem_capacity(e)
                A_e = K_e * self.Tau + C_e / dt
                P_e = np.subtract(C_e / dt, K_e * (1. - self.Tau))
                # Assemble
                for i in range(ndofs):  # loop of dofs
                    ii = self.loc[c[e.number - 1, i]]  # code number
                    if ii < self.neq:  # unknown to be solved
                        for j in range(ndofs):
                            jj = self.loc[c[e.number - 1, j]]
                            if jj < self.neq:
                                self.kuu[ii, jj] += A_e[i, j]
                            else:
                                self.kup[ii, jj - self.neq] += A_e[i, j]
                    else:  # prescribed value
                        for j in range(ndofs):
                            jj = self.loc[c[e.number - 1, j]]
                            if jj >= self.neq:
                                self.kpp[ii - self.neq, jj - self.neq] += A_e[i, j]

                    # rhs mtrx P=C/dt - K*(1-Tau)
                    for j in range(ndofs):
                        jj = self.loc[c[e.number - 1, j]]
                        self.P[ii, jj] += P_e[i, j]

            # add boundary terms
            # print ('convection BC', self.convectionBC)
            # exit(0)
            for i in self.convectionBC:
                # print "Processing bc:", i
                elem = mesh.getCell(i[0])
                side = i[1]
                h = i[2]
                # Te = i[3]
                # print ("h:%f Te:%f" % (h, Te))

                n1 = elem.getVertices()[side]
                n2 = elem.getVertices()[0 if side + 1 == elem.getNumberOfVertices() else side + 1]

                length = math.sqrt((n2.coords[0] - n1.coords[0]) * (n2.coords[0] - n1.coords[0]) +
                                   (n2.coords[1] - n1.coords[1]) * (n2.coords[1] - n1.coords[1]))

                # print (h, Te, length)

                # boundary_lhs=h*(np.dot(N.T,N))
                boundary_lhs = np.zeros((2, 2))
                if self.tria:
                    boundary_lhs[0, 0] = h * (1. / 4.) * length
                    boundary_lhs[0, 1] = h * (1. / 4.) * length
                    boundary_lhs[1, 0] = h * (1. / 4.) * length
                    boundary_lhs[1, 1] = h * (1. / 4.) * length
                else:
                    boundary_lhs[0, 0] = h * (1. / 3.) * length
                    boundary_lhs[0, 1] = h * (1. / 6.) * length
                    boundary_lhs[1, 0] = h * (1. / 6.) * length
                    boundary_lhs[1, 1] = h * (1. / 3.) * length

                # Assemble
                loci = [n1.number, n2.number]
                # print loci
                for i_i in range(2):  # loop nb of dofs
                    ii = self.loc[loci[i_i]]
                    if ii < self.neq:
                        for j in range(2):
                            jj = self.loc[loci[j]]
                            if jj < self.neq:
                                # print "Assembling bc ", ii, jj, boundary_lhs[i_i,j]
                                self.kuu[ii, jj] += boundary_lhs[i_i, j] * self.Tau

                    for j in range(2):
                        jj = self.loc[loci[j]]
                        self.P[ii, jj] += boundary_lhs[i_i, j] * self.Tau

            self.T = np.zeros(self.neq + self.pneq)  # vector of current prescribed temperatures
            self.b = np.zeros(self.neq)  # rhs vector

        # end self.init

        # update solution Tp = T
        # update rhs bp = b
        self.Tp = np.copy(self.T)
        self.bp = np.copy(self.b)

        # initialize prescribed Temperatures in current solution vector (T):
        for i in range(self.mesh.getNumberOfVertices()):
            if i in self.dirichletBCs:
                ii = self.loc[i]
                self.T[ii] = self.dirichletBCs[i]  # assign temperature

        # evaluate RHS
        # add boundary terms due to prescribed fluxes
        self.b = np.zeros(self.neq)
        for i in self.convectionBC:
            # print "Processing bc:", i
            elem = mesh.getCell(i[0])
            side = i[1]
            h = i[2]
            Te = i[3]
            # print ("h:%f Te:%f" % (h, Te))

            n1 = elem.getVertices()[side]
            # print n1
            n2 = elem.getVertices()[0 if side + 1 == elem.getNumberOfVertices() else side + 1]

            length = math.sqrt((n2.coords[0] - n1.coords[0]) * (n2.coords[0] - n1.coords[0]) +
                               (n2.coords[1] - n1.coords[1]) * (n2.coords[1] - n1.coords[1]))

            # print h, Te, length
            # boundary_rhs=h*Te*N.T
            boundary_rhs = np.zeros((2, 1))
            boundary_rhs[0] = h * (1. / 2.) * length * Te
            boundary_rhs[1] = h * (1. / 2.) * length * Te

            # #Assemble
            loci = [n1.number, n2.number]
            # print loci
            for i_i in range(2):  # loop nb of dofs
                ii = self.loc[loci[i_i]]
                if ii < self.neq:
                    self.b[ii] += boundary_rhs[i_i]

        rhs = self.b * self.Tau + self.bp * (1 - self.Tau)
        # add rhs due to previous state (C/dt-K(1-Tau))*r_{i-1}
        tmp = np.dot(self.P, self.Tp)  # contains all DOFs, extract unknown part and add it to rhs
        rhs = rhs + tmp[:self.neq]

        # add effect of dirichlet BCS
        rhs = np.subtract(rhs, np.dot(self.kup, self.T[self.neq:self.neq + self.pneq]))

        self.r = np.zeros(self.pneq)  # reactions
        # solve linear system
        log.info("Solving thermal nonstationary problem")
        self.T[:self.neq] = np.linalg.solve(self.kuu, rhs)  # inefficient, should reuse existing factorization !!!
        self.r = np.dot(self.kup.transpose(), self.T[:self.neq]) + np.dot(self.kpp,
                                                                          self.T[self.neq:self.neq + self.pneq])
        # print (self.r)

        log.info("Done")
        log.info("Time consumed %f s" % (timeTime.time() - start))


@Pyro5.api.expose
class MechanicalModel(mupif.model.Model,extra='allow'):
    """ Simple mechanical solver on 2D rectanglar domain (plane stress problem) """

    def __init__(self):
        metadata = {
            "Name": "Plane stress linear elastic",
            "ID": "Mechanical-1",
            "Description": "Plane stress problem with linear elastic thermo-elastic material",
            "Version_date": "1.0.0, Feb 2019",
            "Geometry": "2D rectangle",
            "Boundary_conditions": "Dirichlet",
            "Inputs": [
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "deg_C",
                    "Required": True,
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                },
                {
                    "Name": "Input file",
                    "Type": "mupif.PyroFile",
                    "Required": False,
                    "Type_ID": "mupif.DataID.ID_InputFile",
                    "Obj_ID": "input_file_mechanical",
                    "Set_at": "initialization",
                    "Units": "",
                    "ValueType": "",
                },
                {
                    "Name": "Prescribed displacement",
                    "Type": "mupif.Property",
                    "Required": False,
                    "Type_ID": "mupif.DataID.ID_Displacement",
                    "Units": "m",
                    "Obj_ID": [
                        "Dirichlet top",
                        "Dirichlet bottom",
                        "Dirichlet left",
                        "Dirichlet right"
                    ],
                    "Set_at": "initialization",
                    "ValueType": "Vector"
                }
            ],
            "Outputs": [
                {
                    "Name": "displacement",
                    "Type_ID": "mupif.DataID.FID_Displacement",
                    "Type": "mupif.Field",
                    "Units": "m",
                    "ValueType": "Vector"
                },
                {
                    "Name": "displacementVTK",
                    "Type_ID": "mupif.DataID.ID_VTKFile",
                    "Type": "mupif.PyroFile",
                    "Units": "",
                    "ValueType": "",
                },
                {
                    "Name": "displacementImage",
                    "Type_ID": "mupif.DataID.ID_Image",
                    "Type": "mupif.PyroFile",
                    "Units": "",
                    "ValueType": "",
                }
            ],
            "Solver": {
                "Software": "own",
                "Type": "Finite elements",
                "Accuracy": "Medium",
                "Sensitivity": "Low",
                "Complexity": "Low",
                "Robustness": "High",
                "Estim_time_step_s": 1,
                "Estim_comp_time_s": 100.,
                "Estim_execution_cost_EUR": 0.01,
                "Estim_personnel_cost_EUR": 0.01,
                "Required_expertise": "None",
                "Language": "Python",
                "License": "LGPL",
                "Creator": "Borek Patzak",
                "Version_date": "1.0.0, Feb 2019",
                "Documentation": "Felippa: Introduction to finite element methods, 2004",
            },
            "Physics": {
                "Type": "Continuum",
                "Entity": "Finite volume",
                "Equation": ["Equilibrium"],
                "Equation_quantities": ["Displacement"],
                "Relation_description": ["Hooke's law"],
                "Relation_formulation": ["Stress strain"],
                "Representation": "Finite volumes"
            },
            "Execution": {
                'ID': '0',
                'Use_case_ID': '0',
                'Task_ID': '0'
            },
        }
        super().__init__(metadata=metadata)
        self.E = 30.0e+9  # ceramics
        self.nu = 0.25  # ceramics
        self.fx = [0., 0., 0., 0.]  # load in x
        self.fy = [0., 0., 0., 0.]  # load in y
        self.temperatureField = None
        self.alpha = 12.e-6
        self.thick = 1.0

        self.dirichletModelEdges = []
        self.loadModelEdges = []

        self.xl = 5
        self.yl = 1
        self.nx = 20
        self.ny = 8

        self.mesh = None
        self.dirichletBCs = None
        self.loadBC = None
        self.loc = None
        self.neq = 0
        self.volume = 0.0
        self.integral = 0.0
        self.T = None

        self.input_file = None

        ns = mupif.pyroutil.connectNameserver()
        self.daemon = mupif.pyroutil.getDaemon(ns)

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.PyroFile):
            if obj.getDataID() == mp.DataID.ID_InputFile:
                print("Downloading the input file..")
                mupif.PyroFile.copy(obj, self.workDir + os.path.sep + 'smin.in')
                print("Download finished.")
                self.readInput(self.workDir + os.path.sep + 'smin.in')

        if obj.isInstance(mp.Field):
            if obj.getFieldID() == mupif.DataID.FID_Temperature:
                self.temperatureField = obj

        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mupif.DataID.ID_Displacement:
                # Dirichlet
                edge_ids = ['Dirichlet bottom', 'Dirichlet right', 'Dirichlet top', 'Dirichlet left']
                for edge_id in edge_ids:
                    if objectID == edge_id:
                        edge_index = edge_ids.index(edge_id)+1
                        self.dirichletModelEdges.append(edge_index) # value ignored

    def getCriticalTimeStep(self):
        return .4*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def readInput(self, filename):

        self.dirichletModelEdges = []
        self.loadModelEdges = []
        try:
            f = open(filename, 'r')
            # size
            line = getline(f)
            size = line.split()
            self.xl = float(size[0])
            self.yl = float(size[1])
            # mesh
            line = getline(f)
            ne = line.split()
            self.nx = int(ne[0])
            self.ny = int(ne[1])
            # Thickness
            rec = getline(f).split()
            self.thick = float(rec[0])
            # Young's modulus and Poissons' ratio
            rec = getline(f).split()
            self.E = float(rec[0])
            self.nu = float(rec[1])
            # thermal dilation
            rec = getline(f).split()
            self.alpha = float(rec[0])

            log.info("Mechanical problem's dimensions: (%g, %g)" % (self.xl, self.yl))

            for iedge in range(4):
                line = getline(f)
                rec = line.split()
                edge = int(rec[0])
                code = rec[1] if len(rec) > 1 else ''
                if code == 'D':
                    self.dirichletModelEdges.append(edge)
                elif code == 'C':
                    self.loadModelEdges.append(edge)
                    self.fx[iedge] = float(rec[2])
                    self.fy[iedge] = float(rec[3])

            # print(self.fx, self.fy)
            f.close()

        except Exception as e:
            log.exception(e)
            exit(1)

    def prepareTask(self):

        # self.mesh = mupif.mesh.UnstructuredMesh()
        # generate a simple mesh here
        # self.xl = 0.5 # domain (0..xl)(0..yl)
        # self.yl = 0.3
        # self.nx = 10 # number of elements in x direction
        # self.ny = 10 # number of elements in y direction
        # self.dx = self.xl / self.nx
        # self.dy = self.yl / self.ny
        self.mesh = mupif.demo.meshgen((0., 0.), (self.xl, self.yl), self.nx, self.ny)

        #
        # Model edges
        #     ----------3----------
        #     |                   |
        #     4                   2
        #     |                   |
        #     ----------1---------
        #

        # self.dirichletModelEdges=(3,4,1)#
        self.dirichletBCs = {}  # key is node number, value is prescribed displacement (zero supported only now)
        for ide in self.dirichletModelEdges:
            if ide == 1:
                for i in range(self.nx + 1):
                    self.dirichletBCs[i * (self.ny + 1)] = (0.0, 0.0, 0.0)
            elif ide == 2:
                for i in range(self.ny + 1):
                    self.dirichletBCs[self.nx * (self.ny + 1) + i] = (0.0, 0.0, 0.0)
            elif ide == 3:
                for i in range(self.nx + 1):
                    self.dirichletBCs[self.ny + i * (self.ny + 1)] = (0.0, 0.0, 0.0)
            elif ide == 4:
                for i in range(self.ny + 1):
                    self.dirichletBCs[i] = (0.0, 0.0, 0.0)

        # convectionModelEdges=(2,)
        self.loadBC = []
        for ice in self.loadModelEdges:
            if ice == 1:
                for i in range(self.nx):
                    self.loadBC.append((self.ny * i, 0, self.fx[ice - 1], self.fy[ice - 1]))
            elif ice == 2:
                for i in range(self.ny):
                    self.loadBC.append(((self.nx - 1) * self.ny + i, 1, self.fx[ice - 1], self.fy[ice - 1]))
            elif ice == 3:
                for i in range(self.nx):
                    self.loadBC.append((self.ny * (i + 1) - 1, 2, self.fx[ice - 1], self.fy[ice - 1]))
            elif ice == 4:
                for i in range(self.ny):
                    self.loadBC.append((i, 3, self.fx[ice - 1], self.fy[ice - 1]))

        self.loc = np.zeros((self.mesh.getNumberOfVertices(), 2), dtype=np.int32)  # Du, Dv dofs per node
        for i in self.dirichletBCs:
            self.loc[i, 0] = -1
            self.loc[i, 1] = -1
        self.neq = 0
        for i in range(self.mesh.getNumberOfVertices()):
            for j in range(2):  # loop over nodal DOFs
                if self.loc[i, j] >= 0:
                    self.loc[i, j] = self.neq
                    self.neq = self.neq + 1

        # print "loc:", self.loc

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mupif.DataID.FID_Displacement or objectTypeID == mupif.DataID.ID_VTKFile or objectTypeID == mupif.DataID.ID_Image:
            values = []
            for i in range(self.mesh.getNumberOfVertices()):
                if time.getValue() == 0.0:  # put zeros everywhere
                    values.append((0., 0., 0.))
                else:
                    if i in self.dirichletBCs:
                        values.append(self.dirichletBCs[i])
                    else:
                        values.append((self.T[self.loc[i, 0], 0], self.T[self.loc[i, 1], 0], 0.0))

            return_field = mupif.field.Field(
                mesh=self.mesh,
                fieldID=mupif.DataID.FID_Displacement,
                valueType=mupif.ValueType.Vector,
                unit=mp.U.m,
                time=time,
                value=values
            )
            if objectTypeID == mupif.DataID.FID_Displacement:
                return return_field
            if objectTypeID == mupif.DataID.ID_VTKFile:
                meshiofield = mupif.Field.manyToMeshioMesh([return_field])
                fn = './field_' + str(uuid.uuid4()) + '.vtk'
                meshiofield.write(fn)
                field_file = mp.PyroFile(filename=fn, mode="rb", dataID=mp.DataID.ID_VTKFile)
                if hasattr(self,'_pyroDaemon'): self._pyroDaemon.register(field_file)
                return field_file
            if objectTypeID == mupif.DataID.ID_Image:
                fn = './field_' + str(uuid.uuid4()) + '.png'
                return_field.plot2D(fileName=fn)
                field_file = mp.PyroFile(filename=fn, mode="rb", dataID=mp.DataID.ID_Image)
                if hasattr(self,'_pyroDaemon'): self._pyroDaemon.register(field_file)
                return field_file
        else:
            raise mupif.apierror.APIError('Unknown field ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.prepareTask()
        mesh = self.mesh
        if tstep and tstep.getNumber() == 0:  # assign mesh only for 0th time step
            return
        rule = mupif.integrationrule.GaussIntegrationRule()
        self.volume = 0.0
        self.integral = 0.0

        # numNodes = mesh.getNumberOfVertices()
        numElements = mesh.getNumberOfCells()
        elemNodes = 4
        nodalDofs = 2
        elemDofs = elemNodes * nodalDofs

        # print numNodes
        # print numElements
        # print ndofs

        start = timeTime.time()
        log.info(self.getApplicationSignature())
        log.info("Number of equations: %d" % self.neq)

        # connectivity
        c = np.zeros((numElements, elemNodes), dtype=np.int32)
        for e in range(0, numElements):
            for i in range(0, elemNodes):
                c[e, i] = self.mesh.getVertex(mesh.getCell(e).vertices[i]).label
        # print "connectivity :",c

        # Global matrix and global vector
        A = np.zeros((self.neq, self.neq))
        b = np.zeros((self.neq, 1))

        log.info("Assembling ...")
        for e in mesh.cells():
            # element matrix and element vector
            A_e = np.zeros((elemDofs, elemDofs))
            b_e = np.zeros((elemDofs, 1))

            ngp = rule.getRequiredNumberOfPoints(e.getGeometryType(), 2)
            pnts = rule.getIntegrationPoints(e.getGeometryType(), ngp)

            # print "e : ",e.number-1
            # print "ngp :",ngp
            # print "pnts :",pnts

            for p in pnts:  # loop over ips
                detJ = e.getTransformationJacobian(p[0])
                # print "Jacobian: ",detJ

                dv = detJ * p[1]
                # print "dv :",dv

                # N = np.zeros((1, elemNodes))
                # tmp = e._evalN(p[0])
                # N = np.asarray(tmp)
                # print "N :",N

                x = e.loc2glob(p[0])
                # print "global coords :", x

                k = 1.
                # Grad = np.zeros((3, elemDofs))
                Grad = self.compute_B(e, p[0])
                D = self.compute_D(self.E, self.nu)
                # print "Grad :",Grad
                # K = np.zeros((elemDofs, elemDofs))
                K = k * (np.dot(Grad.T, np.dot(D, Grad)))

                # Stiffness matrix
                for i in range(elemDofs):  # loop dofs
                    for j in range(elemDofs):
                        A_e[i, j] += K[i, j] * dv

                        # temperature load if temperature field registered
                if self.temperatureField is not None:
                    t = self.temperatureField.evaluate(x)
                    et = np.zeros((3, 1))
                    et[0] = self.alpha * t.getValue()[0]
                    et[1] = self.alpha * t.getValue()[0]
                    et[2] = 0.0
                    b_e += np.dot(Grad.T, np.dot(D, et)) * dv
            # print "A_e :",A_e
            # print "b_e :",b_e

            # Assemble
            for i in range(elemNodes):  # loop nb of dofs
                for idx in range(nodalDofs):
                    ii = int(self.loc[c[e.number - 1, i], idx])
                    if ii >= 0:
                        for j in range(elemNodes):
                            for jd in range(nodalDofs):
                                jj = int(self.loc[c[e.number - 1, j], jd])
                                if jj >= 0:
                                    # print "Assembling", ii, jj
                                    A[ii, jj] += A_e[i * nodalDofs + idx, j * nodalDofs + jd]
                        b[ii] += b_e[i * nodalDofs + idx]

                        # print A
        # print b

        # add boundary terms
        for i in self.loadBC:
            # print "Processing bc:", i
            elem = mesh.getCell(i[0])
            side = i[1]
            fx = i[2]  # specified as intensity per edge length [N/m]
            fy = i[3]  # specified as intensity per edge length [N/m]
            # print(fx,fy)

            n1 = elem.getVertices()[side]
            # print n1
            if side == 3:
                n2 = elem.getVertices()[0]
            else:
                n2 = elem.getVertices()[side + 1]

            length = math.sqrt((n2.coords[0] - n1.coords[0]) * (n2.coords[0] - n1.coords[0]) +
                               (n2.coords[1] - n1.coords[1]) * (n2.coords[1] - n1.coords[1]))

            # boundary_rhs=h*Te*N.T
            boundary_rhs = np.zeros((2, 2))
            boundary_rhs[0, 0] = (1. / 2.) * length * fx
            boundary_rhs[1, 0] = (1. / 2.) * length * fx
            boundary_rhs[0, 1] = (1. / 2.) * length * fy
            boundary_rhs[1, 1] = (1. / 2.) * length * fy

            # #Assemble
            loci = [n1.number, n2.number]
            # print loci
            for i_i in range(2):  # loop nb of nodes
                for idx in range(2):  # loop over dofs
                    ii = self.loc[loci[i_i], idx]
                    if ii >= 0:
                        b[ii] += boundary_rhs[i_i, idx]

                        # print A
        # print b

        # solve linear system
        log.info("Solving mechanical problem")
        self.T = np.linalg.solve(A, b)
        log.info("Done")
        log.info("Time consumed %f s" % (timeTime.time() - start))

    def compute_B(self, elem, lc):
        vertices = elem.getVertices()
        c1 = vertices[0].coords
        c2 = vertices[1].coords
        c3 = vertices[2].coords
        c4 = vertices[3].coords

        B11 = 0.25 * (c1[0] - c2[0] - c3[0] + c4[0])
        B12 = 0.25 * (c1[0] + c2[0] - c3[0] - c4[0])
        B21 = 0.25 * (c1[1] - c2[1] - c3[1] + c4[1])
        B22 = 0.25 * (c1[1] + c2[1] - c3[1] - c4[1])

        C11 = 0.25 * (c1[0] - c2[0] + c3[0] - c4[0])
        C12 = 0.25 * (c1[0] - c2[0] + c3[0] - c4[0])
        C21 = 0.25 * (c1[1] - c2[1] + c3[1] - c4[1])
        C22 = 0.25 * (c1[1] - c2[1] + c3[1] - c4[1])

        # local coords
        ksi = lc[0]
        eta = lc[1]

        B = np.zeros((2, 2))
        B[0, 0] = (1. / elem.getTransformationJacobian(lc)) * (B22 + ksi * C22)
        B[0, 1] = (1. / elem.getTransformationJacobian(lc)) * (-B21 - eta * C21)
        B[1, 0] = (1. / elem.getTransformationJacobian(lc)) * (-B12 - ksi * C12)
        B[1, 1] = (1. / elem.getTransformationJacobian(lc)) * (B11 + eta * C11)

        dNdksi = np.zeros((2, 4))
        dNdksi[0, 0] = 0.25 * (1. + eta)
        dNdksi[0, 1] = -0.25 * (1. + eta)
        dNdksi[0, 2] = -0.25 * (1. - eta)
        dNdksi[0, 3] = 0.25 * (1. - eta)
        dNdksi[1, 0] = 0.25 * (1. + ksi)
        dNdksi[1, 1] = 0.25 * (1. - ksi)
        dNdksi[1, 2] = -0.25 * (1. - ksi)
        dNdksi[1, 3] = -0.25 * (1. + ksi)

        # Grad = np.zeros((2, 4))
        Grad = np.dot(B, dNdksi)

        B = np.zeros((3, 8))
        B[0, 0] = Grad[0, 0]
        B[0, 2] = Grad[0, 1]
        B[0, 4] = Grad[0, 2]
        B[0, 6] = Grad[0, 3]

        B[1, 1] = Grad[1, 0]
        B[1, 3] = Grad[1, 1]
        B[1, 5] = Grad[1, 2]
        B[1, 7] = Grad[1, 3]

        B[2, 0] = Grad[1, 0]
        B[2, 1] = Grad[0, 0]
        B[2, 2] = Grad[1, 1]
        B[2, 3] = Grad[0, 1]
        B[2, 4] = Grad[1, 2]
        B[2, 5] = Grad[0, 2]
        B[2, 6] = Grad[1, 3]
        B[2, 7] = Grad[0, 3]

        return B

    def compute_D(self, E, nu):
        D = np.zeros((3, 3))
        ee = E / (1. - nu * nu)
        G = E / (2.0 * (1. + nu))

        D[0, 0] = ee
        D[0, 1] = nu * ee
        D[1, 0] = nu * ee
        D[1, 1] = ee
        D[2, 2] = G
        D = D * self.thick
        return D

    def getApplicationSignature(self):
        return "Mechanical-demo-solver, ver 1.0"
