from __future__ import annotations
from .baredata import BareData
from typing import Union, Literal, Optional, Any
import pydantic

class DbDictable(BareData):
    def to_db_dict_impl(self): raise NotImplementedError(f'Classes derived from DbDictable must implement to_db_dict_impl. (class {self.__class__.__name__})')

    @pydantic.validate_call
    def to_db_dict(self, dialect: Optional[Literal['edm']] = None) -> dict[str, Any]:
        ret = self.to_db_dict_impl()
        edm_repl = {'Unit': 'unit', 'Value': 'value'}
        if dialect == 'edm':
            return {edm_repl.get(k, k): v for k, v in ret.items()}  # type: ignore
        return ret
    
    # def to_db_dict(self,dialect:Optional[Literal['edm']]=None):
    #     ret=self.to_db_dict_impl()
    #     edmRepl={'Unit':'unit','Value':'value'}
    #     if dialect=='edm': return dict([(edmRepl.get(k,k),v) for k,v in ret.items()])
    #     else: return ret

    @staticmethod
    @pydantic.validate_call
    def from_db_dict(d,dialect:Optional[Literal['edm']]=None):
        import mupif as mp
        edmRepl={'unit':'Unit','value':'Value'}
        if dialect=='edm': d=dict([(edmRepl.get(k,k),v) for k,v in d.items()])
        k=d['ClassName']
        if (klass:=getattr(mp,k,None)) is None or not isinstance(klass,type): raise RuntimeError(f'ClassName {klass} not found in mupif module, or not a class.')
        return klass.from_db_dict(d)

