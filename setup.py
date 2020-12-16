from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tom-alerts-dash',
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
    use_scm_version=True,
    setup_requires=['setuptools_scm', 'wheel'],
    install_requires=[
        'tomtoolkit>=2.1.0',
        'django_plotly_dash==1.4.2',
        'dash-bootstrap-components==0.10.3',
        'whitenoise==5.2.0',
        'dpd-static-support',
        'django-bootstrap4',
    ],
    extras_require={
        'scimma': ['tom-scimma>=1.1.0'],
        'test': ['tom-scimma', 'factory_boy']
    },
    include_package_data=True,
)
