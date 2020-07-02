from setuptools import setup, find_packages, Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension("ais.expand_c", ["ais/expand_cy.pyx"])
]

setup(
    name='expand_cy',
    packages=find_packages(),
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules,
    zip_safe=False,
)
