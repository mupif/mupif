import warnings
with warnings.catch_warnings():
    from numpydantic import NDArray, Shape
    warnings.simplefilter("ignore")
    import nptyping

NumpyArray=NDArray[Shape['*, ...'],nptyping.Floating]
NumpyArrayStr=NDArray[Shape['*, ...'],nptyping.Unicode]
NDArr1=NDArray[Shape["1"],nptyping.Floating]
NDArr2=NDArray[Shape["2"],nptyping.Floating]
NDArr2xX=NDArray[Shape["3,*"],nptyping.Floating]
NDArr3=NDArray[Shape["3"],nptyping.Floating]
NDArr4=NDArray[Shape["3"],nptyping.Floating]
NDArr6=NDArray[Shape["6"],nptyping.Floating]
NDArr6x2=NDArray[Shape["6,2"],nptyping.Floating]
NDArr8=NDArray[Shape["8"],nptyping.Floating]
NDArr3xX=NDArray[Shape["3,*"],nptyping.Floating]
NDArr123=NDArray[Shape["1-3"],nptyping.Floating]
NDArr23=NDArray[Shape["2-3"],nptyping.Floating]
NDArr123xX=NDArray[Shape['1-3,*'],nptyping.Floating]
NDArr123x3=NDArray[Shape['1-3,3'],nptyping.Floating]
# for vertex values type over elements (the 1-3 is for value type, but should be more generic for tensors etc)
NDArr3x123=NDArray[Shape['3,1-3'],nptyping.Floating]
NDArr4x123=NDArray[Shape['4,1-3'],nptyping.Floating]
NDArr6x123=NDArray[Shape['6,1-3'],nptyping.Floating]
NDArr8x123=NDArray[Shape['8,1-3'],nptyping.Floating]
