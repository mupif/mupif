#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')

import vtk
from mupif import Timer
import numpy as np
from mupif import Mesh
from mupif import Vertex
from mupif import Cell
from mupif import Field
from mupif import FieldID
from mupif import ValueType

#debug flag
debug = 0

class EnsightReader(object):

  def __init__(self):
    self.grid = None
    return

  def readVtkFile(self, fileName):
    self.reader = vtk.vtkUnstructuredGridReader()
    self.reader.SetFileName(fileName)
    self.reader.Update()
    self.grid = self.reader.GetOutput()
    self.points = self.grid.GetPoints()

  def readEnsightFile(self, fileName):
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
      appendFilter.AddInput(blocks_unstructured[i])
      i=i+1
    appendFilter.Update();

    unstructuredGrid=vtk.vtkUnstructuredGrid()
    unstructuredGrid.ShallowCopy(appendFilter.GetOutput());
    w = vtk.vtkUnstructuredGridWriter()
    w.SetInput(unstructuredGrid)
    w.SetFileName(fileName+'.vtk')
    w.Write()
    self.readVtkFile(fileName+'.vtk')


  def getMesh (self, cellFilter):
    mesh = Mesh.UnstructuredMesh()
    vertices=[]
    coords = np.zeros((3), dtype='f')
    for i in xrange(0, self.getNumberOfVertices()): 
      coords=self.getCoords(i,coords)
      tuple = (coords)
      vertices.append(Vertex.Vertex(i,i+1, tuple))

    cells = []
    for i in xrange(0, self.getNumberOfCells()):
      if (self.giveCellType(i) == 12 and self.giveCellType(i) in cellFilter):
        cells.append(Cell.Brick_3d_lin(mesh, i, i, (int(self.giveVertex(i,0)), int(self.giveVertex(i,1)), int(self.giveVertex(i,2)), int(self.giveVertex(i,3)), int(self.giveVertex(i,4)), int(self.giveVertex(i,5)), int(self.giveVertex(i,6)), int(self.giveVertex(i,7))) )) 
      elif (self.giveCellType(i) == 9 and self.giveCellType(i) in cellFilter):
        cells.append(Cell.Quad_2d_lin(mesh, i, i,(int(self.giveVertex(i,0)),int(self.giveVertex(i,1)),int(self.giveVertex(i,2)),int(self.giveVertex(i,3))) ))
                        
    mesh.setup(vertices, cells)
    return mesh

  def getField(self, mesh, fileName, fieldName, vertexBasedFlag, cellFilter):
    values=[]
    if (vertexBasedFlag == True):
      for i in xrange(0, self.getNumberOfVertices()): 
        values.append ((self.giveValueAtPoint(fieldName, i), ))
    elif(vertexBasedFlag == False):
      for i in xrange(0, self.getNumberOfCells()):
        if (self.giveCellType(i) == 12 and self.giveCellType(i) in cellFilter):
          values.append ((self.giveValueAtCell(fieldName, i), ))
        elif (self.giveCellType(i) == 9 and self.giveCellType(i) in cellFilter):
          values.append ((self.giveValueAtCell(fieldName, i), ))
    return Field.Field(mesh, FieldID.FID_Temperature, ValueType.Scalar, None, None, values, Field.FieldType.FT_cellBased)
                
  def giveValueAtPoint(self, fieldName, componentID):
    uGrid = vtk.vtkUnstructuredGrid()
    uGrid.ShallowCopy(self.grid)
    return uGrid.GetPointData().GetScalars(fieldName).GetValue( componentID )

  def giveValueAtCell(self, fieldName, componentID):
    uGrid = vtk.vtkUnstructuredGrid()
    uGrid.ShallowCopy(self.grid)
    return uGrid.GetCellData().GetScalars(fieldName).GetValue( componentID )

  def giveVectorAtPoint(self, fieldName, i):
    uGrid = vtk.vtkUnstructuredGrid()
    uGrid.ShallowCopy(self.grid)
    return uGrid.GetPointData().GetVectors(fieldName).GetTuple3(i)

  def giveVectorAtCell(self, fieldName, i):
    uGrid = vtk.vtkUnstructuredGrid()
    uGrid.ShallowCopy(self.grid)
    return uGrid.GetCellData().GetVectors(fieldName).GetTuple3(i)

  def giveTensorAtPoint(self, fieldName, i):
    uGrid = vtk.vtkUnstructuredGrid()
    uGrid.ShallowCopy(self.grid)
    return uGrid.GetPointData().GetTensors(fieldName).GetTuple9(i)

  def giveTensorAtCell(self, fieldName, i):
    uGrid = vtk.vtkUnstructuredGrid()
    uGrid.ShallowCopy(self.grid)
    return uGrid.GetCellData().GetTensors(fieldName).GetTuple9(i)

  def getNumberOfCells(self):
    """Returns the number of Cells."""
    geomData = self.reader.GetOutput();
    numCells = geomData.GetNumberOfCells()
    return numCells;

  def getNumberOfVertices(self):
    """Returns the number of Vertices."""
    geomData = self.reader.GetOutput();
    numPts = geomData.GetNumberOfPoints()
    return numPts;

  def getCoords(self, i, coords):
    #Get the xyz coordinate of the point
    if debug:
      with Timer.Timer() as t:
        coords=self.points.GetPoint(i)
      print('Request getCoords took %.03f sec.' % t.interval)
    else:
      coords=self.points.GetPoint(i)  
    return coords

  def getBounds(self, b):
    geomData = self.reader.GetOutput();
    geomData.ComputeBounds()  
    geomData.GetBounds(b)
    return b

  def giveCellDimension(self, i):
    geomData = self.reader.GetOutput();
    dim=geomData.GetCell(i).GetCellDimension()
    return dim

  def giveCellType(self, i):
    geomData = self.reader.GetOutput();
    type=geomData.GetCellType(i)
    return type

  def giveNumberOfVertices(self, cellid):
    geomData = self.reader.GetOutput();
    PtIds = vtk.vtkIdList()  
    geomData.GetCellPoints(cellid, PtIds)
    return PtIds.GetNumberOfIds()

  def giveVertex(self, cellid, i):
    geomData = self.reader.GetOutput();
    PtIds = vtk.vtkIdList()  
    geomData.GetCellPoints(cellid, PtIds)
    ID = PtIds.GetId(i)
    return ID
