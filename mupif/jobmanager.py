import warnings
warnings.warn("mupif.jobmanager module is deprecated, use mupif.modelserverbase instead.", DeprecationWarning, stacklevel=2)
from .modelserverbase import JobManager, RemoteJobManager,JobManException,JobManNoResourcesException, JOBMAN_OK, JOBMAN_NO_RESOURCES, JOBMAN_ERR
__all__=['JobManager','RemoteJobManager','JobManException','JobManNoResourcesException','JOBMAN_OK','JOBMAN_NO_RESOURCES','JOBMAN_ERR']
