from collections.abc import Iterable
from pathlib import Path
from typing import Type

import pytest
from _pytest._code import Source
from _pytest.pytester import RunResult
from pytest_lambda import not_implemented_fixture, lambda_fixture, static_fixture

TEST_DIR: Path = Path(__file__).parent
REPO_DIR: Path = TEST_DIR.parent


class AppendableSource(Source):
    def __add__(self, other: Source):
        if isinstance(other, str):
            other = self.__class__(other)

        if isinstance(other, Source):
            other_lines = other.lines
        elif isinstance(other, Iterable):
            other_lines = [str(line) for line in other]
        else:
            raise TypeError(f'Expected an iterable or Source instance, got {type(other)}')

        return self.__class__(self.lines + other_lines)


# Whether pytest-camel-collect is already loaded.
# Used to prevent double-loading the plugin, if it's already been pip-installed.
#
# Because we don't specifically ask pytest to load camel-collect,
# the only reason it ought to be loaded is because `setup.py install` has been run.
# In that case, we don't want to request the plugin to be loaded, or pytest will error.
#
is_camel_collect_plugin_loaded = lambda_fixture(
    lambda request:
        request.config.pluginmanager.has_plugin('camel_collect'))


# Contents of conftest.py in temporary test folder
conftest_contents = lambda_fixture(
    lambda is_camel_collect_plugin_loaded:
        AppendableSource(
            'pytest_plugins = "pytest_camel_collect.plugin"' if not is_camel_collect_plugin_loaded else ''
        ))

# Contents of pytest.ini in temporary test folder
pytest_ini_contents = static_fixture(AppendableSource('''
    [pytest]
    python_files = *.py
'''))


def find_in_test_output(pattern: str, test_result: RunResult) -> bool:
    """Return whether the pattern was fnmatched in test_result's stdout
    """
    try:
        test_result.stdout.fnmatch_lines(pattern)
    except pytest.fail.Exception:
        return False
    else:
        return True


@pytest.fixture(autouse=True)
def setup_syspath(testdir):
    testdir.syspathinsert(REPO_DIR)


@pytest.fixture(autouse=True)
def setup_conftest(testdir, conftest_contents):
    testdir.makeconftest(conftest_contents)


@pytest.fixture(autouse=True)
def setup_pytest_ini(testdir, pytest_ini_contents):
    testdir.makeini(pytest_ini_contents)


class UsingPyTestIniPythonClasses:
    """Mixin to set the value of python_classes in pytest.ini"""

    # Value of `python_classes` to place in pytest.ini
    pytest_python_classes = lambda_fixture('default_pytest_python_classes')

    # The default python_classes setting (simply "Test", at time of writing)
    default_pytest_python_classes = lambda_fixture(
        lambda request:
            request.config._parser._inidict['python_classes'][2])  # description, type, *default*

    # Adds `python_classes` to pytest.ini
    pytest_ini_contents = lambda_fixture(
        lambda pytest_ini_contents, pytest_python_classes:
            pytest_ini_contents + f'python_classes = {pytest_python_classes}')


def WithPyTestIniPythonClasses(python_classes: str) -> Type[UsingPyTestIniPythonClasses]:
    """Returns mixin class adding the specified python_classes setting to pytest.ini

    Usage:

        class TestMyClass(
            WithPyTestIniPythonClasses('Pattern-*'),
        ):
            # ...

    """
    class CustomPytestIniPythonClasses(UsingPyTestIniPythonClasses):
        pytest_python_classes = static_fixture(python_classes)

    return CustomPytestIniPythonClasses


class RunPyTest:
    """Mixin to run a pytest session at each test and store result in test_result fixture"""

    # Source of test file to be tested
    test_source = not_implemented_fixture()

    # Physical test file to be tested
    test_file = lambda_fixture(lambda testdir, test_source: testdir.makepyfile(test_source))

    # Result of running the py.test session
    test_result = lambda_fixture(lambda testdir, test_file: testdir.runpytest_inprocess(test_file, '--verbose'),
                                 autouse=True)


class VerifyPyTestCollection:
    """Mixin to verify the collection/non-collection of tests during a pytest session"""

    # Names of tests which ought to be collected
    expected_collected_tests = not_implemented_fixture()

    # Names of tests which ought not to be collected
    unexpected_collected_tests = not_implemented_fixture()

    def it_collects_expected_tests(self, expected_collected_tests, test_result):
        # XXX: this check can give false positives if test names are not specific enough
        expected = set(expected_collected_tests)
        actual = {name
                  for name in expected_collected_tests
                  if find_in_test_output(f'*{name}*', test_result)}
        assert expected == actual, 'py.test did not collect expected test(s)'

    def it_doesnt_collect_unexpected_tests(self, unexpected_collected_tests, test_result):
        # XXX: this check can give false negatives if test names are not specific enough
        expected = set(unexpected_collected_tests)
        actual = {name
                  for name in unexpected_collected_tests
                  if not find_in_test_output(f'*{name}*', test_result)}
        assert expected == actual, 'py.test collected unexpected test(s)'


class StrictVerifyPyTestCollection(VerifyPyTestCollection):
    """Mixin to verify only the specified tests were collected"""

    # TODO


class TestCamelCollector(
    RunPyTest,
):
    test_source = static_fixture('''
        def test_sanity_check():
            # I should always be collected
            pass

        class ForTheLoveOfCollection:
            def test_on_camel_boundary(self):
                pass

            class ForTheChildren:
                def test_child_on_camel_boundary(self):
                    pass

        class ForgiveMeFatherForIHaveNotCollected:
            def test_not_on_camel_boundary(self):
                pass

            class ForgiveTheChildren:
                def test_child_not_on_camel_boundary(self):
                    pass
    ''')

    class WithCamelWordBoundaries(
        VerifyPyTestCollection,
        WithPyTestIniPythonClasses('For-*'),  # with a dash to only match word boundaries
    ):
        expected_collected_tests = static_fixture([
            'test_sanity_check',
            'test_on_camel_boundary',
            'test_child_on_camel_boundary',
        ])
        unexpected_collected_tests = static_fixture([
            'test_not_on_camel_boundary',
            'test_child_not_on_camel_boundary',
        ])

    class WithoutCamelWordBoundaries(
        VerifyPyTestCollection,
        WithPyTestIniPythonClasses('For*'),  # without a dash to match substring anywhere, even across word boundaries
    ):
        expected_collected_tests = static_fixture([
            'test_sanity_check',
            'test_on_camel_boundary',
            'test_child_on_camel_boundary',
            'test_not_on_camel_boundary',
            'test_child_not_on_camel_boundary',
        ])
        unexpected_collected_tests = static_fixture([])
