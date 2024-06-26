
#!/usr/bin/env python3

"""Objects/Drafts_modify
Tests for 'Modification of BCO draft is successful.' (200), 
returns 207, 400, 403 (needs to be reviewed)
"""


import json
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from tests.fixtures.testing_bcos import NOPUB_000001_DRAFT, BCO_000000_DRAFT, BCO_000001_DRAFT

class BcoDraftModifyTestCase(TestCase):
    fixtures = ['tests/fixtures/test_data']
    def setUp(self):
        self.client = APIClient()

        self.token = Token.objects.get(user=User.objects.get(username="tester"))

        self.legacy_data = {
            "POST_api_objects_drafts_modify": [
                {
                    # "prefix": "NOPUB",
                    # "owner_group": "tester",
                    "object_id": "http://127.0.0.1:8000/NOPUB_000001/DRAFT",
                    # "schema": "IEEE",
                    "contents": NOPUB_000001_DRAFT
                }
            ]
        }

        self.data = [
            {
                "object_id": "http://127.0.0.1:8000/NOPUB_000001/DRAFT",
                "prefix": "BCO",
                "authorized_users": ["hivelab"],
                "contents": NOPUB_000001_DRAFT
            },
            {
                "object_id": "http://127.0.0.1:8000/BCO_000000/DRAFT",
                "prefix": "TEST",
                "authorized_users": ["tester"],
                "contents": BCO_000000_DRAFT
            }
        ]

    # def test_legacy_successful_modification(self):
    #     """200: Modification of BCO drafts is successful.
    #     """

    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    #     response = self.client.post('/api/objects/drafts/modify/', self.legacy_data, format='json')
    #     self.assertEqual(response.status_code, 200)

    def test_successful_modification(self):
        """200: Modification of BCO drafts is successful.
        """

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post('/api/objects/drafts/modify/', self.data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_partial_failure(self):
        '''Test case for partial failure (response code 300)
        Returns 207(Multi status) instead of 300(Partial faliure)'''
        data = {
            'POST_api_objects_drafts_modify': [
                {
                    "object_id": "http://127.0.0.1:8000/BCO_000000/DRAFT",
                    "prefix": "TEST",
                    "authorized_users": ["tester"],
                    "contents": BCO_000000_DRAFT
                },
                {
                    'prefix': 'Tianyi',
                    'owner_group': 'bco_drafter',
                    'schema': 'IEEE',
                    'contents': BCO_000001_DRAFT
                }
            ]
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post('/api/objects/drafts/modify/', data=data, format='json')
        self.assertEqual(response.status_code, 207)

    def test_bad_request(self):
        '''Test case for bad request (response code 400)
        Gives 403 forbidden request instead of 400'''
        data =  [
            {
                "object_id": "http://127.0.0.1:8000/TEST_000001",
                "contents": {
                    "object_id": "https://biocomputeobject.org/TEST_000001",
                    "spec_version": "https://w3id.org/ieee/ieee-2791-schema/2791object.json",
                    "etag": "11ee4c3b8a04ad16dcca19a6f478c0870d3fe668ed6454096ab7165deb1ab8ea",
                }
            }
        ]
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post('/api/objects/drafts/modify/', data=data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_token(self):
        '''Test case for invalid token (response code 403)
        Setting authentication token to an invalid value'''
        
        data = {
            'POST_api_objects_drafts_modify': [
                {
                    'prefix': 'BCO',
                    'owner_group': 'bco_drafter',
                    'schema': 'IEEE',
                    'contents': BCO_000000_DRAFT
                },
                
            ]
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token InvalidToken')
        response = self.client.post('/api/objects/drafts/modify/', data=data, format='json')
        self.assertEqual(response.status_code, 403)