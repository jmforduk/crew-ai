
import re
import math
from typing import Union, Dict, Any
import json

class CalculatorTools:
    """Real calculation tools for budget analysis and financial planning"""

    @staticmethod
    def calculate(expression: str) -> str:
        """
        Perform calculations for study abroad budget planning
        Supports basic math, currency conversion estimates, and budget analysis
        """
        try:
            # Clean the expression
            expression = expression.strip()

            # Check if it's a budget analysis request
            if any(keyword in expression.lower() for keyword in ['budget', 'cost', 'expense', 'total', 'monthly', 'annual']):
                return CalculatorTools._budget_analysis(expression)

            # Check if it's a currency conversion request
            if any(symbol in expression for symbol in ['$', '€', '£', '¥']) or 'usd' in expression.lower() or 'eur' in expression.lower():
                return CalculatorTools._currency_calculation(expression)

            # Basic mathematical calculation
            return CalculatorTools._basic_calculation(expression)

        except Exception as e:
            return f"❌ Calculation error: {str(e)}\nPlease check your expression and try again."

    @staticmethod
    def _basic_calculation(expression: str) -> str:
        """Perform basic mathematical calculations safely"""
        try:
            # Clean the expression for safety
            expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            expression = expression.replace('$', '').replace(',', '')

            if not expression:
                return "❌ Invalid mathematical expression"

            # Evaluate safely
            result = eval(expression)

            # Format the result
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 2)

            return f"""
🧮 Calculation: {expression}
✅ Result: {result:,}

💡 Financial Context:
If this is for study abroad planning, consider:
• Tuition fees vary by program and university
• Living costs depend on city and lifestyle  
• Include visa, travel, and emergency fund costs
• Research scholarships and financial aid options
            """.strip()

        except ZeroDivisionError:
            return "❌ Error: Division by zero"
        except Exception as e:
            return f"❌ Calculation error: {str(e)}"

    @staticmethod
    def _currency_calculation(expression: str) -> str:
        """Handle currency-related calculations"""

        # Approximate exchange rates (these would be updated with real API in production)
        exchange_rates = {
            'usd_to_eur': 0.85,
            'usd_to_gbp': 0.75,
            'usd_to_cad': 1.25,
            'usd_to_aud': 1.35,
            'usd_to_jpy': 110.0,
            'eur_to_usd': 1.18,
            'gbp_to_usd': 1.33,
        }

        # Extract numbers and currency symbols
        numbers = re.findall(r'[0-9,]+\.?[0-9]*', expression)

        if numbers:
            try:
                amount = float(numbers[0].replace(',', ''))

                return f"""
💱 Currency Calculation: {expression}
💰 Amount: {amount:,}

📊 Approximate Conversions (USD base):
• EUR (Euro): €{amount * exchange_rates['usd_to_eur']:,.2f}
• GBP (British Pound): £{amount * exchange_rates['usd_to_gbp']:,.2f}  
• CAD (Canadian Dollar): C${amount * exchange_rates['usd_to_cad']:,.2f}
• AUD (Australian Dollar): A${amount * exchange_rates['usd_to_aud']:,.2f}

⚠️ Note: These are approximate rates. Check current exchange rates for accurate conversions.
Use xe.com, google.com, or bank websites for real-time rates.

💡 Study Abroad Tip: Factor in exchange rate fluctuations when budgeting!
                """.strip()

            except ValueError:
                return "❌ Could not parse currency amount"

        return f"💱 Currency query: {expression}\n💡 Please specify amount and currencies for conversion"

    @staticmethod  
    def _budget_analysis(expression: str) -> str:
        """Analyze budget-related calculations"""

        # Extract numbers from the expression
        numbers = re.findall(r'[0-9,]+\.?[0-9]*', expression)

        if numbers:
            try:
                amounts = [float(num.replace(',', '')) for num in numbers]
                total = sum(amounts)

                budget_categories = [
                    "Tuition & Fees",
                    "Accommodation", 
                    "Living Expenses",
                    "Travel & Transport",
                    "Books & Supplies",
                    "Personal & Entertainment",
                    "Emergency Fund"
                ]

                # Create budget breakdown if multiple amounts
                breakdown = ""
                if len(amounts) > 1:
                    breakdown = "\n📊 Budget Breakdown:"
                    for i, amount in enumerate(amounts):
                        category = budget_categories[i] if i < len(budget_categories) else f"Item {i+1}"
                        breakdown += f"\n• {category}: ${amount:,.2f}"

                return f"""
💼 Budget Analysis: {expression}
💰 Total Amount: ${total:,.2f}
{breakdown}

📈 Financial Planning:
• Annual Total: ${total:,.2f}
• Monthly Average: ${total/12:,.2f}
• Weekly Average: ${total/52:,.2f}

💡 Study Abroad Budget Tips:
• Add 10-20% buffer for unexpected expenses
• Research local cost of living variations
• Consider seasonal price fluctuations
• Look into student discounts and deals
• Plan for currency exchange fees

⚠️ Remember to budget for:
✓ Visa application fees
✓ Health insurance requirements  
✓ Initial setup costs (deposits, etc.)
✓ Home visits during breaks
                """.strip()

            except ValueError:
                return f"❌ Could not parse numbers in: {expression}"

        return f"""
💼 Budget Planning Query: {expression}

📋 Study Abroad Budget Template:
• Tuition & Fees: $____
• Accommodation: $____  
• Food & Groceries: $____
• Transportation: $____
• Books & Supplies: $____
• Personal Expenses: $____
• Travel & Exploration: $____
• Emergency Fund: $____

💡 Use specific numbers for detailed budget analysis!
Example: "calculate 35000 + 12000 + 8000 annual budget"
        """.strip()
