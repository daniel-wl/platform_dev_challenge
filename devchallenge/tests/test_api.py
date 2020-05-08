from unittest import mock

from faker import Faker
from mongomock import MongoClient

from devchallenge.api import Prescription, app

# def test_get_prescription_doc():
#     resource = Prescription()
#     doc = resource.get(1)

#     assert doc is not None

faker = Faker()


def get_mockDatabase():
    return MongoClient().db


@mock.patch("devchallenge.api.get_database")
def test_POST(mock_getDatabase):
    mockDb = get_mockDatabase()
    mock_getDatabase.return_value = mockDb

    prescription = {
        "prescription": {
            "target_objectives": [],
            "model_target": faker.name(),
            "model_outcome": faker.name(),
        }
    }

    app.testing = True
    client = app.test_client()
    response = client.post("/prescription/1234", json=prescription)
    assert "predictions" in response.json
