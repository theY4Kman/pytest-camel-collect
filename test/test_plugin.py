from pathlib import Path

import pytest

TEST_DIR: Path = Path(__file__).parent
REPO_DIR: Path = TEST_DIR.parent

pytest_plugins = 'pytester'


@pytest.fixture
def python_classes() -> str:
    """The value of python_classes in pytest.ini"""
    return ''


@pytest.fixture(autouse=True)
def setup_syspath(testdir, python_classes):
    testdir.syspathinsert(REPO_DIR)
    testdir.makeconftest('pytest_plugins = "pytest_camel_collect.plugin"')
    testdir.makeini(f'''
        [pytest]
        python_files = *.py
        python_classes = {python_classes}
    ''')


def assert_test_did_run(res, name):
    res.stdout.fnmatch_lines('*' + name + '*')


def assert_test_did_not_run(res, name):
    with pytest.raises(pytest.fail.Exception):
        res.stdout.fnmatch_lines('*' + name + '*')


class TestCamelCollector:
    @pytest.fixture
    def pyfile(self) -> str:
        """The python test file source to execute"""
        return '''
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
        '''

    @pytest.fixture(autouse=True)
    def test_result(self, testdir, pyfile, setup_syspath):
        file = testdir.makepyfile(pyfile)

        res = testdir.runpytest_inprocess(file, '--verbose')
        outcomes = res.parseoutcomes()
        assert 'passed' in outcomes, 'Tests did not run successfully'

        return res


    class WithCamelWordBoundaries:
        @pytest.fixture
        def python_classes(self) -> str:
            # With a dash to only match word boundaries
            return 'For-*'

        def test(self, test_result):
            assert_test_did_run(test_result, 'test_sanity_check')

            assert_test_did_run(test_result, 'test_on_camel_boundary')
            assert_test_did_run(test_result, 'test_child_on_camel_boundary')
            assert_test_did_not_run(test_result, 'test_not_on_camel_boundary')
            assert_test_did_not_run(test_result, 'test_child_not_on_camel_boundary')


    class WithoutCamelWordBoundaries:
        @pytest.fixture
        def python_classes(self) -> str:
            # Without a dash to match substring anywhere, even outside word boundaries
            return 'For*'

        def test(self, test_result):
            assert_test_did_run(test_result, 'test_sanity_check')

            assert_test_did_run(test_result, 'test_on_camel_boundary')
            assert_test_did_run(test_result, 'test_child_on_camel_boundary')
            assert_test_did_run(test_result, 'test_not_on_camel_boundary')
            assert_test_did_run(test_result, 'test_child_not_on_camel_boundary')
