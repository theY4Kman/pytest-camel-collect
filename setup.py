from pathlib import Path

from setuptools import setup


ROOT_DIR: Path = Path(__file__).parent
PKG_DIR = ROOT_DIR / 'pytest_camel_collect'
VERSION_PATH = PKG_DIR / 'version.py'
README_PATH = ROOT_DIR / 'README.md'


def get_version() -> str:
    with VERSION_PATH.open() as fp:
        source = fp.read()

    ctx = {}
    exec(source, ctx)
    return ctx['__version__']


def get_readme() -> str:
    with README_PATH.open() as fp:
        return fp.read()


setup(
    name='pytest-camel-collect',
    version=get_version(),
    description='Enable CamelCase-aware pytest class collection',
    long_description=get_readme(),
    long_description_content_type='text/markdown',

    author='Zach "theY4Kman" Kanzler',
    author_email='they4kman@gmail.com',
    url='https://github.com/theY4Kman/pytest-camel-collect',

    classifiers=[
        'Framework :: Pytest',
    ],

    packages=['pytest_camel_collect'],
    include_package_data=True,

    entry_points={
        'pytest11': [
            'camel_collect = pytest_camel_collect.plugin',
        ]
    },

    python_requires='>=3.6',  # 3.6+ required due to type annotations
    install_requires=[
        'pytest>=2.9',
        'inflection>=0.3.1,<0.4',
    ],
    extras_require={
        'test': [
            'pytest-lambda==0.0.2',
        ],
        'dev': [
            'pytest-camel-collect[test]',
            'twine~=1.12.1',
        ]
    },
)
