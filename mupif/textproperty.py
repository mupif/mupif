import Pyro5.api
import typing
import pydantic

from . import dataid
from . import mupifobject


@Pyro5.api.expose
class TextProperty(mupifobject.MupifObject):
    """

    """

    value: typing.Text
    dataID: dataid.DataID

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)

    def getValue(self):
        return self.value

    def getDataID(self):
        return self.dataID

    def to_db_dict(self):
        return {
            'ClassName': 'TextProperty',
            'DataID': self.dataID.name,
            'Value': self.value
        }

    @staticmethod
    def from_db_dict(d):
        return TextProperty(
            dataID=dataid.DataID[d['DataID']],
            value=d['Value']
        )
