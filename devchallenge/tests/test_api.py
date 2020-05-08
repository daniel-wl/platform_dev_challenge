from faker import Faker
from mongomock import MongoClient

from devchallenge.api import Prescription

# def test_get_prescription_doc():
#     resource = Prescription()
#     doc = resource.get(1)

#     assert doc is not None

faker = Faker()

def test_pass_mock_db_to_Prescription():
    dbMock = MongoClient()
    subject = Prescription(dbMock.db)
    assert subject.db == dbMock.db
