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


class _StrModel(pydantic.BaseModel):
    value: Union[str,Seq[str],Seq[Seq[str]],Seq[Seq[Seq[str]]],Seq[Seq[Seq[Seq[str]]]]]

@Pyro5.api.expose
class String(data.Data,DbDictable):
    """

    """

    value: NumpyArrayStr
    dataID: dataid.DataID


    @pydantic.validator('value')
    def value_validator(cls,v):
        return np.array(_StrModel.parse_obj({'value':v}).dict()['value'],dtype='str')

    def getValue(self):
        return self.value

    def getDataID(self):
        return self.dataID

    def to_db_dict_impl(self):
        return {
            'ClassName': 'String',
            'DataID': self.dataID.name,
            'Value': self.value.tolist()
        }

    @staticmethod
    def from_db_dict(d):
        return String(
            dataID=dataid.DataID[d['DataID']],
            value=d['Value'] # converted to np.array in the ctor
        )
