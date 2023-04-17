import Pyro5.api
from .property import Property, ConstantProperty
from .units import Quantity, Unit
import numpy as np


@Pyro5.api.expose
class TemporalProperty(Property):
    times: Quantity
    def __init__(self, **kw):
        super().__init__(**kw)
        self._check_times(self.times)
        self._check_consistency()

    def _check_times(self, times):
        if not (times.ndim == 1 and times.size > 1 and np.all(np.diff(times) > 0)):
            raise ValueError('times array must be 1D, with at least 2 elements and be strictly increasing.')
        try: self.times.to('s') # raise exception if not time dimension
        except Exception as e: raise ValueError('times does not have time units? ({e.message})')
    def _check_consistency(self):
        if np.any(self.times.shape[0]!=self.quantity.shape[0]): raise ValueError(f'*times* and *quantity* must have the same first dimension (times: {self.times.shape[0]}, quantity: {self.quantity.shape[0]})')

    def evaluate(self, time: Quantity):
        if self.times.shape[-1]<1: raise ValueError('No time points defined.')
        if time < self.times[0] or time > self.times[-1]:
            raise ValueError(f'time={time} not in range {self.times[0]}..{self.times[1]}')
        time2=time.to(self.times.unit).value
        import numpy.core.multiarray
        interpKw=dict(x=time2, xp=self.times.value, left=np.nan, right=np.nan)
        print(f'{self.quantity.ndim=}')
        if self.quantity.ndim==1: q=np.interp(fp=self.quantity,**interpKw)
        elif self.quantity.ndim==2:
            # interpolate by component; assemble new quality by elements
            qq=[np.interp(fp=self.quantity[:,i],**interpKw) for i in range(self.quantity.shape[1])]
            q=Quantity(value=[q.value for q in qq],unit=qq[0].unit)
        return Property(quantity=q, propID=self.propID, valueType=self.valueType)

