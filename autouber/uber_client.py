#!/usr/bin/env python3
"""
Uber API Client
Handles all interactions with Uber's REST API
"""

import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

class UberClient:
    """
    Client for interacting with Uber's API
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.sandbox_mode = config.get("sandbox_mode", True)
        self.default_ride_type = config.get("default_ride_type", "UberX")
        
        # API endpoints
        if self.sandbox_mode:
            self.base_url = "https://sandbox-api.uber.com/v1"
        else:
            self.base_url = "https://api.uber.com/v1"
            
        # Authentication
        self.access_token = None
        self.token_expires_at = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Cache for estimates to reduce API calls
        self.estimate_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def authenticate(self) -> bool:
        """
        Authenticate with Uber using OAuth 2.0
        In production, this would handle the full OAuth flow
        """
        if not self.client_id or not self.client_secret:
            self.logger.warning("Uber API credentials not configured - using sandbox mode")
            return self._setup_sandbox_mode()
            
        try:
            # For now, we'll simulate authentication
            # In production, this would make actual OAuth requests
            self.access_token = "sandbox_token_" + str(int(time.time()))
            self.token_expires_at = datetime.now() + timedelta(hours=1)
            
            self.logger.info("Successfully authenticated with Uber API")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Uber API: {e}")
            return False
    
    def _setup_sandbox_mode(self) -> bool:
        """Setup sandbox mode for testing"""
        self.logger.info("Using Uber API sandbox mode")
        self.access_token = "sandbox_token"
        self.token_expires_at = datetime.now() + timedelta(hours=24)
        return True
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return self.authenticate()
        return True
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Uber API"""
        if not self._ensure_authenticated():
            return None
            
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            if self.sandbox_mode:
                # Simulate API responses in sandbox mode
                return self._simulate_api_response(endpoint, data)
                
            if method == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Uber API request failed: {e}")
            return None
    
    def _simulate_api_response(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Simulate Uber API responses for sandbox/testing"""
        import random
        
        if "/estimates/price" in endpoint:
            return {
                "prices": [
                    {
                        "product_id": "26546650-e557-4a7b-86e7-6a3942445247",
                        "currency_code": "USD",
                        "display_name": "UberX",
                        "estimate": "$12-15",
                        "low_estimate": 12,
                        "high_estimate": 15,
                        "surge_multiplier": 1.0,
                        "duration": 660,
                        "distance": 3.2
                    },
                    {
                        "product_id": "26546650-e557-4a7b-86e7-6a3942445248",
                        "currency_code": "USD", 
                        "display_name": "UberBlack",
                        "estimate": "$18-22",
                        "low_estimate": 18,
                        "high_estimate": 22,
                        "surge_multiplier": 1.0,
                        "duration": 660,
                        "distance": 3.2
                    }
                ]
            }
            
        elif "/estimates/time" in endpoint:
            return {
                "times": [
                    {
                        "product_id": "26546650-e557-4a7b-86e7-6a3942445247",
                        "display_name": "UberX",
                        "estimate": random.randint(180, 600)  # 3-10 minutes
                    }
                ]
            }
            
        elif "/products" in endpoint:
            return {
                "products": [
                    {
                        "product_id": "26546650-e557-4a7b-86e7-6a3942445247",
                        "description": "The low-cost Uber",
                        "display_name": "UberX",
                        "capacity": 4,
                        "image": "http://d1a3f4spazzrp4.cloudfront.net/car.jpg"
                    },
                    {
                        "product_id": "26546650-e557-4a7b-86e7-6a3942445248",
                        "description": "The premium Uber",
                        "display_name": "UberBlack", 
                        "capacity": 4,
                        "image": "http://d1a3f4spazzrp4.cloudfront.net/car-black.jpg"
                    }
                ]
            }
            
        elif "/requests" in endpoint:
            return {
                "request_id": f"ride_{int(time.time())}_{random.randint(1000, 9999)}",
                "status": "processing",
                "vehicle": None,
                "driver": None,
                "location": None,
                "eta": random.randint(300, 900),  # 5-15 minutes
                "surge_multiplier": 1.0
            }
            
        else:
            return {"status": "success"}
    
    def get_available_products(self, location: Tuple[float, float]) -> List[Dict]:
        """Get available Uber products at a location"""
        lat, lon = location
        endpoint = f"/products?latitude={lat}&longitude={lon}"
        
        response = self._make_request("GET", endpoint)
        if response:
            return response.get("products", [])
        return []
    
    def get_price_estimates(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Dict]:
        """Get price estimates for a trip"""
        # Check cache first
        cache_key = f"price_{origin}_{destination}"
        cached = self._get_cached_estimate(cache_key)
        if cached:
            return cached
            
        start_lat, start_lon = origin
        end_lat, end_lon = destination
        
        endpoint = f"/estimates/price?start_latitude={start_lat}&start_longitude={start_lon}&end_latitude={end_lat}&end_longitude={end_lon}"
        
        response = self._make_request("GET", endpoint)
        if response:
            estimates = response.get("prices", [])
            self._cache_estimate(cache_key, estimates)
            return estimates
        return []
    
    def get_time_estimates(self, location: Tuple[float, float]) -> List[Dict]:
        """Get pickup time estimates at a location"""
        # Check cache first
        cache_key = f"time_{location}"
        cached = self._get_cached_estimate(cache_key)
        if cached:
            return cached
            
        lat, lon = location
        endpoint = f"/estimates/time?start_latitude={lat}&start_longitude={lon}"
        
        response = self._make_request("GET", endpoint)
        if response:
            estimates = response.get("times", [])
            self._cache_estimate(cache_key, estimates)
            return estimates
        return []
    
    def get_estimated_pickup_time(self, location: Tuple[float, float], ride_type: str = None) -> timedelta:
        """Get estimated pickup time for a specific ride type"""
        if not ride_type:
            ride_type = self.default_ride_type
            
        estimates = self.get_time_estimates(location)
        
        for estimate in estimates:
            if estimate.get("display_name") == ride_type:
                seconds = estimate.get("estimate", 300)  # Default 5 minutes
                return timedelta(seconds=seconds)
                
        # Default estimate if not found
        return timedelta(minutes=5)
    
    def get_estimated_cost(self, origin: Tuple[float, float], destination: Tuple[float, float], 
                          ride_type: str = None) -> Optional[float]:
        """Get estimated cost for a trip"""
        if not ride_type:
            ride_type = self.default_ride_type
            
        estimates = self.get_price_estimates(origin, destination)
        
        for estimate in estimates:
            if estimate.get("display_name") == ride_type:
                # Return average of low and high estimate
                low = estimate.get("low_estimate", 0)
                high = estimate.get("high_estimate", 0)
                if low and high:
                    return (low + high) / 2
                    
        return None
    
    def get_estimated_travel_time(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> timedelta:
        """Get estimated travel time between two points"""
        estimates = self.get_price_estimates(origin, destination)
        
        if estimates:
            # Use duration from first estimate
            duration_seconds = estimates[0].get("duration", 600)  # Default 10 minutes
            return timedelta(seconds=duration_seconds)
            
        # Fallback calculation based on distance
        distance = self._calculate_distance(origin, destination)
        # Assume average speed of 25 mph in city
        travel_time_hours = distance / 40233.6  # meters to miles conversion and speed
        return timedelta(hours=travel_time_hours)
    
    def request_ride(self, origin: Tuple[float, float], destination: Tuple[float, float], 
                    ride_type: str = None) -> Optional[str]:
        """Request an Uber ride"""
        if not ride_type:
            ride_type = self.default_ride_type
            
        # Get product ID for ride type
        products = self.get_available_products(origin)
        product_id = None
        
        for product in products:
            if product.get("display_name") == ride_type:
                product_id = product.get("product_id")
                break
                
        if not product_id:
            self.logger.error(f"Ride type {ride_type} not available")
            return None
            
        start_lat, start_lon = origin
        end_lat, end_lon = destination
        
        request_data = {
            "product_id": product_id,
            "start_latitude": start_lat,
            "start_longitude": start_lon,
            "end_latitude": end_lat,
            "end_longitude": end_lon
        }
        
        response = self._make_request("POST", "/requests", request_data)
        
        if response:
            ride_id = response.get("request_id")
            self.logger.info(f"Successfully requested {ride_type} ride: {ride_id}")
            return ride_id
        
        self.logger.error("Failed to request ride")
        return None
    
    def get_ride_status(self, ride_id: str) -> Optional[Dict]:
        """Get status of a ride request"""
        endpoint = f"/requests/{ride_id}"
        return self._make_request("GET", endpoint)
    
    def cancel_ride(self, ride_id: str) -> bool:
        """Cancel a ride request"""
        endpoint = f"/requests/{ride_id}"
        response = self._make_request("DELETE", endpoint)
        return response is not None
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Haversine formula
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Earth radius in meters
        
        return c * r
    
    def _get_cached_estimate(self, key: str) -> Optional[List[Dict]]:
        """Get cached estimate if still valid"""
        if key in self.estimate_cache:
            cached_data, timestamp = self.estimate_cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        return None
    
    def _cache_estimate(self, key: str, data: List[Dict]):
        """Cache an estimate"""
        self.estimate_cache[key] = (data, time.time())
        
        # Clean old cache entries
        current_time = time.time()
        self.estimate_cache = {
            k: v for k, v in self.estimate_cache.items()
            if current_time - v[1] < self.cache_ttl
        }

if __name__ == "__main__":
    # Test the Uber client
    config = {
        "client_id": "test",
        "client_secret": "test", 
        "sandbox_mode": True
    }
    
    client = UberClient(config)
    
    # Test coordinates (downtown area)
    origin = (37.7749, -122.4194)  # San Francisco
    destination = (37.7849, -122.4094)
    
    print("Testing Uber API client...")
    
    # Test products
    products = client.get_available_products(origin)
    print(f"Available products: {len(products)}")
    
    # Test price estimates
    prices = client.get_price_estimates(origin, destination)
    print(f"Price estimates: {prices}")
    
    # Test time estimates
    times = client.get_time_estimates(origin)
    print(f"Time estimates: {times}")
    
    # Test ride request (sandbox mode)
    ride_id = client.request_ride(origin, destination)
    print(f"Ride requested: {ride_id}")
