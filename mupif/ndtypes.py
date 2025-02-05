import warnings
from numpydantic import NDArray, Shape
from numpydantic.dtype import Float, Unicode

NumpyArray=NDArray[Shape['*, ...'],Float]
NumpyArrayStr=NDArray[Shape['*, ...'],Unicode]
NDArr1=NDArray[Shape["1"],Float]
NDArr2=NDArray[Shape["2"],Float]
NDArr2xX=NDArray[Shape["3,*"],Float]
NDArr3=NDArray[Shape["3"],Float]
NDArr4=NDArray[Shape["3"],Float]
NDArr6=NDArray[Shape["6"],Float]
NDArr6x2=NDArray[Shape["6,2"],Float]
NDArr8=NDArray[Shape["8"],Float]
NDArr3xX=NDArray[Shape["3,*"],Float]
NDArr123=NDArray[Shape["1-3"],Float]
NDArr23=NDArray[Shape["2-3"],Float]
NDArr123xX=NDArray[Shape['1-3,*'],Float]
NDArr123x3=NDArray[Shape['1-3,3'],Float]
# for vertex values type over elements (the 1-3 is for value type, but should be more generic for tensors etc)
NDArr3x123=NDArray[Shape['3,1-3'],Float]
NDArr4x123=NDArray[Shape['4,1-3'],Float]
NDArr6x123=NDArray[Shape['6,1-3'],Float]
NDArr8x123=NDArray[Shape['8,1-3'],Float]
