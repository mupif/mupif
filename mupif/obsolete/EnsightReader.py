#!/usr/bin/env python
# -*- coding: utf-8 -*-

from builtins import range, object
import sys
sys.path.append('../')

try:
    import vtk
except ImportError:
    pass

from mupif import Timer
import numpy as np
from mupif import Mesh
#from mupif import VertexserverHost
from mupif import Cell
from mupif import Field
from mupif import FieldID
from mupif import ValueType

#debug flag
debug = 0

class EnsightReader(object):
    """
    Read ensight files with vertices, cells, fields. Why is there this version and version 2? Is this file obsolete?
    """

    def __init__(self):
        self.grid = None
        return

    def readVtkFile(self, fileName):
        """
        Read VTK file.
    
        :param str filename: Input filename
        """
        self.reader = vtk.vtkUnstructuredGridReader()
        self.reader.SetFileName(fileName)
        self.reader.Update()
        self.grid = self.reader.GetOutput()
        self.points = self.grid.GetPoints()

    def readEnsightFile(self, fileName):
        """
        Read Ensight file. Writes a VTK file with fileName+'.vtk'.
        :param str filename: Input filename
        """
        #read the ensight file
        reader = vtk.vtkGenericEnSightReader()
        reader.SetCaseFileName(fileName)
        reader.Update()

        output = reader.GetOutput()
        num_blocks =  output.GetNumberOfBlocks()  

        #blocks_unstructured is a list of objects of vtkUnstructuredGrid
        blocks_unstructured = []
        for i in range(num_blocks):
            blocks_unstructured.append(output.GetBlock(i))

        appendFilter = vtk.vtkAppendFilter()
        i = 0
        while i < len(blocks_unstructured):
            if(vtk.VTK_MAJOR_VERSION <= 5):
                appendFilter.AddInput(blocks_unstructured[i])
            else:
                appendFilter.AddInputData(blocks_unstructured[i])
            i=i+1
        appendFilter.Update();

        unstructuredGrid=vtk.vtkUnstructuredGrid()
        unstructuredGrid.ShallowCopy(appendFilter.GetOutput());
        w = vtk.vtkUnstructuredGridWriter()
        if(vtk.VTK_MAJOR_VERSION <= 5):
            w.SetInput(unstructuredGrid)
        else:
            w.SetInputData(unstructuredGrid)
        w.SetFileName(fileName+'.vtk')
        w.Write()
        self.readVtkFile(fileName+'.vtk')

    def getMesh (self, cellFilter):
        """
        Reads a mesh from Ensight file.
        :param tuple cellFilter: A tuple containing a list of eligible cell types (according to CellGeometryType)??

        :return: mesh
        :rtype: Mesh
        """

        mesh = Mesh.UnstructuredMesh()
        vertices=[]
        coords = np.zeros((3), dtype='f')
        for i in range(0, self.getNumberOfVertices()): 
            coords=self.getCoords(i,coords)
        tuple = (coords)
        vertices.append(Vertex.Vertex(i,i+1, tuple))

        cells = []
        for i in range(0, self.getNumberOfCells()):
            if (self.giveCellType(i) == 12 and self.giveCellType(i) in cellFilter):
                cells.append(Cell.Brick_3d_lin(mesh, i, i, (int(self.giveVertex(i,0)), int(self.giveVertex(i,1)), int(self.giveVertex(i,2)), int(self.giveVertex(i,3)), int(self.giveVertex(i,4)), int(self.giveVertex(i,5)), int(self.giveVertex(i,6)), int(self.giveVertex(i,7))) )) 
            elif (self.giveCellType(i) == 9 and self.giveCellType(i) in cellFilter):
                cells.append(Cell.Quad_2d_lin(mesh, i, i,(int(self.giveVertex(i,0)),int(self.giveVertex(i,1)),int(self.giveVertex(i,2)),int(self.giveVertex(i,3))) ))
        mesh.setup(vertices, cells)
        return mesh

    def getField(self, mesh, fileName, fieldName, vertexBasedFlag, cellFilter):
        """
        Extract field from Ensight file.
        
        :param Mesh mesh: A mesh
        :param str fileName: ???
        :param str fieldName: A name of a computed field
        :param bool vertexBasedFlag: Field is assigned to vertices directly???
        :param tuple cellFilter: A tuple containing a list of eligible cell types (according to CellGeometryType)??
        """
        values=[]
        if (vertexBasedFlag == True):
            for i in range(0, self.getNumberOfVertices()): 
                values.append ((self.giveValueAtPoint(fieldName, i), ))
        elif(vertexBasedFlag == False):
            for i in range(0, self.getNumberOfCells()):
                if (self.giveCellType(i) == 12 and self.giveCellType(i) in cellFilter):
                    alues.append ((self.giveValueAtCell(fieldName, i), ))
                elif (self.giveCellType(i) == 9 and self.giveCellType(i) in cellFilter):
                    values.append ((self.giveValueAtCell(fieldName, i), ))
        return Field.Field(mesh, FieldID.FID_Temperature, ValueType.ValueType.Scalar, None, None, values, Field.FieldType.FT_cellBased)
                    
    def giveValueAtPoint(self, fieldName, componentID):
        """
        Evaluate field value at a given Point??
        
        :param str fieldName: Name of unknown field
        :param int componentID: ???
        :return: ??
        :rtype: ??
        """
        uGrid = vtk.vtkUnstructuredGrid()
        uGrid.ShallowCopy(self.grid)
        return uGrid.GetPointData().GetScalars(fieldName).GetValue( componentID )

    def giveValueAtCell(self, fieldName, componentID):
        """
        Evaluate field value at a given Point??
        :param str fieldName: Name of unknown field
        :param int componentID: ???
        :return: ??
        :rtype: ??
        """
        uGrid = vtk.vtkUnstructuredGrid()
        uGrid.ShallowCopy(self.grid)
        return uGrid.GetCellData().GetScalars(fieldName).GetValue( componentID )

    def giveVectorAtPoint(self, fieldName, i):
        """
        Evaluate field value at a given Point??
        :param str fieldName: Name of unknown field
        :param int i: ???
        :return: ??
        :rtype: ??
        """
        uGrid = vtk.vtkUnstructuredGrid()
        uGrid.ShallowCopy(self.grid)
        return uGrid.GetPointData().GetVectors(fieldName).GetTuple3(i)

    def giveVectorAtCell(self, fieldName, i):
        """
        Evaluate field value at a given cell??
        :param str fieldName: Name of unknown field
        :param int i: ???
        :return: ??
        :rtype: ??
        """
        uGrid = vtk.vtkUnstructuredGrid()
        uGrid.ShallowCopy(self.grid)
        return uGrid.GetCellData().GetVectors(fieldName).GetTuple3(i)

    def giveTensorAtPoint(self, fieldName, i):
        """
        Evaluate field value at a given point
        :param str fieldName: Name of unknown field
        :param int i: ???
        :return: ??
        :rtype: ??
        """
        uGrid = vtk.vtkUnstructuredGrid()
        uGrid.ShallowCopy(self.grid)
        return uGrid.GetPointData().GetTensors(fieldName).GetTuple9(i)

    def giveTensorAtCell(self, fieldName, i):
        """
        Evaluate field value at a given cell ??
        :param str fieldName: Name of unknown field
        :param int i: ???
        :return: ??
        :rtype: ??
        """
        uGrid = vtk.vtkUnstructuredGrid()
        uGrid.ShallowCopy(self.grid)
        return uGrid.GetCellData().GetTensors(fieldName).GetTuple9(i)

    def getNumberOfCells(self):
        """
        Returns the number of Cells.
        :return: Number of cells
        :rtype: int
        """
        geomData = self.reader.GetOutput();
        numCells = geomData.GetNumberOfCells()
        return numCells;

    def getNumberOfVertices(self):
        """
        Returns the number of Vertices.
        :return: Number of vertices
        :rtype: int
        """
        geomData = self.reader.GetOutput();
        numPts = geomData.GetNumberOfPoints()
        return numPts;

    def getCoords(self, i, coords):
        """
        Get the xyz coordinate of the point
        :param int i: Point number??
        :param tuple coords: Coordinate of a point?? Why is here as input argument, should be return value instead??
        :return: Coordinates
        :rtype: tuple
        """
        if debug:
            with Timer.Timer() as t:
                coords=self.points.GetPoint(i)
            print('Request getCoords took %.03f sec.' % t.interval)
        else:
            coords=self.points.GetPoint(i)  
        return coords

    def getBounds(self, b):
        """
        ???
        """
        geomData = self.reader.GetOutput();
        geomData.ComputeBounds()  
        geomData.GetBounds(b)
        return b

    def giveCellDimension(self, i):
        """
        :return: Dimensions of a cell, e.g. length, width, thickness??
        :rtype: tuple??
        """
        geomData = self.reader.GetOutput();
        dim=geomData.GetCell(i).GetCellDimension()
        return dim

    def giveCellType(self, i):
        """
        :param int i: Cell number
        :return: CellType
        :rtype: int
        """
        geomData = self.reader.GetOutput();
        type=geomData.GetCellType(i)
        return type

    def giveNumberOfVertices(self, cellid):
        """
        :param int cellid: Cell number
        :return: Number of vertices
        :rtype: int
        """
        geomData = self.reader.GetOutput();
        PtIds = vtk.vtkIdList()  
        geomData.GetCellPoints(cellid, PtIds)
        return PtIds.GetNumberOfIds()

    def giveVertex(self, cellid, i):
        """
        :param int cellid: ??
        :param int i: ??
        :return: ID??
        :rtype: ??
        """
        geomData = self.reader.GetOutput();
        PtIds = vtk.vtkIdList()  
        geomData.GetCellPoints(cellid, PtIds)
        ID = PtIds.GetId(i)
        return ID
