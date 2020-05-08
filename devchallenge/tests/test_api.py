from unittest.mock import MagicMock

from devchallenge.api import Prescription

# def test_get_prescription_doc():
#     resource = Prescription()
#     doc = resource.get(1)

#     assert doc is not None


def test_pass_mock_db_to_Prescription():
    dbMock = MagicMock()
    subject = Prescription(dbMock)
    assert subject.db == dbMock
