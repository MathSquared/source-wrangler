"""Specifies one operation that SourceWrangler can perform.

SourceWrangler can perform various operations. Each one is encapsulated as a command. For instance, the add command interactively adds a source to the repository.

All commands are classes decorated with @register_command('name'), which will make the command run with `sw name`. They must define the static specify_args method, which takes an argparse that the command should fill with arguments. They must also define an instance method named run, which will receive a SourceFolder along with a Namespace generated by parsing the arguments using the generated argparse. Finally, they may define strings _description and _help, which provide a long-form description and terse help string for the command, respectively.
"""


_registry = {}


class ImproperlyDefinedCommandError(Exception):
    """Indicates that a class decorated with @register_command lacks a specify_args or run method. This does not check that the attributes are methods, and the other stipulations in the module documentation."""
    pass


def register_command(name):
    """Class decorator: marks a class as the command for a particular name.

    Classes decorated with this are bestowed with the name attribute, which contains the name of the command. They should contain specify_args and run methods as specified in the module documentation.
    """
    def decorator(cls):
        if not hasattr(cls, "specify_args") or not hasattr(cls, "run"):
            raise ImproperlyDefinedCommandError

        _registry[name] = cls
        cls.name = name

        return cls
    return decorator


class InvalidCommandError(Exception):
    """Indicates that the given command name does not exist."""
    pass


def all_commands():
    """Returns a generator yielding all registered commands, in arbitrary order."""
    return (value for _, value in _registry.iteritems())


def has_command(name):
    return name in _registry


def get_command(name):
    """Gets the command with a given name, or raises InvalidCommandError if the command does not exist."""
    if has_command(name):
        return _registry[name]
    else:
        raise InvalidCommndError