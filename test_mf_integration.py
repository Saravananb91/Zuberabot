"""Test script for MF API integration."""

import asyncio
from zuberabot.utils.mf_api import MFAPIClient
from zuberabot.agent.tools.finance import FinanceTool


async def test_mf_api():
    """Test MF API client functionality."""
    print("=" * 60)
    print("Testing MF API Integration")
    print("=" * 60)
    
    # Test 1: Search for funds
    print("\n1. Testing fund search (HDFC equity)...")
    results = await MFAPIClient.search_funds("HDFC equity", limit=3)
    for fund in results:
        print(f"   - {fund.get('schemeName')} (Code: {fund.get('schemeCode')})")
    
    # Test 2: Get fund details
    print("\n2. Testing fund details (scheme code 119551)...")
    details = await MFAPIClient.get_fund_details("119551")
    if details:
        meta = details.get('meta', {})
        print(f"   - Fund: {meta.get('scheme_name')}")
        print(f"   - House: {meta.get('fund_house')}")
        print(f"   - Category: {meta.get('scheme_category')}")
    
    # Test 3: Get latest NAV
    print("\n3. Testing NAV retrieval...")
    nav = await MFAPIClient.get_latest_nav("119551")
    if nav:
        print(f"   - Latest NAV: Rs. {nav:.4f}")
    
    # Test 4: Calculate returns
    print("\n4. Testing return calculation...")
    returns_1y = await MFAPIClient.calculate_returns("119551", months=12)
    returns_3y = await MFAPIClient.calculate_returns("119551", months=36)
    if returns_1y:
        print(f"   - 1 Year Return: {returns_1y:+.2f}%")
    if returns_3y:
        print(f"   - 3 Year Return: {returns_3y:+.2f}%")
    
    # Test 5: Finance tool integration
    print("\n5. Testing FinanceTool integration...")
    tool = FinanceTool()
    
    # Test search_funds action
    print("\n   a) Testing search_funds action...")
    result = await tool.execute(action="search_funds", query="ICICI liquid")
    print(result[:200] + "..." if len(result) > 200 else result)
    
    # Test get_fund_nav action
    print("\n   b) Testing get_fund_nav action...")
    result = await tool.execute(action="get_fund_nav", scheme_code="119551")
    print(result)
    
    # Test recommend_funds action
    print("\n   c) Testing recommend_funds action...")
    result = await tool.execute(action="recommend_funds", risk_profile="moderate", investment_amount=10000)
    print(result)
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mf_api())
