"""Specifies mechanisms to retrieve sources from the Internet.

SourceWrangler supports a variety of ways to download sources. Each way of retrieving sources is known as a protocol, which has a string name. Each protocol is associated with a retriever, which takes certain retrieval options (in the retrieval field of a download object) and downloads the source into a temp folder.

All retrievers are classes decorated with @register_retriever('protocol'). Fields are expressed as methods, decorated with @required_field('field') or @optional_field('field'), which validate possible values for the field.

Retrievers are bestowed with certain public fields; see the documentation for register_retriever.

    http_retriever = get_retriever('http')
    if http_retriever.validate(options):
        output = http_retriever.run(options, tmp_folder)
"""


_registry = {}


class DuplicateFieldError(Exception):
    """Indicates that multiple fields of a retriever were defined with the same name."""
    pass


class InvalidRetrievalOptionsError(Exception):
    """Indicates that the retrieval object passed to the run method of a retriever failed validation."""
    pass


class UnrunnableRetrieverError(Exception):
    """Indicates that a class decorated with @register_retriever lacks a _run method."""
    pass


def register_retriever(protocol):
    """Class decorator: marks a class as the retriever for a given protocol.
    
    Classes decorated with this get the following attributes, which shouldn't be modified except through the mechanisms in this module:
        protocol: The name of the protocol passed into this decorator.
        required: A map from required field names to their validators.
        optional: A map from optional field names to their validators.
        validate: Class method: takes a complete retrieval object and checks that all required fields are present and that all field values are valid.
        run: Takes a retrieval object and a temp folder object, validates the retrieval, then calls _run with the same parameters.
    """
    def decorator(cls):
        # Fail fast if no _run method (needed for the run method below).
        if not hasattr(cls, "_run"):
            raise UnrunnableRetrieverError

        # Create registries for required and optional fields.
        cls.required = {}
        cls.optional = {}

        for method_name, method in cls.__dict__.iteritems():
            if hasattr(method, "_required_field"):
                # Check for duplicates.
                if method._required_field in cls.required or method._required_field in cls.optional:
                    raise DuplicateFieldError

                cls.required[method._required_field] = method

            elif hasattr(method, "_optional_field"):
                # Check for duplicates.
                if method._optional_field in cls.required or method._optional_field in cls.optional:
                    raise DuplicateFieldError

                cls.optional[method._optional_field] = method

        # Make a method to validate a retrieval object.
        @classmethod
        def validate(cls, retrieval):
            # Track if we've seen every required field.
            num_required_fields = 0

            for field, value in retrieval.iteritems():
                if field in cls.required:
                    if not cls.required[field](value):
                        return False
                    num_required_fields += 1
                elif field in cls.optional:
                    if not cls.optional[field](value):
                        return False
                else:
                    # Spurious field!
                    return False
            
            # All done, did we catch 'em all?
            return num_required_fields == len(cls.required)
        cls.validate = validate

        # Make a thin wrapper for run.
        def run(self, retrieval, tmp_folder):
            if not self.validate(retrieval):
                raise InvalidRetrievalOptionsError
            return self._run(retrieval, tmp_folder)
        cls.run = run

        # Register the class at the end, so we don't register broken stuff.
        _registry[protocol] = cls
        cls.protocol = protocol

        return cls
    return decorator


def required_field(name):
    """Method decorator: marks a method as the validator for a required field. The class should be decorated with register_retriever, and this decorator adds the method to required.

    The validator should take one parameter, the proposed value for the field, and return True iff the value is valid.
    """
    def decorator(func):
        func._required_field = name
        return func
    return decorator


def optional_field(name):
    """Method decorator: marks a method as the validator for an optional field. The class should be decorated with register_retriever, and this decorator adds the method to optional.

    The validator should take one parameter, the proposed value for the field, and return True iff the value is valid.
    """
    def decorator(func):
        func._optional_field = name
        return func
    return decorator


class InvalidProtocolError(Exception):
    """Indicates that the given protocol does not have a registered retriever."""
    pass


def has_retriever(protocol):
    """Returns True iff a retriever is defined for a given protocol."""
    return protocol in _registry


def get_retriever(protocol):
    """Gets the retriever for a given protocol, or raises InvalidProtocolError if one has not been defined."""
    try:
        return _registry[protocol]
    except:
        raise InvalidProtocolError
