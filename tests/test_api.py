"""
Tests for Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        name: {**details, "participants": details["participants"].copy()}
        for name, details in activities.items()
    }
    
    # Reset to original state after each test
    yield
    
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


def test_root_redirects(client):
    """Test that root URL redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test GET /activities endpoint"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Verify it returns a dictionary with activities
    assert isinstance(data, dict)
    assert len(data) > 0
    
    # Verify structure of an activity
    assert "Soccer Team" in data
    activity = data["Soccer Team"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Sign up
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify participant was added
    updated_response = client.get("/activities")
    updated_activity = updated_response.json()[activity_name]
    assert len(updated_activity["participants"]) == initial_count + 1
    assert email in updated_activity["participants"]


def test_signup_duplicate_prevention(client):
    """Test that signing up twice is prevented"""
    email = "duplicate@mergington.edu"
    activity_name = "Math Olympiad"
    
    # First signup should succeed
    response1 = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Student is already signed up"


def test_signup_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    email = "student@mergington.edu"
    activity_name = "Nonexistent Activity"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_success(client):
    """Test successful unregistration from an activity"""
    email = "test@mergington.edu"
    activity_name = "Drama Club"
    
    # First sign up
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Get participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Unregister
    response = client.delete(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify participant was removed
    updated_response = client.get("/activities")
    updated_activity = updated_response.json()[activity_name]
    assert len(updated_activity["participants"]) == initial_count - 1
    assert email not in updated_activity["participants"]


def test_unregister_not_signed_up(client):
    """Test unregistering when not signed up"""
    email = "notsignedup@mergington.edu"
    activity_name = "Basketball Club"
    
    response = client.delete(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_nonexistent_activity(client):
    """Test unregistering from a non-existent activity"""
    email = "student@mergington.edu"
    activity_name = "Nonexistent Activity"
    
    response = client.delete(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_and_unregister_existing_participant(client):
    """Test unregistering an existing participant"""
    activity_name = "Soccer Team"
    
    # Get the first existing participant
    initial_response = client.get("/activities")
    existing_email = initial_response.json()[activity_name]["participants"][0]
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Unregister existing participant
    response = client.delete(
        f"/activities/{activity_name}/signup?email={existing_email}"
    )
    assert response.status_code == 200
    
    # Verify they were removed
    updated_response = client.get("/activities")
    updated_activity = updated_response.json()[activity_name]
    assert len(updated_activity["participants"]) == initial_count - 1
    assert existing_email not in updated_activity["participants"]


def test_special_characters_in_activity_name(client):
    """Test signup with URL-encoded activity name"""
    # Programming Class has a space in it
    email = "programmer@mergington.edu"
    activity_name = "Programming Class"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 200
