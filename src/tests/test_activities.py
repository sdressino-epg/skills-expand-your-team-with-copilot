"""
Unit tests for the activities.py router module.

Tests all endpoints in the activities router with comprehensive coverage of:
- Success scenarios
- Error handling 
- Authentication requirements
- Database interactions
- Edge cases
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.routers.activities import router, get_activities, get_available_days, signup_for_activity, unregister_from_activity


class TestGetActivities:
    """Test cases for the get_activities endpoint."""
    
    def test_get_activities_no_filters(self):
        """Test getting all activities without any filters."""
        # Mock database response
        mock_activities = [
            {
                "_id": "Chess Club",
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
                "schedule_details": {
                    "days": ["Monday", "Friday"],
                    "start_time": "15:15",
                    "end_time": "16:45"
                },
                "max_participants": 12,
                "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
            },
            {
                "_id": "Programming Class",
                "description": "Learn programming fundamentals",
                "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
                "schedule_details": {
                    "days": ["Tuesday", "Thursday"],
                    "start_time": "07:00",
                    "end_time": "08:00"
                },
                "max_participants": 20,
                "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
            }
        ]
        
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.find.return_value = mock_activities.copy()
            
            result = get_activities()
            
            # Verify the query was called with empty filter
            mock_collection.find.assert_called_once_with({})
            
            # Verify the response structure
            assert len(result) == 2
            assert "Chess Club" in result
            assert "Programming Class" in result
            assert result["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
            assert result["Programming Class"]["max_participants"] == 20
    
    def test_get_activities_with_day_filter(self):
        """Test getting activities filtered by day."""
        mock_activities = [
            {
                "_id": "Chess Club",
                "description": "Learn strategies and compete in chess tournaments",
                "schedule_details": {
                    "days": ["Monday", "Friday"],
                    "start_time": "15:15",
                    "end_time": "16:45"
                },
                "max_participants": 12,
                "participants": []
            }
        ]
        
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.find.return_value = mock_activities.copy()
            
            result = get_activities(day="Monday")
            
            # Verify the query was called with day filter
            expected_query = {"schedule_details.days": {"$in": ["Monday"]}}
            mock_collection.find.assert_called_once_with(expected_query)
            
            assert len(result) == 1
            assert "Chess Club" in result
    
    def test_get_activities_with_time_filters(self):
        """Test getting activities filtered by start and end time."""
        mock_activities = [
            {
                "_id": "Morning Fitness",
                "description": "Early morning physical training",
                "schedule_details": {
                    "days": ["Monday", "Wednesday", "Friday"],
                    "start_time": "06:30",
                    "end_time": "07:45"
                },
                "max_participants": 30,
                "participants": []
            }
        ]
        
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.find.return_value = mock_activities.copy()
            
            result = get_activities(start_time="06:00", end_time="08:00")
            
            # Verify the query was called with time filters
            expected_query = {
                "schedule_details.start_time": {"$gte": "06:00"},
                "schedule_details.end_time": {"$lte": "08:00"}
            }
            mock_collection.find.assert_called_once_with(expected_query)
            
            assert len(result) == 1
            assert "Morning Fitness" in result

    def test_get_activities_with_all_filters(self):
        """Test getting activities with day, start time, and end time filters."""
        mock_activities = []
        
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.find.return_value = mock_activities
            
            result = get_activities(day="Tuesday", start_time="07:00", end_time="08:00")
            
            # Verify the query was called with all filters
            expected_query = {
                "schedule_details.days": {"$in": ["Tuesday"]},
                "schedule_details.start_time": {"$gte": "07:00"},
                "schedule_details.end_time": {"$lte": "08:00"}
            }
            mock_collection.find.assert_called_once_with(expected_query)
            
            assert len(result) == 0


class TestGetAvailableDays:
    """Test cases for the get_available_days endpoint."""
    
    def test_get_available_days_success(self):
        """Test getting available days successfully."""
        mock_aggregation_result = [
            {"_id": "Friday"},
            {"_id": "Monday"},
            {"_id": "Thursday"},
            {"_id": "Tuesday"},
            {"_id": "Wednesday"}
        ]
        
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.aggregate.return_value = mock_aggregation_result
            
            result = get_available_days()
            
            # Verify the aggregation pipeline was called correctly
            expected_pipeline = [
                {"$unwind": "$schedule_details.days"},
                {"$group": {"_id": "$schedule_details.days"}},
                {"$sort": {"_id": 1}}
            ]
            mock_collection.aggregate.assert_called_once_with(expected_pipeline)
            
            # Verify the result
            assert result == ["Friday", "Monday", "Thursday", "Tuesday", "Wednesday"]
    
    def test_get_available_days_empty(self):
        """Test getting available days when no activities exist."""
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.aggregate.return_value = []
            
            result = get_available_days()
            
            assert result == []


class TestSignupForActivity:
    """Test cases for the signup_for_activity endpoint."""
    
    def test_signup_success(self):
        """Test successful student signup for an activity."""
        mock_teacher = {
            "_id": "mrodriguez",
            "display_name": "Ms. Rodriguez",
            "role": "teacher"
        }
        
        mock_activity = {
            "_id": "Chess Club",
            "description": "Learn strategies and compete in chess tournaments",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        }
        
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            mock_activities.update_one.return_value = mock_update_result
            
            result = signup_for_activity(
                activity_name="Chess Club",
                email="student@mergington.edu",
                teacher_username="mrodriguez"
            )
            
            # Verify database calls
            mock_teachers.find_one.assert_called_once_with({"_id": "mrodriguez"})
            mock_activities.find_one.assert_called_once_with({"_id": "Chess Club"})
            mock_activities.update_one.assert_called_once_with(
                {"_id": "Chess Club"},
                {"$push": {"participants": "student@mergington.edu"}}
            )
            
            # Verify response
            assert result == {"message": "Signed up student@mergington.edu for Chess Club"}
    
    def test_signup_no_teacher_authentication(self):
        """Test signup failure when no teacher authentication is provided."""
        with pytest.raises(HTTPException) as exc_info:
            signup_for_activity(
                activity_name="Chess Club",
                email="student@mergington.edu",
                teacher_username=None
            )
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required for this action"
    
    def test_signup_invalid_teacher(self):
        """Test signup failure when teacher credentials are invalid."""
        with patch('backend.routers.activities.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                signup_for_activity(
                    activity_name="Chess Club",
                    email="student@mergington.edu",
                    teacher_username="invalid_teacher"
                )
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid teacher credentials"
    
    def test_signup_activity_not_found(self):
        """Test signup failure when activity doesn't exist."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                signup_for_activity(
                    activity_name="NonExistent Activity",
                    email="student@mergington.edu",
                    teacher_username="mrodriguez"
                )
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Activity not found"
    
    def test_signup_already_signed_up(self):
        """Test signup failure when student is already signed up."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        mock_activity = {
            "_id": "Chess Club",
            "participants": ["student@mergington.edu", "other@mergington.edu"]
        }
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            
            with pytest.raises(HTTPException) as exc_info:
                signup_for_activity(
                    activity_name="Chess Club",
                    email="student@mergington.edu",
                    teacher_username="mrodriguez"
                )
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Already signed up for this activity"
    
    def test_signup_database_update_failure(self):
        """Test signup failure when database update fails."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        mock_activity = {
            "_id": "Chess Club",
            "participants": ["other@mergington.edu"]
        }
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 0
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            mock_activities.update_one.return_value = mock_update_result
            
            with pytest.raises(HTTPException) as exc_info:
                signup_for_activity(
                    activity_name="Chess Club",
                    email="student@mergington.edu",
                    teacher_username="mrodriguez"
                )
            
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Failed to update activity"


class TestUnregisterFromActivity:
    """Test cases for the unregister_from_activity endpoint."""
    
    def test_unregister_success(self):
        """Test successful student unregistration from an activity."""
        mock_teacher = {
            "_id": "mrodriguez",
            "display_name": "Ms. Rodriguez",
            "role": "teacher"
        }
        
        mock_activity = {
            "_id": "Chess Club",
            "description": "Learn strategies and compete in chess tournaments",
            "max_participants": 12,
            "participants": ["student@mergington.edu", "michael@mergington.edu"]
        }
        
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            mock_activities.update_one.return_value = mock_update_result
            
            result = unregister_from_activity(
                activity_name="Chess Club",
                email="student@mergington.edu",
                teacher_username="mrodriguez"
            )
            
            # Verify database calls
            mock_teachers.find_one.assert_called_once_with({"_id": "mrodriguez"})
            mock_activities.find_one.assert_called_once_with({"_id": "Chess Club"})
            mock_activities.update_one.assert_called_once_with(
                {"_id": "Chess Club"},
                {"$pull": {"participants": "student@mergington.edu"}}
            )
            
            # Verify response
            assert result == {"message": "Unregistered student@mergington.edu from Chess Club"}
    
    def test_unregister_no_teacher_authentication(self):
        """Test unregister failure when no teacher authentication is provided."""
        with pytest.raises(HTTPException) as exc_info:
            unregister_from_activity(
                activity_name="Chess Club",
                email="student@mergington.edu",
                teacher_username=None
            )
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required for this action"
    
    def test_unregister_invalid_teacher(self):
        """Test unregister failure when teacher credentials are invalid."""
        with patch('backend.routers.activities.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                unregister_from_activity(
                    activity_name="Chess Club",
                    email="student@mergington.edu",
                    teacher_username="invalid_teacher"
                )
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid teacher credentials"
    
    def test_unregister_activity_not_found(self):
        """Test unregister failure when activity doesn't exist."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                unregister_from_activity(
                    activity_name="NonExistent Activity",
                    email="student@mergington.edu",
                    teacher_username="mrodriguez"
                )
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Activity not found"
    
    def test_unregister_not_registered(self):
        """Test unregister failure when student is not registered for the activity."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        mock_activity = {
            "_id": "Chess Club",
            "participants": ["other@mergington.edu", "another@mergington.edu"]
        }
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            
            with pytest.raises(HTTPException) as exc_info:
                unregister_from_activity(
                    activity_name="Chess Club",
                    email="student@mergington.edu",
                    teacher_username="mrodriguez"
                )
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Not registered for this activity"
    
    def test_unregister_database_update_failure(self):
        """Test unregister failure when database update fails."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        mock_activity = {
            "_id": "Chess Club",
            "participants": ["student@mergington.edu", "other@mergington.edu"]
        }
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 0
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            mock_activities.update_one.return_value = mock_update_result
            
            with pytest.raises(HTTPException) as exc_info:
                unregister_from_activity(
                    activity_name="Chess Club",
                    email="student@mergington.edu",
                    teacher_username="mrodriguez"
                )
            
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Failed to update activity"


# Edge cases and additional scenarios
class TestActivitiesEdgeCases:
    """Test edge cases and additional scenarios."""
    
    def test_get_activities_empty_database(self):
        """Test getting activities when database is empty."""
        with patch('backend.routers.activities.activities_collection') as mock_collection:
            mock_collection.find.return_value = []
            
            result = get_activities()
            
            assert result == {}
    
    def test_signup_with_empty_participants_list(self):
        """Test signup when activity has empty participants list."""
        mock_teacher = {"_id": "mrodriguez", "role": "teacher"}
        mock_activity = {
            "_id": "New Activity",
            "participants": []
        }
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        
        with patch('backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = mock_teacher
            mock_activities.find_one.return_value = mock_activity
            mock_activities.update_one.return_value = mock_update_result
            
            result = signup_for_activity(
                activity_name="New Activity",
                email="first@mergington.edu",
                teacher_username="mrodriguez"
            )
            
            assert result == {"message": "Signed up first@mergington.edu for New Activity"}