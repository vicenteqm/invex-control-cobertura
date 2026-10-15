import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'python'),str(Path(__file__).resolve().parents[1]/'.build-deps')]
from fuentes_tiendas import sync_base

class BaseSourceTests(unittest.TestCase):
    def test_invalid_source_preserves_previous_copy_and_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'updated.xlsx';source.write_bytes(b'invalid')
            dest=root/'inputs/fuentes/base_tiendas/BASE_TIENDAS_ACTUAL.xlsx';dest.parent.mkdir(parents=True);dest.write_bytes(b'previous')
            config={}
            with patch('fuentes_tiendas.is_base',return_value=False):
                with self.assertRaises(ValueError):sync_base(config,root,source)
            self.assertEqual(dest.read_bytes(),b'previous');self.assertEqual(config,{})

    def test_linked_file_refreshes_and_missing_source_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'updated.xlsx';source.write_bytes(b'first');config={}
            with patch('fuentes_tiendas.is_base',return_value=True):
                target=sync_base(config,root,source);self.assertEqual(target.read_bytes(),b'first')
                source.write_bytes(b'second');sync_base(config,root);self.assertEqual(target.read_bytes(),b'second')
                source.unlink()
                with self.assertRaises(ValueError):sync_base(config,root)
                self.assertEqual(target.read_bytes(),b'second')
