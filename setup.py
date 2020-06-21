# Install zeta trader package and its required packages.
import os
from setuptools import setup, find_packages

def readmepath(fname):
    return os.path.join(os.path.dirname(__file__), fname)

setup(name='zetatrader'
    , version='0.2dev'
    , author = 'Darren Yeap'
    , author_email = 'darren.yeap@outlook.com'
    , description = ("A algorithmic trading package for research, testing, and "
        "live trading.")
    , packages=find_packages()
    , install_requires=['wheel','numpy', 'scipy', 'matplotlib', 'pandas'
        ,'scikit-learn','ipython','pyzmq','pygments', 'patsy','statsmodels'
        ,'pyqt5==5.14', 'PyMySQL', 'lxml', 'mysql-connector-python','qtconsole'
        ,'jupyter', 'mplfinance']
    , long_description=open(readmepath('README.md')).read()
)

