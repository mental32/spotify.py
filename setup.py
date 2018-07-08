import re
from setuptools import setup

requirements = [
  'aiohttp'
]

def get_version():
  with open('spotify/__init__.py') as inf:
      match = re.search(r"((\d\.){2,5}\d)", inf.read(), re.MULTILINE)

      if match is None:
        inf.seek(0)
        version_tag = '__version__ = '

        for line in inf.readlines():
          if line.startswith(version_tag):
            return line[len(version_tag):].strip()

      if match is None:
          raise RuntimeError('Version could not be found.')

      return match.groups()[0]

setup(name='spotify.py',
      author='mental',
      url='https://github.com/mental32/spotify.py',
      version=get_version(),
      packages=['spotify', 'spotify.models'],
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
