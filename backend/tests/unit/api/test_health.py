from app.main import app


def test_health_route_exists():
    # Simple placeholder test to validate test wiring.
    assert app is not None
    # Check that health route exists
    routes = [route.path for route in app.routes]
    assert "/health" in routes
