import dataclasses
from dataclasses import dataclass
from typing import Any, Optional, Annotated
import typing
import sys
import numpy as np
# backing storage
import h5py
import Pyro5.api
# metadata support
from .data import Data
from .mupifquantity import ValueType
from . import units, pyroutil, baredata
from . import dataid
from .property import Property
from .pyrofile import PyroFile
import types
import json
import tempfile
import logging
import os
import pydantic
import subprocess
import shutil

import atexit
import pydantic

log = logging.getLogger(__name__)


from .baredata import addPydanticInstanceValidator
addPydanticInstanceValidator(h5py.Dataset)

from .units import Quantity, RefQuantity
import astropy


class Hdf5RefQuantity(RefQuantity):
    'Quantity stored in HDF5 dataset, the HDF5 file being managed somewhere else.'
    # unit: astropy.units.UnitBase
    dataset: Annotated[typing.Optional[h5py.Dataset], pydantic.Field(exclude=True)] = None

    def __init__(self, *, unit=None, **kw):
        super().__init__(**kw)
        if self.dataset and unit:
            self.dataset.attrs['unit'] = str(unit)
        if not self.dataset and unit:
            raise ValueError(f'{unit=} cannot be specified without dataset (no storage for unit available)')

    # this will convert nicesly to arrays
    def __len__(self): return self.dataset.shape[0]

    class ValueRowAccessor(object):
        def __init__(self, refq): self.refq, self.shape = refq, refq.dataset.shape

        def __getitem__(self, row):
            ret = self.refq.dataset[row]
            ret.flags.writeable = False
            return ret

        def __setitem__(self, row: int, val):
            self.refq.dataset[row] = val

    class QuantityRowAccessor(object):
        def __init__(self, refq): self.refq, self.shape = refq, refq.dataset.shape

        def __getitem__(self, row):
            ret = self.refq.dataset[row]*units.Unit(self.refq.dataset.attrs['unit'])
            ret.flags.writeable = False
            return ret

        def __setitem__(self, row: int, q: units.Quantity):
            if not isinstance(q, units.Quantity):
                raise ValueError('quantity must be an instance of mupif.units.Quantity (not a {q.__class__.__name__})')
            self.refq.dataset[row] = q.to(self.refq.dataset.attrs['unit'])

    # def checkValue(self):
    #    import h5py
    #    if not isinstance(self.value,type(property5py.Dataset,Hdf5RefQuantity.ValueRowAccessor))

    def _ensureData(self):
        if self.dataset is None:
            raise ValueError('Dataset not allocated yet.')

    @property
    def value(self):
        self._ensureData()
        if len(self.dataset.shape) > 1:
            return Hdf5RefQuantity.ValueRowAccessor(self)
        return self.dataset

    @property
    def quantity(self):
        self._ensureData()
        if len(self.dataset.shape) > 1:
            return Hdf5RefQuantity.QuantityRowAccessor(self)
        return self.dataset

    @property
    def unit(self):
        self._ensureData()
        return units.Unit(self.dataset.attrs['unit'])

    @property
    def ndim(self):
        self._ensureData()
        return self.dataset.ndim

    @property
    def shape(self):
        self._ensureData()
        return self.dataset.shape

    # properties setters don't work with pydantic
    # thus the user can screw up easily
    # there is not much we can do really

    # @value.setter
    # def value(self, val):
    #     print('VALUE SETTER')
    #     raise ValueError

    # this is apparently never called, see https://stackoverflow.com/q/70966128
    # @value.setter
    # def value(self, val):
    #     print('VALUE SETTER', val)
    #     self.value_[:] = val
    # same as value.setter
    # @quantity.setter
    # def quantity(self,q): self.dataset[:]=q.to(self.unit)


HeavyDataBase_ModeChoice = typing.Literal['readonly', 'readwrite', 'overwrite', 'create', 'create-memory', 'copy-readwrite']


@Pyro5.api.expose
class HeavyDataBase(Data):
    """
    Base class for various HDF5-backed objects with automatic HDF5 transfer when copied to remote location. This class is to be used internally only.
    """
    h5path: str = ''
    h5uri: typing.Optional[str] = None
    mode: HeavyDataBase_ModeChoice = 'readonly'
    pyroIds: typing.List[str]=pydantic.Field([],exclude=True)

    def __init__(self, **kw):
        super().__init__(**kw)  # calls the real ctor
        self._h5obj = None  # _h5obj # normally assigned in openStorage
        self.pyroIds = []
        if self.h5uri is not None:
            log.info(f'HDF5 transfer: starting…\n')
            uri = Pyro5.api.URI(self.h5uri)
            remote = Pyro5.api.Proxy(uri)
            # sys.stderr.write(f'Remote is {remote}\n')
            fd, self.h5path = tempfile.mkstemp(suffix='.h5', prefix='mupif-tmp-', text=False)

            def _try_unlink():
                try:
                    os.unlink(self.h5path)
                except PermissionError:
                    pass  # can fail on Windows if the file is still open
            atexit.register(_try_unlink)
            log.debug(f'Temporary is {self.h5path}, will be deleted via atexit handler.')
            PyroFile.copy(remote, self.h5path)
            log.info(f'HDF5 transfer: finished, {os.stat(self.h5path).st_size} bytes.\n')
            # local copy is not the original, the URI is no longer valid
            self.h5uri = None

    def _returnProxy(self, v):
        if hasattr(self, '_pyroDaemon'):
            self._pyroDaemon.register(v)
            self.pyroIds.append(v._pyroId)
        return v

    def _ensureData(self, msg=None):
        if not self._h5obj:
            raise RuntimeError('Backing storage not open'+('' if msg is None else f' ({msg})')+'.')

    def allocateDataset(self, *, h5loc, shape, **kw):
        if not self._h5obj:
            self.openStorage()
        if h5loc in self._h5obj:
            raise RuntimeError(f'Dataset {h5loc} already exists (shape {"×".join(self._h5obj[h5loc].shape)}).')
        return self._h5obj.create_dataset(h5loc, shape=shape, **kw)

    @pydantic.validate_call
    def moveStorage(self, new_h5path):
        """
        Moves underlying storage in the filesystem to the new path *new_h5path*, and sets the ``h5path`` attribute to the new path.
        """
        if self._h5obj:
            raise RuntimeError(f'HDF5 file {self.h5path} open (must be closed before moving).')
        shutil.move(self.h5path, new_h5path)
        self.h5path = new_h5path

    @pydantic.validate_call
    def deepcopy(self):
        """
        Overrides BareData.deepcopy, enriching it with copy of the backing HDF5 file; it should correctly detect whether the call is local or remote.
        """
        if self._h5obj:
            raise RuntimeError(f'HDF5 file {self.h5path} open (must be closed before deepcopy).')
        # local
        if Pyro5.callcontext.current_context.client is None:
            fd, h5path_new = tempfile.mkstemp(suffix='.h5', prefix='mupif-tmp', text=False)
            shutil.copy(self.h5path, h5path_new)
            # creates new local object
            ret = super().deepcopy()
            ret.h5path = h5path_new
            return ret
        else:
            self.exposeData()
            return super().deepcopy()

    @pydantic.validate_call
    def openStorage(self, mode: typing.Optional[HeavyDataBase_ModeChoice] = None):
        """
        """
        if mode is not None:
            self.mode = mode
        # log.warning(f'Opening in mode {self.mode}')

        # for copy-readwrite, do the copy and let readwrite handle th rest
        if self.mode == 'copy-readwrite':
            if self._h5obj and self._h5obj.mode != 'r':
                raise RuntimeError(f'HDF5 file {self.h5path} open for writing (must be closed or read-only).')
            fd, h5path_new = tempfile.mkstemp(suffix='.h5', prefix='mupif-tmp', text=False)
            log.info('Using new temporary file {self.h5path}')
            import shutil
            shutil.copy(self.h5path, h5path_new)
            self.h5path = h5path_new
            self.mode = 'readwrite'

        if self.mode in ('readonly', 'readwrite'):
            if self.mode == 'readonly':
                if self._h5obj:
                    if self._h5obj.mode != 'r':
                        raise RuntimeError(f'HDF5 file {self.h5path} already open for writing.')
                else:
                    self._h5obj = h5py.File(self.h5path, 'r')
            elif self.mode == 'readwrite':
                if self._h5obj:
                    if self._h5obj.mode != 'r+':
                        raise RuntimeError(f'HDF5 file {self.h5path} already open read-only.')
                else:
                    if not os.path.exists(self.h5path):
                        raise RuntimeError(f'HDF5 file {self.h5path} does not exist (use mode="create" to create a new file.')
                    self._h5obj = h5py.File(self.h5path, 'r+')
        elif self.mode in ('overwrite', 'create', 'create-memory'):
            if self._h5obj:
                raise RuntimeError(f'HDF5 file {self.h5path} already open.')
            if self.mode == 'create-memory':
                import uuid
                doSave = bool(self.h5path)
                p = (self.h5path if doSave else str(uuid.uuid4()))
                if not doSave:
                    log.warning(f'Data will eventually disappear with mode="create-memory" and h5path="" (empty).')
                # hdf5 uses filename for lock management (even if the file is memory block only)
                # therefore pass if something unique if filename is not given
                self._h5obj = h5py.File(p, mode='x', driver='core', backing_store=doSave)
            else:
                assert self.mode in ('overwrite', 'create')
                # overwrite, create
                if useTemp := (not self.h5path):
                    fd, self.h5path = tempfile.mkstemp(suffix='.h5', prefix='mupif-tmp-', text=False)
                    log.info(f'Using new temporary file {self.h5path}')
                if self.mode == 'overwrite' or useTemp:
                    self._h5obj = h5py.File(self.h5path, 'w')
                # 'create' mode should fail if file exists already
                # it would fail also with new temporary file; *useTemp* is therefore handled as overwrite
                else:
                    self._h5obj = h5py.File(self.h5path, 'x')
            self.mode = 'readwrite'
        else:
            raise ValueError(f'Invalid mode {self.mode}: must be one of {HeavyDataBase_ModeChoice}')
        return self._h5obj

    def preDumpHook(self):
        # remote call will expose the data throgu the daemon so that the HDF5 container gets transferred automatically
        if Pyro5.callcontext.current_context.client is not None:
            self.exposeData()
        super().preDumpHook()

    def exposeData(self):
        """
        If *self* is registered in a Pyro daemon, the underlying HDF5 file will be exposed as well.
        This modifies the :obj:`h5uri` attribute which causes transparent download of the HDF5 file when the :obj:`HeavyDataBase` object is reconstructed remotely by Pyro (e.g. by using :obj:`BareData.copyRemote`).
        """
        if self._h5obj:
            raise RuntimeError('Cannot expose open HDF5 file. Call closeData() first.')
        if (daemon := getattr(self, '_pyroDaemon', None)) is None:
            raise RuntimeError(f'{self.__class__.__name__} not registered in a Pyro5.api.Daemon.')
        if self.h5uri:
            return  # already exposed
        # binary mode is necessary!
        # otherwise: remote UnicodeDecodeError somewhere, and then 
        # TypeError: a bytes-like object is required, not 'dict'
        self.h5uri = str(daemon.register(pf := PyroFile(filename=self.h5path, mode='rb')))
        self.pyroIds.append(pf._pyroId)

    # this seems to be breaking some other stuff, so leave it up to the user to close the data by hand
    # def __del__(self):
    #     if hasattr(self, '_h5obj'):
    #         self.closeData()

    def closeData(self):
        """
        * Flush and close the backing HDF5 file;
        * unregister all contexts from Pyro (if registered)
        """
        if self._h5obj:
            self._h5obj.close()
            self._h5obj = None
        if daemon := getattr(self, '_pyroDaemon', None):
            for i in self.pyroIds:
                # sys.stderr.write(f'Unregistering {i}\n')
                daemon.unregister(i)

    @pydantic.validate_call
    def cloneHandle(self, newPath: str = ''):
        """Return clone of the handle; the underlying storage is copied into *newPath* (or a temporary file, if not given). All handle attributes (besides :obj:`h5path`) are preserved."""
        if self._h5obj:
            raise RuntimeError(f'HDF5 file {self.h5path} is open (call closeData() first).')
        if not newPath:
            _fd, newPath = tempfile.mkstemp(suffix='.h5', prefix='mupif-tmp-', text=False)
        shutil.copy(self.h5path, newPath)
        ret = self.model_copy(deep=True)  # this is provided by pydantic
        ret.h5path = newPath
        return ret

    def repack(self):
        """Repack the underlying storage (experimental, untested). Data must not be open."""
        if self._h5obj:
            raise RuntimeError(f'Cannot repack while {self._h5obj} is open (call closeData first).')
        try:
            log.warning(f'Repacking {self.h5path} via h5repack [experimental]')
            out = self.h5path+'.~repacked~'
            subprocess.run(['h5repack', self.h5path, out], check=True)
            shutil.copy(out, self.h5path)
        except subprocess.CalledProcessError:
            log.warning('Repacking HDF5 file failed, unrepacked version was retained.')


HeavyDataBase.ModeChoice = HeavyDataBase_ModeChoice


class Hdf5OwningRefQuantity(Hdf5RefQuantity, HeavyDataBase):
    """Quantity stored in HDF5 dataset, managing the HDF5 file itself."""
    h5loc: str = '/quantity'

    def __init__(self, **kw):
        super().__init__(**kw)
        self._h5obj = None  # disappears??

    def allocateDataset(self, *, shape, unit, **kw):
        if self.dataset:
            raise RuntimeError(f'dataset is already assigned (shape {"×".join(self.dataset.shape)})')
        self.dataset = HeavyDataBase.allocateDataset(self, h5loc=self.h5loc, shape=shape, **kw)
        self.dataset.attrs['unit'] = str(unit)

    def makeRef(self):
        ret = Hdf5RefQuantity(dataset=self.dataset)
        return ret

    @staticmethod
    @pydantic.validate_call
    def makeFromQuantity(q: units.Quantity, h5path: str = '', h5loc: Optional[str] = '/quantity'):
        ret = Hdf5OwningRefQuantity(h5path=h5path, h5loc=h5loc, mode='create')
        ret.allocateDataset(shape=q.value.shape, unit=q.unit)
        ret.value[:] = q.value
        assert (q.value[:] == ret.value[:]).all()
        assert q.unit == ret.unit
        return ret

    def toQuantity(self):
        """Convert to "normal" (in-memory) quantity"""
        return units.Quantity(value=np.array(self.dataset), unit=self.unit)

    def reopenData(self, mode: typing.Optional[HeavyDataBase_ModeChoice] = None):
        self.closeData()
        self.openData(mode=mode)

    def openData(self, mode: typing.Optional[HeavyDataBase_ModeChoice] = None):
        self.openStorage(mode=mode)
        assert self._h5obj
        self.dataset = self._h5obj[self.h5loc]
        assert 'unit' in self.dataset.attrs
        # u=units.Unit(self.dataset.attrs['unit'])
        # if self.unit and u!=self.unit: raise RuntimeError(f'Inconsistent unit: instance has {str(self.unit)}, HDF5 file has {str(u)}')


class Hdf5HeavyProperty(Property, HeavyDataBase):
    dataset: Annotated[typing.Optional[h5py.Dataset], pydantic.Field(exclude=True)] = None
    def __init__(self, **kw):
        super().__init__(mode='create', **kw)

    @staticmethod
    def make(*, quantity, propID, valueType):
        ret = Hdf5HeavyProperty(quantity=quantity, propID=propID, valueType=valueType)
        ret.dataset = ret.allocateDataset(h5loc=propID.name, shape=quantity.value.shape)
        ret.dataset.attrs['unit'] = str(quantity.unit)
        ret.dataset.attrs['valueType'] = valueType.name
        ret.dataset[:] = quantity.value
        ret.quantity = Hdf5RefQuantity(dataset=ret.dataset)
        # ret.closeData() # reopenData(mode='readonly')
        return ret

    @staticmethod
    def loadFromHdf5(*, h5path):
        ret = Hdf5HeavyProperty(h5path=h5path, quantity=Quantity(0), propID=dataid.DataID.ID_None)
        ret.openStorage(mode='readonly')
        if (l := len(ret._h5obj.keys())) != 1:
            raise RuntimeError(f'HDF5 file must contain exactlyone dataset (not {l})')
        h5loc = list(ret._h5obj.keys())[0]
        ds = ret._h5obj[h5loc]
        ret.quantity = Hdf5RefQuantity(dataset=ds)
        ret.valueType = ValueType[ds.attrs['valueType']]
        ret.propID = dataid.DataID[h5loc]
        return ret


class HeavyConvertible(pydantic.BaseModel):
    # returns dataset index in h5grp
    def copyToHeavy(self,*,h5grp): raise NotImplementedError(f'Derived class {self.__class__.__name__} did not implment the method.')
    @classmethod
    def makeFromHeavy(klass,*,h5grp,indices):
        # TODO: decode which type is stored in h5grp
        assert issubclass(klass,HeavyConvertible)
        return klass.makeFromHdf5(h5group=h5grp,indices=indices,heavy=True)
