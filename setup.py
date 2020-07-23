from setuptools import setup, find_packages, Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension("ais.base_c", ["ais/base_cy.pyx"])
]

setup(
    name='base_cy',
    packages=find_packages(),
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules,
    zip_safe=False,
)
