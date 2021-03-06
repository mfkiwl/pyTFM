#!/usr/bin/env python

from setuptools import setup
import os
import platform



install_requires=['numpy' ,'cython','openpiv',
		      'scipy', 'scikit-image', 'matplotlib >= 2.1.2', 'tqdm', 'solidspy','clickpoints >= 1.9.6', "natsort"]

version='1.2' # adding a version file automatically
file_path=os.path.join(os.getcwd(),os.path.join("pyTFM","_version.py"))
with open(file_path,"w") as f:
	f.write("__version__ = '%s'"%version)

# installing openpiv from local .whl if we are on windows
local_openpiv = os.path.join(os.getcwd(),"local_dependencies","OpenPIV-0.20.8-cp37-cp37m-win_amd64.whl")
print('\033[92m'+"Identified operating system: ",platform.system() + '\033[0m')

try:
	if platform.system()=="Windows":
		print('\033[92m' + "installing openpiv from local wheel" + '\033[0m')
		print(local_openpiv)
		if os.system("pip install "+ local_openpiv)!=0: # checking if exit code 0 (successfull)
			raise Exception
		install_requires.remove('openpiv')
except Exception as e:
	print('\033[91m' + "Failed to install openpiv from local files")
	print("Error:", e)
	print("trying to install open piv from pip" + '\033[0m')


setup(
    name='pyTFM',
    packages=['pyTFM'],
    version=version,
    description='traction force microscopy and FEM analysis of cell sheets',
    url='https://pytfm.readthedocs.io/',
    download_url = 'https://github.com/fabrylab/pyTFM.git',
    author='Andreas Bauer',
    author_email='andreas.b.bauer@fau.de',
    license='',
    install_requires=install_requires,
    keywords = ['traction force microscopy', 'finite elements'],
    classifiers = [],
    include_package_data=True,
    )


	
