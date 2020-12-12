from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tom-alerts-dash',
    version='1.0.0',
    description='Plotly Dash-based broker app for the TOM Toolkit',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://tom-toolkit.readthedocs.io',
    author='TOM Toolkit Project',
    author_email='dcollom@lco.global',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics'
    ],
    keywords=['tomtoolkit', 'astronomy', 'astrophysics', 'cosmology', 'science', 'fits', 'observatory'],
    packages=find_packages(),
    install_requires=[
        'tomtoolkit>=1.13.0a5',
        'django_plotly_dash==1.4.2',
        'dash-bootstrap-components==0.10.3',
        'whitenoise==5.2.0',
        'dpd-static-support',
        'django-bootstrap4',
    ],
    extras_require={
        'scimma': ['tom-scimma'],
        'antares': ['tom-antares'],
        'test': ['tom-scimma', 'tom-antares']
    },
    include_package_data=True,
)
