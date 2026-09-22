import io
import json
import os
import unittest
from unittest import mock

import railway_control


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class RailwayControlTests(unittest.TestCase):
    def test_project_token_header_is_scoped_header(self):
        auth = railway_control.RailwayAuth("secret", "project")
        headers = auth.headers()
        self.assertEqual(headers["Project-Access-Token"], "secret")
        self.assertNotIn("Authorization", headers)

    def test_bearer_header(self):
        auth = railway_control.RailwayAuth("secret", "bearer")
        self.assertEqual(auth.headers()["Authorization"], "Bearer secret")

    def test_environment_fails_closed_when_both_tokens_exist(self):
        with mock.patch.dict(
            os.environ,
            {"RAILWAY_PROJECT_TOKEN": "a", "RAILWAY_TOKEN": "b"},
            clear=True,
        ):
            with self.assertRaises(railway_control.RailwayControlError):
                railway_control.RailwayAuth.from_environment()

    def test_environment_fails_closed_when_no_token_exists(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(railway_control.RailwayControlError):
                railway_control.RailwayAuth.from_environment()

    def test_graphql_200_errors_are_not_treated_as_success(self):
        client = railway_control.RailwayClient(railway_control.RailwayAuth("x"))
        payload = {
            "errors": [
                {
                    "message": "Not Authorized",
                    "extensions": {"code": "INTERNAL_SERVER_ERROR", "traceId": "abc"},
                }
            ],
            "data": None,
        }
        with mock.patch("urllib.request.urlopen", return_value=_Response(payload)):
            with self.assertRaises(railway_control.RailwayControlError) as ctx:
                client.execute("query { projectToken { projectId } }")
        self.assertIn("traceId", str(ctx.exception))

    def test_scope_query_returns_data(self):
        client = railway_control.RailwayClient(railway_control.RailwayAuth("x"))
        payload = {
            "data": {
                "projectToken": {
                    "projectId": "project-1",
                    "environmentId": "env-1",
                }
            }
        }
        with mock.patch("urllib.request.urlopen", return_value=_Response(payload)) as call:
            result = client.project_token_scope()
        self.assertEqual(result["projectToken"]["projectId"], "project-1")
        request = call.call_args.args[0]
        self.assertEqual(request.get_header("Project-access-token"), "x")

    def test_scope_rejects_bearer_token(self):
        client = railway_control.RailwayClient(
            railway_control.RailwayAuth("x", "bearer")
        )
        with self.assertRaises(railway_control.RailwayControlError):
            client.project_token_scope()


if __name__ == "__main__":
    unittest.main()
