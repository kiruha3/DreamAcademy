import pytest
from app import moodle_db


def test_validate_modname_allowed():
    # Should not raise
    moodle_db._validate_modname("quiz")
    moodle_db._validate_modname("forum")
    moodle_db._validate_modname("assign")


def test_validate_modname_disallowed():
    with pytest.raises(ValueError, match="Invalid module name"):
        moodle_db._validate_modname("; DROP TABLE users;")

    with pytest.raises(ValueError, match="Invalid module name"):
        moodle_db._validate_modname("unknown_module")
