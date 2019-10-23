import sys
import importlib
import unittest
from types import ModuleType


class TestImporting(unittest.TestCase):
    def _import(self, name: str) -> ModuleType:
        module = importlib.import_module(name)

        try:
            sys.modules.pop(name)
        finally:
            del module

    def test_import(self):
        self._import('spotify')

    def test_import_sync(self):
        self._import('spotify.sync')

if __name__ == '__main__':
    unittest.main()
