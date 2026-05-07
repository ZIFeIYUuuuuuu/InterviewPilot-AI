import unittest

from backend.app.api.v1.routes.health import health_check
from backend.app.main import app


class BackendSkeletonTests(unittest.TestCase):
    def test_health_route_is_registered(self):
        paths = {route.path for route in app.routes}

        self.assertIn("/api/v1/health", paths)

    def test_health_check_response_shape(self):
        response = health_check()

        self.assertEqual("ok", response.status)
        self.assertEqual("InterviewPilot AI", response.service)
        self.assertEqual("/api/v1", response.api_prefix)


if __name__ == "__main__":
    unittest.main()
