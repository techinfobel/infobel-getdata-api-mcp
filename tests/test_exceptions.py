"""Tests for custom exception classes."""
import pytest


class TestInfobelAPIError:
    def test_basic_message(self):
        from infobel_api.exceptions import InfobelAPIError
        err = InfobelAPIError("something went wrong")
        assert str(err) == "something went wrong"
        assert err.message == "something went wrong"

    def test_optional_status_code_default_none(self):
        from infobel_api.exceptions import InfobelAPIError
        err = InfobelAPIError("error")
        assert err.status_code is None

    def test_optional_response_data_default_none(self):
        from infobel_api.exceptions import InfobelAPIError
        err = InfobelAPIError("error")
        assert err.response_data is None

    def test_with_all_args(self):
        from infobel_api.exceptions import InfobelAPIError
        data = {"detail": "bad request"}
        err = InfobelAPIError("error msg", status_code=400, response_data=data)
        assert err.message == "error msg"
        assert err.status_code == 400
        assert err.response_data == data

    def test_is_exception(self):
        from infobel_api.exceptions import InfobelAPIError
        with pytest.raises(InfobelAPIError):
            raise InfobelAPIError("test")

    def test_can_be_caught_as_base_exception(self):
        from infobel_api.exceptions import InfobelAPIError
        with pytest.raises(Exception):
            raise InfobelAPIError("test")


class TestAuthenticationError:
    def test_is_infobel_api_error(self):
        from infobel_api.exceptions import AuthenticationError, InfobelAPIError
        err = AuthenticationError("auth failed", status_code=401)
        assert isinstance(err, InfobelAPIError)

    def test_attributes_inherited(self):
        from infobel_api.exceptions import AuthenticationError
        err = AuthenticationError("auth failed", status_code=401, response_data={"x": 1})
        assert err.message == "auth failed"
        assert err.status_code == 401
        assert err.response_data == {"x": 1}

    def test_raised_and_caught(self):
        from infobel_api.exceptions import AuthenticationError, InfobelAPIError
        with pytest.raises(InfobelAPIError):
            raise AuthenticationError("bad creds")


class TestNetworkError:
    def test_is_infobel_api_error(self):
        from infobel_api.exceptions import NetworkError, InfobelAPIError
        assert issubclass(NetworkError, InfobelAPIError)

    def test_message(self):
        from infobel_api.exceptions import NetworkError
        err = NetworkError("timeout")
        assert err.message == "timeout"

    def test_raised_and_caught(self):
        from infobel_api.exceptions import NetworkError, InfobelAPIError
        with pytest.raises(InfobelAPIError):
            raise NetworkError("connection refused")


class TestRateLimitError:
    def test_is_infobel_api_error(self):
        from infobel_api.exceptions import RateLimitError, InfobelAPIError
        assert issubclass(RateLimitError, InfobelAPIError)

    def test_with_status_code(self):
        from infobel_api.exceptions import RateLimitError
        err = RateLimitError("too many requests", status_code=429)
        assert err.status_code == 429

    def test_raised_and_caught(self):
        from infobel_api.exceptions import RateLimitError, InfobelAPIError
        with pytest.raises(InfobelAPIError):
            raise RateLimitError("rate limited")


class TestSearchError:
    def test_is_infobel_api_error(self):
        from infobel_api.exceptions import SearchError, InfobelAPIError
        assert issubclass(SearchError, InfobelAPIError)

    def test_message(self):
        from infobel_api.exceptions import SearchError
        err = SearchError("search failed", status_code=500)
        assert err.message == "search failed"
        assert err.status_code == 500
