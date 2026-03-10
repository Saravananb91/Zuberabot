"""Test conversational fund recommendation flow."""

import asyncio
from zuberabot.agent.tools.finance import FinanceTool


async def test_conversational_recommendations():
    """Test the interactive recommendation flow."""
    tool = FinanceTool()
    
    print("=" * 70)
    print("Testing Conversational Fund Recommendations")
    print("=" * 70)
    
    # Test 1: No parameters - should ask for risk profile
    print("\n📝 TEST 1: Starting with no parameters")
    print("-" * 70)
    result = await tool.execute(action="get_fund_recommendation")
    print(result)
    
    # Test 2: Only risk profile - should ask for investment amount
    print("\n\n📝 TEST 2: Providing risk profile only")
    print("-" * 70)
    result = await tool.execute(action="get_fund_recommendation", risk_profile="moderate")
    print(result)
    
    # Test 3: Risk profile + investment amount - should ask for goal
    print("\n\n📝 TEST 3: Providing risk profile and investment amount")
    print("-" * 70)
    result = await tool.execute(action="get_fund_recommendation", 
                                risk_profile="moderate", 
                                investment_amount=10000)
    print(result)
    
    # Test 4: All parameters - should get recommendations
    print("\n\n📝 TEST 4: Providing all parameters - getting recommendations")
    print("-" * 70)
    result = await tool.execute(action="get_fund_recommendation",
                                risk_profile="moderate",
                                investment_amount=10000,
                                investment_goal="retirement")
    print(result)
    
    # Test 5: Different combination - aggressive wealth building
    print("\n\n📝 TEST 5: Aggressive risk for wealth building")
    print("-" * 70)
    result = await tool.execute(action="get_fund_recommendation",
                                risk_profile="aggressive",
                                investment_amount=25000,
                                investment_goal="wealth")
    print(result)
    
    # Test  6: Conservative emergency fund
    print("\n\n📝 TEST 6: Conservative risk for emergency fund")
    print("-" * 70)
    result = await tool.execute(action="get_fund_recommendation",
                                risk_profile="conservative",
                                investment_amount=5000,
                                investment_goal="emergency")
    print(result)
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_conversational_recommendations())
