"""Finance tools using yfinance and MF API."""

import json
from typing import Any
from zuberabot.agent.tools.base import Tool
from zuberabot.utils.mf_api import MFAPIClient

class FinanceTool(Tool):
    """Get financial data using yfinance."""
    
    name = "finance_tool"
    description = "Get stock prices, fund info, and market news."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get_stock_price", "get_fund_info", "market_news", "recommend_funds", "compare_funds", "search_funds", "get_fund_nav", "get_fund_recommendation"],
                "description": "The action to perform"
            },
            "symbol": {
                "type": "string",
                "description": "Stock/Fund symbol (e.g., AAPL, SPY, TATAMOTORS.NS)"
            },
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple symbols for comparison"
            },
            "risk_profile": {
                "type": "string",
                "enum": ["conservative", "moderate", "aggressive"],
                "description": "Investment risk profile"
            },
            "investment_amount": {
                "type": "number",
                "description": "Monthly investment amount in INR"
            },
            "query": {
                "type": "string",
                "description": "Search query for news or fund search"
            },
            "scheme_code": {
                "type": "string",
                "description": "Mutual fund scheme code (e.g., 119551 for Aditya Birla fund)"
            },
            "investment_goal": {
                "type": "string",
                "enum": ["retirement", "wealth", "emergency", "child_education", "short_term"],
                "description": "Investment goal or purpose"
            }
        },
        "required": ["action"]
    }
    
    async def execute(self, **kwargs: Any) -> str:
        """Execute the finance action."""
        try:
            import yfinance as yf
            
            action = kwargs.get('action')
            symbol = kwargs.get('symbol', '')
            query = kwargs.get('query', '')
            
            if action == "get_stock_price":
                if not symbol:
                    return "Please provide a stock symbol."
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
                return f"📈 {info.get('longName', symbol)}: ${price}"
            
            elif action == "get_fund_info":
                if not symbol:
                    return "Please provide a fund symbol."
                ticker = yf.Ticker(symbol)
                info = ticker.info
                response = [f"💼 **{info.get('longName', symbol)}**"]
                response.append(f"• NAV: {info.get('navPrice', 'N/A')}")
                response.append(f"• Category: {info.get('category', 'N/A')}")
                response.append(f"• YTD Return: {info.get('ytdReturn', 'N/A')}")
                return "\n".join(response)
            
            elif action == "market_news":
                if symbol:
                    ticker = yf.Ticker(symbol)
                    return json.dumps(ticker.news[:3], indent=2)
                return "Please provide a symbol to get news for (general market news requires web search)."
            
            elif action == "search_funds":
                if not query:
                    return "Error: Search query required"
                
                # Search for mutual funds
                results = await MFAPIClient.search_funds(query, limit=5)
                
                if not results:
                    return f"No mutual funds found matching '{query}'"
                
                response = [f"🔍 **Mutual Fund Search Results** for '{query}':\n"]
                for fund in results:
                    scheme_code = fund.get('schemeCode')
                    scheme_name = fund.get('schemeName', 'Unknown')
                    
                    # Try to get latest NAV
                    nav = await MFAPIClient.get_latest_nav(str(scheme_code))
                    nav_str = f" - NAV: ₹{nav:.2f}" if nav else ""
                    
                    response.append(f"• **{scheme_name}**{nav_str}")
                    response.append(f"  Code: {scheme_code}\n")
                
                response.append("💡 Use 'get_fund_nav' with scheme code to get detailed info!")
                return "\n".join(response)
            
            elif action == "get_fund_nav":
                scheme_code = kwargs.get('scheme_code') or symbol
                if not scheme_code:
                    return "Error: Scheme code required"
                
                # Get fund details
                details = await MFAPIClient.get_fund_details(str(scheme_code))
                if not details:
                    return f"Could not fetch details for scheme code {scheme_code}"
                
                meta = details.get('meta', {})
                nav_data = details.get('data', [])
                
                # Get latest NAV and calculate returns
                latest_nav = await MFAPIClient.get_latest_nav(str(scheme_code))
                returns_1y = await MFAPIClient.calculate_returns(str(scheme_code), months=12)
                returns_3y = await MFAPIClient.calculate_returns(str(scheme_code), months=36)
                
                response = ["📊 **Mutual Fund Details**\n"]
                response.append(f"**Name:** {meta.get('scheme_name', 'N/A')}")
                response.append(f"**Fund House:** {meta.get('fund_house', 'N/A')}")
                response.append(f"**Category:** {meta.get('scheme_category', meta.get('scheme_type', 'N/A'))}")
                response.append(f"**Scheme Code:** {scheme_code}\n")
                
                if latest_nav:
                    response.append(f"**Latest NAV:** ₹{latest_nav:.4f}")
                    if nav_data:
                        response.append(f"**Date:** {nav_data[0].get('date', 'N/A')}\n")
                
                if returns_1y is not None:
                    response.append(f"**1 Year Return:** {returns_1y:+.2f}%")
                if returns_3y is not None:
                    response.append(f"**3 Year Return:** {returns_3y:+.2f}%")
                
                return "\n".join(response)
            
            elif action == "recommend_funds":
                risk_profile = kwargs.get('risk_profile', 'moderate')
                investment_amount = kwargs.get('investment_amount', 5000)
                
                # Real Indian mutual fund recommendations with scheme codes
                recommendations = {
                    'conservative': [
                        ('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund'),
                        ('100828', 'Kotak Liquid Fund'),
                        ('100868', 'HDFC Liquid Fund')
                    ],
                    'moderate': [
                        ('100119', 'HDFC Balanced Advantage Fund'),
                        ('100414', 'Tata Aggressive Hybrid Fund'),
                        ('100684', 'UTI Aggressive Hybrid Fund')
                    ],
                    'aggressive': [
                        ('100080', 'DSP Flexi Cap Fund'),
                        ('101762', 'HDFC Flexi Cap Fund'),
                        ('100520', 'Franklin India Flexi Cap Fund')
                    ]
                }
                
                funds = recommendations.get(risk_profile, recommendations['moderate'])
                response = [f"📊 **Recommended Mutual Funds** ({risk_profile} risk profile):"]
                response.append(f"💰 Monthly Investment: ₹{investment_amount}\n")
                
                for scheme_code, name in funds:
                    # Get NAV and returns
                    nav = await MFAPIClient.get_latest_nav(scheme_code)
                    returns = await MFAPIClient.calculate_returns(scheme_code, months=12)
                    
                    nav_str = f" - ₹{nav:.2f}" if nav else ""
                    returns_str = f" ({returns:+.2f}% 1Y)" if returns is not None else ""
                    
                    response.append(f"• **{name}**{nav_str}{returns_str}")
                    response.append(f"  Code: {scheme_code}\n")
                
                response.append("💡 Use 'get_fund_nav' with scheme code for more details!")
                return "\n".join(response)
            
            elif action == "get_fund_recommendation":
                # Interactive fund recommendation with questionnaire
                risk_profile = kwargs.get('risk_profile')
                investment_amount = kwargs.get('investment_amount')
                investment_goal = kwargs.get('investment_goal')
                
                # Step 1: Ask for risk profile if not provided
                if not risk_profile:
                    return """🎯 **Let's find the perfect mutual funds for you!**

I'll need to ask a few questions to provide personalized recommendations.

**Question 1/3: What's your risk profile?**

1️⃣ **Conservative** - Low risk, stable returns (Debt funds)
   • Suitable for: Risk-averse investors, short-term goals
   • Expected returns: 6-8% annually
   
2️⃣ **Moderate** - Balanced risk and growth (Hybrid funds)
   • Suitable for: Medium-term goals, balanced approach
   • Expected returns: 10-14% annually
   
3️⃣ **Aggressive** - Higher risk, maximum growth (Equity funds)
   • Suitable for: Long-term goals, higher risk tolerance
   • Expected returns: 12-18% annually

Please respond with: **conservative**, **moderate**, or **aggressive**"""
                
                # Step 2: Ask for investment amount if not provided
                if not investment_amount:
                    return f"""Great choice! You selected **{risk_profile}** risk profile.

**Question 2/3: How much do you want to invest monthly?**

💰 Please provide your monthly investment amount in ₹

Examples: 5000, 10000, 25000

(Minimum recommended: ₹1000)"""
                
                # Step 3: Ask for investment goal if not provided
                if not investment_goal:
                    return f"""Perfect! Monthly investment: **₹{investment_amount}**

**Question 3/3: What's your primary investment goal?**

1️⃣ **Retirement** - Long-term wealth creation (10+ years)
2️⃣ **Wealth** - Medium to long term wealth building (5-10 years)
3️⃣ **Emergency** - Safe, liquid emergency fund
4️⃣ **Child Education** - Goal-based planning (5-15 years)
5️⃣ **Short Term** - Short-term savings (1-3 years)

Please respond with: **retirement**, **wealth**, **emergency**, **child_education**, or **short_term**"""
                
                # All information collected - Generate personalized recommendations
                goal_based_funds = {
                    'retirement': {
                        'conservative': [('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Stable debt fund ideal for conservative long-term retirement corpus')],
                        'moderate': [
                            ('100119', 'HDFC Balanced Advantage Fund', 'Dynamic asset allocation perfect for retirement planning with balanced risk'),
                            ('100684', 'UTI Aggressive Hybrid Fund', 'Equity-oriented hybrid for long-term retirement wealth creation')
                        ],
                        'aggressive': [
                            ('101762', 'HDFC Flexi Cap Fund', 'Diversified equity fund for maximum long-term retirement growth'),
                            ('100080', 'DSP Flexi Cap Fund', 'Multi-cap equity fund for aggressive retirement portfolio')
                        ]
                    },
                    'wealth': {
                        'conservative': [('100828', 'Kotak Liquid Fund', 'Liquid fund for safe wealth accumulation')],
                        'moderate': [
                            ('100414', 'Tata Aggressive Hybrid Fund', 'Balanced fund for steady wealth creation'),
                            ('100119', 'HDFC Balanced Advantage Fund', 'Adaptive hybrid for wealth building')
                        ],
                        'aggressive': [
                            ('101762', 'HDFC Flexi Cap Fund', 'High-growth equity for wealth maximization'),
                            ('100520', 'Franklin India Flexi Cap Fund', 'Multi-cap fund for long-term wealth')
                        ]
                    },
                    'emergency': {
                        'conservative': [
                            ('100868', 'HDFC Liquid Fund', 'Highly liquid fund for emergency corpus'),
                            ('100828', 'Kotak Liquid Fund', 'Safe and liquid for emergency needs')
                        ],
                        'moderate': [('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Good liquidity with slightly better returns')],
                        'aggressive': [('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Even aggressive investors should keep emergency funds in debt')]
                    },
                    'child_education': {
                        'conservative': [('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Safe debt fund for child education goal')],
                        'moderate': [
                            ('100119', 'HDFC Balanced Advantage Fund', 'Balanced approach for medium-term education goal'),
                            ('100684', 'UTI Aggressive Hybrid Fund', 'Equity exposure for education fund growth')
                        ],
                        'aggressive': [
                            ('101762', 'HDFC Flexi Cap Fund', 'Long-term equity for higher education corpus'),
                            ('100080', 'DSP Flexi Cap Fund', 'Diversified equity for child education')
                        ]
                    },
                    'short_term': {
                        'conservative': [
                            ('100868', 'HDFC Liquid Fund', 'Best for short-term parking of funds'),
                            ('100828', 'Kotak Liquid Fund', 'Ultra-short duration for 1-3 year goals')
                        ],
                        'moderate': [('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Moderate duration for short-term goals')],
                        'aggressive': [('119551', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Avoid equity for short-term - stick to debt')]
                    }
                }
                
                funds = goal_based_funds.get(investment_goal, goal_based_funds['wealth']).get(risk_profile, [])
                if not funds:
                    funds = [('100119', 'HDFC Balanced Advantage Fund', 'Balanced fund suitable for most goals')]
                
                response = ["🎯 **Your Personalized Mutual Fund Recommendations**\n"]
                response.append("**Your Investment Profile:**")
                response.append(f"• Risk Profile: **{risk_profile.title()}**")
                response.append(f"• Monthly Investment: **₹{investment_amount}**")
                response.append(f"• Investment Goal: **{investment_goal.replace('_', ' ').title()}**\n")
                response.append("**Recommended Funds:**\n")
                
                for idx, (scheme_code, name, explanation) in enumerate(funds, 1):
                    nav = await MFAPIClient.get_latest_nav(scheme_code)
                    returns_1y = await MFAPIClient.calculate_returns(scheme_code, months=12)
                    nav_str = f" - ₹{nav:.2f}" if nav else ""
                    returns_str = f" ({returns_1y:+.2f}% 1Y)" if returns_1y is not None else ""
                    response.append(f"**{idx}. {name}**{nav_str}{returns_str}")
                    response.append(f"   📍 Code: {scheme_code}")
                    response.append(f"   💡 Why: {explanation}\n")
                
                advice = {
                    'retirement': "💡 **Tip:** For retirement planning, stay invested for 15+ years and increase SIP amount as your income grows.",
                    'wealth': "💡 **Tip:** Review your portfolio annually and rebalance if needed to maintain desired asset allocation.",
                    'emergency': "💡 **Tip:** Keep 6-12 months of expenses as emergency fund. Don't invest this in equity.",
                    'child_education': "💡 **Tip:** Start early and increase equity allocation when timeline is longer. Shift to debt as goal approaches.",
                    'short_term': "💡 **Tip:** Avoid equity for goals less than 3 years. Stick to liquid/debt funds for capital safety."
                }
                response.append(advice.get(investment_goal, "💡 Invest regularly and stay disciplined for best results!"))
                response.append("\n💡 Use 'get_fund_nav' with scheme code for detailed fund information!")
                return "\n".join(response)
            
            elif action == "compare_funds":
                symbols = kwargs.get('symbols', [])
                if not symbols or len(symbols) < 2:
                    return "❌ Error: Please provide at least 2 fund symbols to compare"
                
                comparison = ["📊 **Fund Comparison**\n"]
                for sym in symbols[:3]:  # Limit to 3 funds
                    try:
                        ticker = yf.Ticker(sym)
                        info = ticker.info
                        hist = ticker.history(period="1y")
                        
                        # Calculate 1-year return
                        if not hist.empty:
                            year_return = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                        else:
                            year_return = 0
                        
                        comparison.append(f"**{info.get('longName', sym)}**")
                        comparison.append(f"• 1Y Return: {year_return:.2f}%")
                        comparison.append(f"• Category: {info.get('category', 'N/A')}")
                        comparison.append(f"• Expense Ratio: {info.get('annualReportExpenseRatio', 'N/A')}")
                        comparison.append("")
                    except:
                        comparison.append(f"**{sym}**: Data unavailable\n")
                
                return "\n".join(comparison)
            
            return f"Unknown action: {action}"

        except Exception as e:
            return f"Finance Tool Error: {e}"
