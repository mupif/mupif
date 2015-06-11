import sys
sys.path.append('../..')
import demoapp
import meshgen
from mupif import FieldID
from mupif import Field
from mupif import ValueType
from mupif import TimeStep
from mupif import PropertyID
from mupif import Mesh
from mupif import Vertex
from mupif import Cell

app = demoapp.thermal(None)
print app.getApplicationSignature()

sol = app.solveStep(TimeStep.TimeStep(0,1)) 
f = app.getField(FieldID.FID_Temperature, 0.0)
data = f.field2VTKData().tofile('example2')

import mayavi
#v = mayavi.mayavi() # create a MayaVi window
#v.open_vtk_data(data) # load the data from the vtkStructuredPoints object.
#f = v.load_filter('WarpScalar', 0)

from mayavi.plugins.app import main
# Note, this does not process any command line arguments.
mayavi = main()

d = mayavi.open('example2.vtk')
# Import a few modules.
from mayavi.modules.api import Outline, IsoSurface, Streamline

# Show an outline.
o = Outline()
mayavi.add_module(o)
o.actor.property.color = 1, 0, 0 # red color.

# Make a few contours.
iso = IsoSurface()
mayavi.add_module(iso)
iso.contour.contours = [450, 570]
