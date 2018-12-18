"""
# pytest-camel-collect

This plugin extends the semantics of fnmatch for python_classes, so a dash '-'
in the pattern matches a CamelWords boundary.

 - For* will match "ForbidsAnonymousUsers" as well as "ForCurrentUser"
 - For-* will match "ForCurrentUser", but not "ForbidsAnonymousUsers"

"""
import fnmatch
import re
from copy import copy
from typing import TypeVar, Union, Dict

import inflection
import pytest
from _pytest.compat import safe_isclass
from _pytest.python import PyCollector, Module, Instance, Class, Package
from inflection import camelize


def underscore(word, lowercase=True):
    """
    Make an underscored, optionally lowercase form from the expression in the string.

    Example::

        >>> underscore("DeviceType")
        "device_type"

    As a rule of thumb you can think of :func:`underscore` as the inverse of
    :func:`camelize`, though there are cases where that does not hold::

        >>> camelize(underscore("IOError"))
        "IoError"

    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")
    if lowercase:
        word = word.lower()
    return word


def preprocess_camel_words(s: str) -> str:
    """Adds dashes between camel words, preserving underscores

    >>> preprocess_camel_words('Forbids_AnonymousUsers')
    'Forbids_Anonymous-Users'
    >>> preprocess_camel_words('ForbidsAnonymousUsers')
    'Forbids-Anonymous-Users'
    >>> preprocess_camel_words('For8x5x4')
    'For-8-x-5-x-4'
    """
    # 'For24x7Users' -> 'For24x7Users'
    s = s.replace('_', ' ')

    # 'For24x7Users' -> 'For24x7_Users'
    s = underscore(s, lowercase=False)

    # 'For24x7_Users' -> 'For_24_x_7__Users'
    s = re.sub(r'(\d+)', r'_\1_', s)

    # 'For_24_x_7__Users' -> 'For_24_x_7_Users'
    s = s.replace('__', '_')

    # 'For_24_x_7_Users' -> 'For_24_x_7_Users'
    s = re.sub(' _|_ ', ' ', s)

    # 'For_24_x_7_Users' -> 'For_24_x_7_Users'
    s = s.strip('_')

    # 'For_24_x_7_Users' -> 'For-24-x-7-Users'
    s = inflection.dasherize(s)

    # 'For-24-x-7-Users' -> 'For-24-x-7-Users'
    s = s.replace(' ', '_')

    return s


class CamelWordsSensitiveCollector(PyCollector):
    def classnamefilter(self, name):
        preprocessed_name = preprocess_camel_words(name)
        patterns = self.config.getini('python_classes')

        for pattern in patterns:
            if name.startswith(pattern):
                return True

            # check that name looks like a glob-string before calling fnmatch
            # because this is called for every name in each collected module,
            # and fnmatch is somewhat expensive to call
            elif '*' in pattern or '?' in pattern or '[' in pattern:
                if fnmatch.fnmatch(preprocessed_name, pattern):
                    return True

        return False

    def _getcustomclass(self, name):
        return CAMEL_COLLECTORS_BY_NAME.get(name) or super()._getcustomclass(name)


CamelPackage = type('CamelPackage', (CamelWordsSensitiveCollector, Package), {})
CamelModule = type('CamelModule', (CamelWordsSensitiveCollector, Module), {})
CamelClass = type('CamelClass', (CamelWordsSensitiveCollector, Class), {})
CamelInstance = type('CamelInstance', (CamelWordsSensitiveCollector, Instance), {})


# Map supported PyCollector classes to their wrapped CamelWords subclass
CAMEL_COLLECTORS: Dict[PyCollector, CamelWordsSensitiveCollector] = {
    Package: CamelPackage,
    Module: CamelModule,
    Class: CamelClass,
    Instance: CamelInstance,
}

# Map names of supported PyCollector classes to their wrapped CamelWords subclass
# (Used in _getcustomclass)
CAMEL_COLLECTORS_BY_NAME: Dict[str, CamelWordsSensitiveCollector] = {
    subclass.__name__: cls
    for subclass, cls in CAMEL_COLLECTORS.items()
}


T = TypeVar('T', bound=PyCollector)


def inject_camel_collector(collector: T) -> Union[T, CamelWordsSensitiveCollector]:
    # XXX: is this cls detection too brittle when interacting with other plugins?
    base = collector.__class__
    if base not in CAMEL_COLLECTORS:
        return collector

    camel_cls = CAMEL_COLLECTORS[base]

    # XXX: can we use a copy of collector, to avoid mutating an arg?
    #      if not, remove the return, so it's obvious the func has side effects.
    instance = collector
    instance.__class__ = camel_cls

    return instance


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makemodule(path, parent):
    outcome = yield
    res = outcome.get_result()
    if res is None:
        return

    new_res = inject_camel_collector(res)
    outcome.force_result(new_res)
