import re
from setuptools import setup

requirements = [
  'aiohttp'
]

with open('README.md') as inf:
  long_description = inf.read()

def get_version():
  with open('spotify/__init__.py') as inf:
      match = re.search(r"((\d\.){2,5}\d)", inf.read(), re.MULTILINE)

      if match is None:
        # version regex broke
        # use a primitive search method
        inf.seek(0)
        version_tag = '__version__ = '
        version_tag_len = len(version_tag)

        for line in inf.readlines():
          if line[:version_tag_len] == version_tag:
            return line[version_tag_len:].strip()

      if match is None:
          raise RuntimeError('Version could not be found.')

      return match.groups()[0]

setup(name='spotify',
      author='mental',
      url='https://github.com/mental32/spotify.py',
      version=get_version(),
      packages=['spotify', 'spotify.models', 'spotify.sync'],
      license='MIT',
      description='spotify.py is an asynchronous API wrapper for Spotify written in Python.',
      long_description=long_description,
      include_package_data=True,
      install_requires=requirements,
      python_requires='>=3.5',
      classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)
