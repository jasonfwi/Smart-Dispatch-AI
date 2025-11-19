"""
Tests for Flask API endpoints.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestAPIEndpoints:
    """Test Flask API endpoints."""
    
    def test_init_endpoint(self, client):
        """Test /api/init endpoint."""
        response = client.post('/api/init', json={'max_range_km': 50})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
    
    def test_dispatch_search_endpoint(self, client):
        """Test /api/dispatches/search endpoint."""
        response = client.post('/api/dispatches/search', json={
            'assignment_status': 'unassigned',
            'state': 'NY',
            'limit': 100
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
    
    def test_dispatch_ids_endpoint(self, client):
        """Test /api/dispatches/ids endpoint."""
        response = client.get('/api/dispatches/ids')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
        assert 'dispatch_ids' in data
    
    def test_skills_endpoint(self, client):
        """Test /api/skills endpoint."""
        response = client.get('/api/skills')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
        assert 'skills' in data
    
    def test_unassigned_endpoint(self, client):
        """Test /api/unassigned endpoint (legacy)."""
        response = client.post('/api/unassigned', json={
            'date': '2025-11-20',
            'city': 'New York',
            'state': 'NY',
            'limit': 100
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
    
    def test_city_capacity_endpoint(self, client):
        """Test /api/city/capacity endpoint."""
        response = client.post('/api/city/capacity', json={
            'city': 'New York',
            'state': 'NY',
            'date': '2025-11-20'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
    
    def test_technician_availability_endpoint(self, client):
        """Test /api/technician/availability endpoint."""
        response = client.post('/api/technician/availability', json={
            'tech_id': 'T900000',
            'date': '2025-11-20'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
    
    def test_maintenance_stats_endpoint(self, client):
        """Test /api/maintenance/stats endpoint."""
        response = client.get('/api/maintenance/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
        assert 'stats' in data
    
    def test_maintenance_history_endpoint(self, client):
        """Test /api/maintenance/history endpoint."""
        response = client.post('/api/maintenance/history', json={
            'limit': 10,
            'offset': 0
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
        assert 'history' in data
    
    def test_generate_week_endpoint(self, client):
        """Test /api/technician/generate-week endpoint."""
        response = client.post('/api/technician/generate-week', json={
            'tech_id': 'T900000',
            'week_start': '2025-12-01',
            'available': 1,
            'start_time': '09:00',
            'end_time': '17:00',
            'max_assignments': 8,
            'include_weekend': False
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
    
    def test_error_handling(self, client):
        """Test API error handling."""
        # Missing required parameters
        response = client.post('/api/dispatches/search', json={})
        
        # Should still return 200 with success: true (no required params)
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
    
    def test_cities_endpoint(self, client):
        """Test /api/cities endpoint."""
        response = client.get('/api/cities')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert 'success' in data
        assert 'cities' in data or 'states' in data

