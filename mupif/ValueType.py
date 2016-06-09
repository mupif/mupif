"""
Enumeration defining supported types of field and property values, e.g. scalar, vector, tensor
"""
Scalar = 1
Vector = 2
Tensor = 3

def fromNumberOfComponents(i):
    '''
    :param int i: number of components
    :return: value type corresponding to the number of components
    
    RuntimeError is raised if *i* does not match any value known.
    '''
    if i==1: return Scalar
    elif i==3: return Vector
    elif i==9: return Tensor
    else: raise RuntimeError('No ValueType with %i components'%i)
