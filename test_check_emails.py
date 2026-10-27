
import unittest
from unittest.mock import patch

from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from httplib2 import Response

import download_attachments as app


class FakeRequest:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.result


class FakeMessagesList:
    def __init__(self, responses=None, errors=None):
        self.responses = responses or []
        self.errors = errors or []
        self.calls = 0

    def list(self, **kwargs):
        index = self.calls
        self.calls += 1

        if index < len(self.errors) and self.errors[index]:
            return FakeRequest(error=self.errors[index])

        if index < len(self.responses):
            return FakeRequest(result=self.responses[index])

        return FakeRequest(result={"messages": []})


class FakeMessages:
    def __init__(self, responses=None, errors=None):
        self.list_api = FakeMessagesList(responses, errors)

    def list(self, **kwargs):
        return self.list_api.list(**kwargs)


class FakeUsers:
    def __init__(self, messages):
        self.messages_api = messages

    def messages(self):
        return self.messages_api


class FakeService:
    def __init__(self, responses=None, errors=None):
        self.messages_api = FakeMessages(responses, errors)

    def users(self):
        return FakeUsers(self.messages_api)


def make_http_error(status):
    response = Response({"status": str(status)})
    return HttpError(response, b"Simulated Gmail API error")


class TestCheckEmails(unittest.TestCase):

    def test_403_during_listing_is_propagated(self):
        service = FakeService(errors=[make_http_error(403)])

        with self.assertRaises(HttpError) as context:
            app.check_emails(service)

        self.assertEqual(context.exception.resp.status, 403)

    def test_continues_after_one_message_fails(self):
        service = FakeService(
            responses=[{"messages": [{"id": "message-1"},
                                     {"id": "message-2"}]}]
        )

        with patch.object(
            app, "process_message",
            side_effect=[HttpError(
                Response({"status": "403"}),
                b"Simulated error"
            ), None],
        ) as process_mock:
            app.check_emails(service)

        self.assertEqual(process_mock.call_count, 2)
        self.assertEqual(
            [call.args[1] for call in process_mock.call_args_list],
            ["message-1", "message-2"],
        )


if __name__ == "__main__":
    unittest.main()
