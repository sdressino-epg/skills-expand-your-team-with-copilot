# Testing Activities.py

This directory contains comprehensive unit tests for the `activities.py` router module.

## Running the Tests

### Basic test run:
```bash
cd src
python -m pytest tests/test_activities.py -v
```

### Run tests with coverage:
```bash
cd src  
python -m pytest tests/test_activities.py --cov=backend.routers.activities --cov-report=term-missing
```

### Run all tests:
```bash
cd src
python -m pytest
```

## Test Coverage

The test suite achieves **100% code coverage** for the `activities.py` module, testing:

- All 4 endpoints: `get_activities`, `get_available_days`, `signup_for_activity`, `unregister_from_activity`
- Success scenarios
- Error handling (authentication failures, not found errors, validation errors)
- Edge cases (empty database, empty participants list)
- Database interaction failures

## Test Structure

- **TestGetActivities**: Tests for the GET /activities endpoint with filtering
- **TestGetAvailableDays**: Tests for the GET /activities/days endpoint
- **TestSignupForActivity**: Tests for the POST /{activity_name}/signup endpoint
- **TestUnregisterFromActivity**: Tests for the POST /{activity_name}/unregister endpoint  
- **TestActivitiesEdgeCases**: Additional edge case scenarios

All database interactions are mocked to ensure unit tests run independently without requiring a MongoDB instance.