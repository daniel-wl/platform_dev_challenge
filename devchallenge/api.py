import json
import logging
import os

from flask import Flask, abort, jsonify, request
from flask_restful import Api, Resource
from pymongo import DESCENDING, MongoClient

from devchallenge import mongo_helpers, prediction_api, schemas

logger = logging.getLogger(__name__)

mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/test_db')


def get_database():
    client = MongoClient(mongo_url)
    return client.get_database()


class Prescription(Resource):
    def __init__(self):
        self.db = get_database()

    def get(self, case_id):
        """
        Get the latest prescription for a given case

        Returns mongo document as json
        ---
        tags:
          - prescription
        parameters:
          - in: path
            name: case_id
            description: Case ID
            required: true
            type: integer
            x-example: 1
        responses:
            200:
                description: OK
            400:
                description: Bad Request - invalid request params
            401:
                description: Unauthorized - user does not have permission to view prescription
            404:
                description: No prescription found
            503:
                description: Service Unavailable - connection to the database failed
        """
        case_id = int(case_id)

        prescription_cursor = mongo_helpers.retreive_doc(
            self.db.prescription,
            {"case_id": case_id},
            find_one=False,
            sort_params=("timestamp", DESCENDING),
        )
        prescriptions = list(prescription_cursor)
        if len(prescriptions) == 0:
            logger.warning("no prescriptions found for case")
            abort(404, "No prescription found")

        most_recent_prescription = prescriptions[0]
        logger.info("prescription found")

        return jsonify(most_recent_prescription)

    def post(self, case_id):
        """
        Submit a prescription for predictions

        Inserts raw JSON object and returns full prescription object
        ---
        tags:
          - prescription
        parameters:
          - in: path
            name: case_id
            description: Case ID
            required: true
            type: integer
            x-example: 1
          - in: body
            name: prescription
            description: new prescription
            required: true
            schema:
                $ref: '#/definitions/Prescription'
        responses:
            200:
                description: OK
                schema:
                    type: object
                    properties:
                        prescription_id:
                            type: string
                        predictions:
                            $ref: '#/definitions/RiskPrediction'
            400:
                description: Bad Request - invalid request params
            401:
                description: Unauthorized - user does not have permission to create plans
            500:
                description: Internal Server Error - analytics service failed
            503:
                description: Service Unavailable - connection to the database failed
        """
        case_id = int(case_id)
        args = request.get_json()

        # client = MongoClient(mongo_url)
        # db = client.get_database()

        logger.info("request received", extra={"request_data": args})

        prescription_doc = args.get(schemas.PRESCRIPTION_FIELD)

        # save prescription doc
        prescription_doc = mongo_helpers.add_user_metadata(
            prescription_doc, request.headers.get("Username")
        )
        prescription_doc["case_id"] = case_id

        # #maybe unnecessary?
        # client = MongoClient(mongo_url)
        # db = client.get_database()

        prescription_docid, success = mongo_helpers.persist_doc(
            self.db.prescription, prescription_doc
        )
        prescription_docid = str(prescription_docid)

        prescription_doc["_id"] = prescription_docid
        logger.info('prescription saved', extra={"doc_id": prescription_docid})

        prescription = args["prescription"]
        predictionsResponse = prediction_api.get_risk_prediction(
            "https://api.mypredictions.com/v1/predictions",
            json.dumps(
                dict(
                    case=case_id,
                    target_objectives=prescription["target_objectives"],
                    model_target=prescription["model_target"],
                    model_outcome=prescription["model_outcome"],
                )
            ),
        )

        predictions = predictionsResponse.json()
        predictions.update(case_id=case_id, prescription_id=prescription_docid)
        prediction_docid, success = mongo_helpers.persist_doc(self.db.predictions, predictions)
        print(f"predictions object is {predictions}")
        predictions.update(prediction_id=str(prediction_docid))
        del predictions["_id"]

        return {"prescription_id": prescription_docid, "predictions": predictions}


app = Flask('platform_dev_challenge')
api = Api(app)

api.add_resource(Prescription, '/prescription/<case_id>')
