import Pyro5.api
import typing
from typing import Union
from typing import Sequence as Seq
import pydantic
import numpy as np


from . import dataid
from . import data
from .baredata import NumpyArrayStr
from .dbrec import DbDictable
from .mupifquantity import ValueType


class _StrModel(pydantic.BaseModel):
    value: Union[str, Seq[str], Seq[Seq[str]], Seq[Seq[Seq[str]]], Seq[Seq[Seq[Seq[str]]]]]


@Pyro5.api.expose
class String(data.Data, DbDictable):
    """

    """

    value: NumpyArrayStr
    dataID: dataid.DataID
    valueType: ValueType = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.valueType is None:
            if len(self.value.shape) == 0:
                self.valueType = ValueType.Scalar
            elif len(self.value.shape) == 1:
                self.valueType = ValueType.Vector
            elif len(self.value.shape) == 2:
                self.valueType = ValueType.Tensor

    @pydantic.field_validator('value')
    def value_validator(cls, v):
        if isinstance(v,np.ndarray) and v.dtype.type==np.dtype('str').type: return v
        return np.array(_StrModel.model_validate({'value': v}).model_dump()['value'], dtype='str')

    def getValue(self):
        return self.value

    def getValueType(self):
        return self.valueType

    def getDataID(self):
        return self.dataID

    def to_db_dict_impl(self):
        return {
            'ClassName': 'String',
            'ValueType': self.valueType.name,
            'DataID': self.dataID.name,
            'Value': self.value.tolist()
        }

    @staticmethod
    def from_db_dict(d):
        return String(
            dataID=dataid.DataID[d['DataID']],
            value=d['Value'],  # converted to np.array in the ctor
            valueType=ValueType[d['ValueType']]
        )
