import datetime
import os


class IncompleteSourceFolderError(Exception):
    """Indicates that a SourceFolder was constructed for a folder that is an invalid source folder, or that a ReceivingBay or TemporaryFolder was created for a folder that does not exist. If you wish to create a SourceFolder, call its spawn method."""
    pass


class SourceFolder(object):
    """Represents a folder that contains sources, a manifest, and other auxiliary items used by SourceWrangler."""
    @staticmethod
    def check(fname):
        """Checks that a given relative or absolute path would yield a valid SourceFolder."""
        absfname = os.path.abspath(fname)

        # Is it a directory?
        if not os.path.isdir(absfname):
            return False

        # Check for an rbay, a .tmp, and a manifest.json.
        if not os.path.isdir(os.path.join(absfname, "rbay")):
            return False
        if not os.path.isdir(os.path.join(absfname, ".tmp")):
            return False
        if not os.path.isfile(os.path.join(absfname, "manifest.json")):
            return False

        # LGTM
        return True

    @staticmethod
    def _ensure_directory_exists(absfname):
        if os.path.lexists(absfname):
            if not os.path.isdir(absfname):
                raise os.error
            # already exists, we're done
        else:
            os.makedirs(absfname)

    @classmethod
    def _ensure_file_exists(cls, absfname):
        if os.path.lexists(absfname):
            if not os.path.isfile(absfname):
                raise os.error
            # already exists, we're done
        else:
            cls._ensure_directory_exists(os.path.join(absfname, ".."))
            with open(absfname):
                pass

    @classmethod
    def spawn(cls, fname):
        """Turns an existing folder into a valid SourceFolder. Raises os.error if this is impossible."""
        absfname = os.path.abspath(fname)

        cls._ensure_directory_exists(absfname)
        cls._ensure_directory_exists(os.path.join(absfname, "rbay"))
        cls._ensure_directory_exists(os.path.join(absfname, ".tmp"))
        cls._ensure_file_exists(os.path.join(absfname, "manifest.json"))

        # Write an initial empty list to the manifest.
        with open(os.path.join(absfname, "manifest.json")) as mf_json:
            mf_json.write("[]")

        return cls(fname)

    def __init__(self, fname):
        if not self.check(fname):
            raise IncompleteSourceFolderError

        self._fname = os.path.abspath(fname)
        self._rbay = ReceivingBay(os.path.join(self._fname, "rbay"))
        self._tmp = TemporaryFolder(os.path.join(self._fname, ".tmp"))

    @property
    def fname(self):
        """Returns the absolute path to the folder on disk that this SourceFolder represents."""
        return self._fname

    def open(self, name, mode="r", buffering=-1):
        """Opens the file of the given name in the source folder. This does not check against e.g. someone passing in .., so it shouldn't be fed input that isn't trusted by the owner of the running user account."""
        return open(os.path.join(_fname, name), mode, buffering)

    def available(self):
        """Returns a list of the files in the receiving bay, in arbitrary order."""
        return os.listdir(_fname)

    def get(self, key):
        """Returns the filename of the file corresponding to the given source name. The filename is relative to the location of the source folder on disk. Raises KeyError if such a file does not exist, or if str(key) is the empty string."""
        cached_string_key = str(key)
        if cached_string_key == "":
            raise KeyError
        for candidate in self.available():
            if candidate.startswith(cached_string_key):
                return candidate
        raise KeyError

    def __getitem__(self, key):
        return self.get(key)

    def open_source(self, key, mode="r", buffering=-1):
        """Opens the file corresponding to the source with the given key (which should be an integer). Raises KeyError if such a file does not exist, or os.error if it cannot be opened. This does not check against e.g. someone passing in .., so it shouldn't be fed input that isn't trusted by the owner of the running user account."""
        return self.open(self.get(key), mode, buffering)

    def open_manifest(self):
        """Returns a new ManifestFile for the manifest of this SourceFolder.

        Despite its name, this method does not return a file object or file-like object. See the ManifestFile documentation for details on its interface.
        """
        return manifest.ManifestFile(os.path.join(_fname, "manifest.json"))

    @property
    def rbay(self):
        """Returns the ReceivingBay for this SourceFolder."""
        return self._rbay

    @property
    def tmp(self):
        """Returns the TemporaryFolder for this SourceFolder."""
        return self._tmp


class ReceivingBay(object):
    """Represents a receiving bay (rbay in a source folder).

    A ReceivingBay is iterable, and iterates over the files it contains."""
    def __init__(self, fname):
        if not os.path.isdir(fname):
            raise IncompleteSourceFolderError
        self._fname = os.path.abspath(fname)

    @property
    def fname(self):
        """Returns the absolute path to the folder on disk that this ReceivingBay represents."""
        return self._fname

    def open(self, name, mode="r", buffering=-1):
        """Opens the file of the given name in the receiving bay. This does not check against e.g. someone passing in .., so it shouldn't be fed input that isn't trusted by the owner of the running user account."""
        return open(os.path.join(_fname, name), mode, buffering)

    def available(self):
        """Returns a list of the files in the receiving bay, in arbitrary order."""
        return os.listdir(_fname)

    def __iter__(self):
        """Iterates over the files in the receiving bay, in arbitrary order."""
        return iter(self.available())


class TemporaryFolder(object):
    def __init__(self, fname):
        if not os.path.isdir(fname):
            raise IncompleteSourceFolderError
        self._fname = os.path.abspath(fname)

    @property
    def fname(self):
        """Returns the absolute path to the folder on disk that this TemporaryFolder represents."""
        return self._fname

    def open(self, name, mode="r", buffering=-1):
        """Opens the file of the given name in the temporary folder. This does not check against e.g. someone passing in .., so it shouldn't be fed input that isn't trusted by the owner of the running user account."""
        return open(os.path.join(_fname, name), mode, buffering)

    def allocate(self, suffix):
        """Creates a new file with the given suffix in the TemporaryFolder and returns it as a TemporaryFile, or raises OSError if it can't."""
        datecode = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")

        opened = None
        for attempt in xrange(1000):
            try:
                os.close(os.open(os.path.join(_fname, "%s-%03d%s" % (datecode, attempt, suffix)), os.O_CREAT | os.O_EXCL | os.O_RDONLY))
                opened = attempt
            except OSError:
                # continue
                pass

            if opened is not None:
                break

        if opened is None:
            raise OSError

        return new TemporaryFile(os.path.join(_fname, "%s-%03d%s" % (datecode, opened, suffix)))


class TemporaryFile(object):
    def __init__(self, fname):
        self._fname = os.path.abspath(fname)

    @property
    def fname(self):
        return self._fname

    def open(self, mode="r", buffering=-1):
        return open(self._fname, mode, buffering)

    def cleanup(self):
        os.remove(self._fname)
