# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Fixed
 - Resolve broken collection of nested classes

### Changed
 - Support pytest versions 2.9, 3.6, 3.9, 4.0, 4.4, 4.5, 4.6, 5.0, 5.1, 5.2, 5.3, 5.4, and 6.0
 - Minor README updates


## [1.0.1] - 2018-12-17
### Changed
 - Added PyPI version badge to README
 - Improved tests using [pytest-lambda](https://github.com/theY4Kman/pytest-lambda)


## [1.0.0] - 2018-12-17
### Added
 - Initial release: CamelCase-aware pytest class name filter (dashes in pytest.ini's python_classes represent CamelWord boundaries)
