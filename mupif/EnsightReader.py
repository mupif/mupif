#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')

from mupif import *
import vtk
from vtk import *
from mupif import Timer

#debug flag
debug = 0

class EnsightReader():

	def __init__(self):
		self.grid = None
		#self.nx = 0 #numberOfNodesX
		#self.ny = 0
		#self.nz = 0 
		#self.dim = 0 #dimension see mupif
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
		#print "numb : ", num_blocks

		#blocks_unstructured is a list of objects of vtkUnstructuredGrid
		blocks_unstructured = []
		for i in range(num_blocks):
			blocks_unstructured.append(output.GetBlock(i))
		#print "blocks :", blocks_unstructured   

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


	def readField (self, fileName, fieldName, componentID):
		# Read the source file.
		#self.reader = vtk.vtkUnstructuredGridReader()
		#self.reader.SetFileName(fileName)
		#self.reader.ReadAllScalarsOn()
		#self.reader.Update()

                uGrid = vtk.vtkUnstructuredGrid()
		uGrid.ShallowCopy(self.reader.GetOutput())
		#return uGrid.GetPointData().GetScalars(fieldName).GetValue( componentID )
		return uGrid.GetCellData().GetScalars(fieldName).GetValue( componentID )

                
        def giveValueAtPoint(self, fieldName, componentID):
		uGrid = vtk.vtkUnstructuredGrid()
		uGrid.ShallowCopy(self.grid)
		print componentID
		return uGrid.GetPointData().GetScalars(fieldName).GetValue( componentID )

	def giveValueAtCell(self, fieldName, cellID):
		uGrid = vtk.vtkUnstructuredGrid()
		uGrid.ShallowCopy(self.grid)
		print cellID
		return uGrid.GetCellData().GetScalars(fieldName).GetValue( componentID )

        def getNumberOfCells(self):
		"""Returns the number of Cells."""
		geomData = self.reader.GetOutput();
		numCells = geomData.GetNumberOfCells()
		print "number of cells : ", numCells
		return numCells;

	def getNumberOfVertices(self):
		geomData = self.reader.GetOutput();
		numPts = geomData.GetNumberOfPoints()
		print "number of points : ",numPts
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

	def giveCellDimension(self):
		geomData = self.reader.GetOutput();
		dim=geomData.GetCell(0).GetCellDimension()
		print "dim :",dim 
		return dim

	def giveCellType(self, i):
		geomData = self.reader.GetOutput();
		type=geomData.GetCellType(i)
		#print "type of cells: ", type
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
