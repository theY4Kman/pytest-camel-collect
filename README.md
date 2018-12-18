# pytest-camel-collect
[![PyPI version](https://badge.fury.io/py/pytest-camel-collect.svg)](https://badge.fury.io/py/pytest-camel-collect)

Allow pytest to respect word boundaries of CamelCaseWords in class name patterns.


# Installation

```bash
pip install pytest-camel-collect
```


# Usage

This plug-in augments the pattern matching of [`python_classes`](https://docs.pytest.org/en/4.0.2/reference.html#confval-python_classes)
in your _pytest.ini_, tox.ini, or setup.cfg file.

A `-` (dash) now represents a CamelCase word boundary.

```ini
[pytest]
python_classes = Camel-*
```

`Camel-*` will match class names like `CamelClub` and `CamelCamelCamel`, but not `Camelizer`.


# Why?

Mixin classes can be helpful to reduce boilerplate. One might use these mixin classes
to add tests verifying API response status codes when authenticated as different users:

```python
class ForbidsAnonymousUsers:
    class TestAnonymousUsersAreForbidden:
        @pytest.fixture
        def user(self):
            return AnonymousUser()
        
        def test_anonymous_user_is_forbidden(self, response):
            assert response.status_code == 401

class ForbidsNonAdmins:
    class TestNonAdminsAreForbidden:
        @pytest.fixture
        def user(self):
            return User(is_admin=False)
        
        def test_non_admin_is_forbidden(self, response):
            assert response.status_code == 401
```

Now, these mixins can be used to declare "traits" of certain test environments:

```python
class DescribeMyAPIEndpoint(BaseAPITest):
    @pytest.fixture
    def url(self):
        return '/my-endpoint'

    class DescribeList(
        ForbidsAnonymousUsers,
    ):
        @pytest.fixture
        def method(self):
            return 'GET'

    class DescribeCreate(
        ForbidsAnonymousUsers,
        ForbidsNonAdmins,
    ):
        @pytest.fixture
        def method(self):
            return 'POST'
```

As it goes, business requirements change, and the API endpoint must now respond differently
depending on the user's language.

No sweat! As experts in nameology, we add well-named context classes to test other languages:

```python

class DescribeMyAPIEndpoint(BaseAPITest):
    # ...

    class DescribeCreate(
        ForbidsAnonymousUsers,
        ForbidsNonAdmins,
    ):
        # ...

        class ForEnglishSpeakers:
            @pytest.fixture
            def user(self, user):
                user.language = 'english'
                return user

            def it_returns_english(self, response):
                assert response['message'] == 'Created new thing'

        class ForSpanishSpeakers:
            @pytest.fixture
            def user(self, user):
                user.language = 'spanish'
                return user

            def it_returns_spanish(self, response):
                assert response['message'] == 'Creado cosa nueva'
```

Hmmm, but when pytest is executed, it doesn't collect our two new tests...

Ah, right! `python_classes` in _pytest.ini_!

```ini
[pytest]
python_classes = Test* Describe* For*
```

Run pytest again and it picks up our tests! Oh, and also picks up 
our `ForbidsAnonymousUsers` and `ForbidsNonAdmins` mixins... but because
they don't inherit `BaseAPITest`, the `response` fixture doesn't exist,
and they fail.

_What ever will we do?_

**Introducing: pytest-camel-collect**, the pytest plugin enabling _you_,
the hard-working, dependable, definitely-not-sleep-deprived developer
to explicitly match CamelCase words during pytest collection.

No longer must you run tests from your `ForbidsAnonymousUsers` mixin,
just because you also want to run tests in your `ForSpanishSpeakers` context!
_Hell no!_

```ini
[pytest]
python_classes = Test-* Describe-* For-*
```

That's the spirit! Now, `TestStuff` will be collected, but not `Testimony`;
`DescribeStuff` will be collected, but not `DescribesCosas`; and most importantly,
`ForSpanishSpeakers` will be collected, but not `ForbidsAnonymousUsers`.


# Development

To play around with the project and run its tests:

 1. Clone the repo
 2. In a virtualenv (or whatever you wanna do, I don't control you), run `pip install -e .[dev,test]`
 3. Run `py.test` to run the tests
