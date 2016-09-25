import codecs
import json
import os
import re

class Manifest(object):
    """Represents the manifest for a given source folder.

    The ManifestFile class adds locking and autocommit features, while providing a compatible interface to Manifest. You should prefer ManifestFile over Manifest when the manifest in question is stored on disk.
    """

    def __init__(self, fp):
        """Initializes a new Manifest object.

        Args:
            fp: a readable file-like object storing the JSON file. It should be an array of objects. The Manifest does not preserve a reference to fp.
        """
        self._manifest = json.load(fp)

    def revert(self, fp):
        """Overwrites this Manifest with the state of the given readable file-like object."""
        self._manifest = json.load(fp)

    def commit(self, fp):
        """Writes the Manifest to the given writable file-like object."""
        json.dump(self._manifest, fp)

    def get(self, key):
        """Returns the dict representing the source with a given integer ID."""
        return self._manifest[key]

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return key in self._manifest

    def __len__(self):
        return len(self._manifest)

    def values(self, field):
        """Returns a set of the unique values of the given field among all sources in this manifest."""
        found = set()
        for source in self._manifest:
            if field in source:
                found.add(source[field])
        return found

    def search(self, field, query, is_regex):
        """Returns the IDs of all sources that match the given query in the given field."""
        results = []
        for key, source in enumerate(self._manifest):
            if is_regex:
                if field in source and re.search(query, source[field]):
                    results.append(key)
            else:
                if field in source and source[field] == query:
                    results.append(key)

        return results

    # These methods modify the manifest, and should trigger autocommit for ManifestFile.
    # If you define a new method that should trigger autocommit, mention it in ManifestFile.__getattr__.

    def add(self, source):
        """Adds a new source to the manifest and returns its index."""
        idx = len(self._manifest)
        self._manifest.append(source)
        return idx

    def replace(self, key, source):
        """Replaces the source at the given index with the given source."""
        if key >= len(self._manifest) or key < 0:
            raise IndexError

        self._manifest[key] = source


class ManifestFile(object):
    """Interacts with a manifest stored on disk, adding autocommit and locking features.

    Methods that are not explicitly overriden in this class are delegated to Manifest (except that all functions that modify the manifest will trigger autocommit if it is set). You should use this class in preference to Manifest when the manifest is stored on disk.
    """

    # These methods deal with context: creating and destroying a ManifestFile.

    def __init__(self, fname, autocommit=True, lock=True, encoding="utf_8"):
        """Creates a new ManifestFile. Raises ValueError if the given file does not exist.

        Args:
            fname: The file where this manifest is stored.
            autocommit: If true, all method calls that modify the manifest write the results back to disk immediately. If false, you must call commit.
            lock: If true, also generate a lock file that prevents multiple open ManifestFiles from governing the same file on disk.
            encoding: The character encoding of the file on disk. You are strongly encouraged to use the default of UTF-8 for interoperability purposes.
        """
        if not os.path.isfile(fname):
            raise ValueError
        self._fname = os.path.abspath(fname)
        self._autocommit = autocommit
        self._lock = lock
        self._encoding = encoding
        self._mf = None

        # Locking; create the file; we don't need the fd
        if self._lock:
            try:
                os.close(os.open(fname + ".lock", os.O_CREAT | os.O_EXCL | os.O_RDONLY))
            except OSError:  # file already exists
                raise FileLockError

        with codecs.open(self._fname, "r", encoding) as mf_file:
            self._mf = Manifest(mf_file)

    def __enter__(self):
        # We've already initialized the context in __init__
        return self

    def close(self):
        """Closes this ManifestFile. Attempts to use a closed FileManifest will raise a ValueError. This method is idempotent: attempts to close an already-closed ManifestFile will have no effect."""
        if self._lock:
            os.remove(fname + ".lock")

        # We signal that a ManifestFile has been closed by setting its manifest to None.
        self._mf = None

    def __exit__(self, e_type, unused_e, unused_e_traceback):
        # We can close it without checking if there was an exception, since closure is idempotent, and we shouldn't leave random lock files around.
        self.close()

        if e_type:
            return False  # propagate the exception

    # Reversions and commits shouldn't take a file-like object anymore.

    def revert(self):
        if not self._mf:
            raise ValueError

        with codecs.open(self._fname, "r", self._encoding) as mf_file:
            self._mf.revert(mf_file)

    def commit(self):
        if not self._mf:
            raise ValueError

        with codecs.open(self._fname, "w", self._encoding) as mf_file:
            self._mf.commit(mf_file)

    # Other methods delegate to the Manifest, but we should autocommit and check for closure.
    def __getattr__(self, attr):
        if not self._mf:
            raise ValueError

        # If autocommit is on, add and replace should commit.
        if self._autocommit and (attr == "add" or attr == "replace"):
            return lambda *args, **kwargs: getattr(self._mf, attr)(*args, **kwargs); self.commit()

        return getattr(self._mf, attr)


class FileLockError(Exception):
    """Indicates that a ManifestFile was constructed using lock = True, but another ManifestFile was already using that file."""
    pass
