"""MF API Client for Indian Mutual Fund data.

API Documentation: https://api.mfapi.in
"""

import time
from typing import Any
import httpx


class MFAPIClient:
    """Client for fetching mutual fund data from MF API."""
    
    BASE_URL = "https://api.mfapi.in"
    
    # Simple in-memory caches
    _fund_list_cache: dict[str, Any] = {"data": None, "expires": 0}
    _nav_cache: dict[str, dict[str, Any]] = {}
    
    # Cache durations in seconds
    FUND_LIST_CACHE_DURATION = 86400  # 24 hours
    NAV_CACHE_DURATION = 3600  # 1 hour
    
    @classmethod
    async def get_all_funds(cls) -> list[dict[str, Any]]:
        """Fetch all mutual funds (cached for 24 hours)."""
        now = time.time()
        
        # Return cached data if valid
        if cls._fund_list_cache["data"] and now < cls._fund_list_cache["expires"]:
            return cls._fund_list_cache["data"]
        
        # Fetch fresh data
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{cls.BASE_URL}/mf")
                response.raise_for_status()
                funds = response.json()
                
                # Update cache
                cls._fund_list_cache["data"] = funds
                cls._fund_list_cache["expires"] = now + cls.FUND_LIST_CACHE_DURATION
                
                return funds
        except Exception as e:
            # Return cached data even if expired, or empty list
            return cls._fund_list_cache["data"] or []
    
    @classmethod
    async def search_funds(cls, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for mutual funds by name.
        
        Args:
            query: Search term (case-insensitive)
            limit: Maximum number of results to return
            
        Returns:
            List of matching funds with schemeCode and schemeName
        """
        funds = await cls.get_all_funds()
        query_lower = query.lower()
        
        # Filter funds matching the query
        matches = [
            fund for fund in funds
            if query_lower in fund.get("schemeName", "").lower()
        ]
        
        return matches[:limit]
    
    @classmethod
    async def get_fund_details(cls, scheme_code: str) -> dict[str, Any] | None:
        """Get detailed fund information including NAV history.
        
        Args:
            scheme_code: The mutual fund scheme code
            
        Returns:
            Dictionary with meta and data (NAV history), or None on error
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{cls.BASE_URL}/mf/{scheme_code}")
                response.raise_for_status()
                return response.json()
        except Exception:
            return None
    
    @classmethod
    async def get_latest_nav(cls, scheme_code: str) -> float | None:
        """Get the most recent NAV for a fund (cached for 1 hour).
        
        Args:
            scheme_code: The mutual fund scheme code
            
        Returns:
            Latest NAV value, or None if unavailable
        """
        now = time.time()
        
        # Check cache
        if scheme_code in cls._nav_cache:
            cache_entry = cls._nav_cache[scheme_code]
            if now < cache_entry["expires"]:
                return cache_entry["nav"]
        
        # Fetch fresh data
        details = await cls.get_fund_details(scheme_code)
        if not details or "data" not in details or not details["data"]:
            return None
        
        # Get latest NAV
        try:
            latest_nav = float(details["data"][0]["nav"])
            
            # Update cache
            cls._nav_cache[scheme_code] = {
                "nav": latest_nav,
                "expires": now + cls.NAV_CACHE_DURATION
            }
            
            return latest_nav
        except (IndexError, KeyError, ValueError):
            return None
    
    @classmethod
    async def calculate_returns(cls, scheme_code: str, months: int = 12) -> float | None:
        """Calculate returns over a specified period.
        
        Args:
            scheme_code: The mutual fund scheme code
            months: Number of months to calculate returns for (default: 12)
            
        Returns:
            Percentage return, or None if insufficient data
        """
        details = await cls.get_fund_details(scheme_code)
        if not details or "data" not in details:
            return None
        
        nav_history = details["data"]
        if len(nav_history) < 2:
            return None
        
        try:
            # Get latest NAV
            latest_nav = float(nav_history[0]["nav"])
            
            # Find NAV from ~months ago (approximate by trading days)
            # Assuming ~22 trading days per month
            target_index = min(months * 22, len(nav_history) - 1)
            old_nav = float(nav_history[target_index]["nav"])
            
            # Calculate percentage return
            returns = ((latest_nav - old_nav) / old_nav) * 100
            return round(returns, 2)
        except (IndexError, KeyError, ValueError):
            return None
