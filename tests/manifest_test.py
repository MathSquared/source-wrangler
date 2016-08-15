import StringIO
import unittest

from sourcewrangler import manifest

class TestManifest(unittest.TestCase):
    def _manifest_from_string(self, string):
        buf = StringIO.StringIO(string)
        mf = manifest.Manifest(buf)
        return mf, buf

    def test_get(self):
        mf, buf = self._manifest_from_string("""
            [
                {"a": 1},
                {"a": 2, "b": 6},
                {"a": 3, "c": 5}
            ]
        """)
        obj = mf.get(1)
        self.assertEqual(obj, {"a": 2, "b": 6})
        buf.close()

    def test_values(self):
        mf, buf = self._manifest_from_string("""
            [
                {"foo": "bar", "bar": "baz"},
                {"foo": "baz", "baz": "bar"},
                {"bar": "quux", "quux": "foo"}
            ]
        """)
        vals = mf.values("foo")
        self.assertEqual(vals, set(["bar", "baz"]))
        buf.close()

    def test_search_exact(self):
        mf, buf = self._manifest_from_string("""
            [
                {"foo": "bar", "bar": "baz"},
                {"foo": "baz", "baz": "bar"},
                {"bar": "quux", "quux": "foo"},
                {"foo": "baz", "baz": "quux"}
            ]
        """)
        results = mf.search("foo", "baz", False)
        self.assertEqual(results, [1, 3])
        buf.close()

    def test_search_regex(self):
        mf, buf = self._manifest_from_string("""
            [
                {"foo": "bar", "bar": "baz"},
                {"foo": "baz", "baz": "bar"},
                {"bar": "quux", "quux": "foo"},
                {"foo": "foo", "baz": "quux"}
            ]
        """)
        results = mf.search("foo", "^ba.", True)
        self.assertEqual(results, [0, 1])
        buf.close()

    def test_add(self):
        mf, buf = self._manifest_from_string("""
            [
                {"a": 1},
                {"a": 2, "b": 6},
                {"a": 3, "c": 5}
            ]
        """)
        idx = mf.add({"a": 7})
        self.assertEqual(idx, 3)
        self.assertEqual(mf.get(idx), {"a": 7})
        buf.close()

    def test_replace(self):
        mf, buf = self._manifest_from_string("""
            [
                {"a": 1},
                {"a": 2, "b": 6},
                {"a": 3, "c": 5}
            ]
        """)
        mf.replace(2, {"a": 7})
        self.assertEqual(mf.get(2), {"a": 7})
        buf.close()
