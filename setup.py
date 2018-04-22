import re
from setuptools import setup

with open('requirements.txt') as inf:
    requirements = inf.readlines()

with open('spotify/__init__.py') as inf:
    match = re.search(r"__version__ = '(\d\.\d\.\d(\.\d|)+)'", inf.read(), re.MULTILINE)

    if match is None:
        raise RuntimeError('Version could not be found.')

    version = match.groups()[0]

setup(name='spotify.py',
      author='mental',
      url='https://github.com/mental32/spotify.py',
      version=version,
      packages=['spotify'],
      license='MIT',
      description='spotify.py is an asynchronous API wrapper for Spotify written in Python.',
      include_package_data=True,
      install_requires=requirements,
      classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)
