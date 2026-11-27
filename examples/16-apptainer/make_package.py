"""
Build the model package of example 16: the container image and the package directory.

1. ``image.sif`` is built from ``image.def`` (``apptainer build --fakeroot``, no root needed; a few
   minutes, needs network), unless it exists.
2. ``package/`` is written: the model code (``model/``) and ``mupif-model.toml`` with
   ``Image = "file://<this directory>/image.sif"`` and its ``ImageDigest``.

The image is referenced by its path because the example runs on one host; on several hosts the path
would be on a shared file system (as on HPC systems), or the image would be pushed to an OCI
registry (``apptainer push image.sif oras://<registry>/<name>:<tag>``) and referenced as
``oras://<registry>/<name>@sha256:<digest>``. The digest is computed here: execution servers verify
the image against it, so that a changed image file is refused.

Usage: ``python make_package.py`` (or called by server.py).
"""
import hashlib
import os
import shutil
import subprocess
import sys

d = os.path.dirname(os.path.abspath(__file__))
IMAGE = os.path.join(d, 'image.sif')
PACKAGE = os.path.join(d, 'package')

MANIFEST = '''# Written by make_package.py: the image digest depends on the image built here.
ID = "mupif-example16"
Version = "1.0"
Entrypoint = "ex16model.model:Example16Model"
Description = "Example 16: a model in an Apptainer container image"
RequiresHost = []

[Runtime]
Type = "apptainer"
Image = "file://{image}"
ImageDigest = "{digest}"
'''


def apptainer() -> str:
    exe = os.environ.get('APPTAINER_EXE') or shutil.which('apptainer') or shutil.which('singularity')
    if not exe:
        sys.exit('apptainer (or singularity) not found: install it first (https://apptainer.org)')
    return exe


def build():
    """Build the image if needed and write the package; return the package directory."""
    if not os.path.exists(IMAGE):
        print(f'Building {IMAGE} from image.def (a few minutes) ...', flush=True)
        tmp = IMAGE + '.tmp'
        subprocess.run([apptainer(), 'build', '--force', '--fakeroot', tmp, os.path.join(d, 'image.def')], check=True)
        os.rename(tmp, IMAGE)
    with open(IMAGE, 'rb') as f:
        digest = 'sha256:' + hashlib.file_digest(f, 'sha256').hexdigest()
    shutil.rmtree(PACKAGE, ignore_errors=True)
    shutil.copytree(os.path.join(d, 'model'), PACKAGE, ignore=shutil.ignore_patterns('__pycache__'))
    with open(os.path.join(PACKAGE, 'mupif-model.toml'), 'w') as f:
        f.write(MANIFEST.format(image=IMAGE, digest=digest))
    print(f'Model package written to {PACKAGE} (image {digest})', flush=True)
    return PACKAGE


if __name__ == '__main__':
    build()
