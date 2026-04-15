import pytest
import inspect
import app.invite as invite_mod


def test_invite_existing_user_no_unbound_local():
    source = inspect.getsource(invite_mod)
    assert "temp_password = None" in source
