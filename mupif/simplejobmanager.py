import warnings
warnings.warn("mupif.simplejobmanager module is deprecated, use mupif.modelserver instead.", DeprecationWarning, stacklevel=2)
from .modelserver import SimpleJobManager
__all__=['SimpleJobManager']

