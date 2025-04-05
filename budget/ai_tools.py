"""
AI integration tools for the budget application using Claude and OpenAI APIs.
"""
import json
import requests
import time
from typing import Dict, List, Any, Optional, Union

from configs.config import AI_API
from .logger import logger

class AITools:
    """
    Tools for integrating with AI APIs (Claude, OpenAI) for financial insights and assistance.
    """
    
    def __init__(self):
        """Initialize the AI tools with the configured provider."""
        self.provider = AI_API['provider']
        self.claude_config = AI_API['claude']
        self.openai_config = AI_API['openai']
        self.local_config = AI_API['local']
        self.capabilities = AI_API['capabilities']
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self):
        """Validate the AI API configuration."""
        if self.provider == 'claude' and self.claude_config['enabled']:
            if not self.claude_config['api_key']:
                logger.warning("Claude API is enabled but no API key is provided")
                
        elif self.provider == 'openai' and self.openai_config['enabled']:
            if not self.openai_config['api_key']:
                logger.warning("OpenAI API is enabled but no API key is provided")
                
        elif self.provider == 'local' and self.local_config['enabled']:
            if not self.local_config['api_url']:
                logger.warning("Local model is enabled but no API URL is provided")
                
        elif self.provider != 'none':
            logger.warning(f"Unknown AI provider: {self.provider}")
            
    def is_enabled(self) -> bool:
        """Check if AI integration is enabled and properly configured."""
        if self.provider == 'claude':
            return self.claude_config['enabled'] and bool(self.claude_config['api_key'])
        elif self.provider == 'openai':
            return self.openai_config['enabled'] and bool(self.openai_config['api_key'])
        elif self.provider == 'local':
            return self.local_config['enabled'] and bool(self.local_config['api_url'])
        return False
        
    def switch_provider(self, provider: str) -> bool:
        """
        Switch to a different AI provider.
        
        Args:
            provider (str): The provider to switch to ('claude', 'openai', 'local', or 'none')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if provider not in ['claude', 'openai', 'local', 'none']:
            logger.error(f"Unknown AI provider: {provider}")
            return False
            
        self.provider = provider
        logger.info(f"Switched AI provider to {provider}")
        return True
        
    def categorize_transaction(self, description: str, amount: float, date: str) -> Dict[str, Any]:
        """
        Use AI to categorize a transaction based on its description, amount, and date.
        
        Args:
            description (str): Transaction description
            amount (float): Transaction amount
            date (str): Transaction date
            
        Returns:
            dict: Category prediction with confidence score
        """
        if not self.is_enabled() or not self.capabilities['transaction_categorization']:
            return {'category': 'uncategorized', 'confidence': 0.0}
            
        prompt = f"""
        Analyze this financial transaction and categorize it into exactly one of these categories:
        - income (salary, deposits, refunds)
        - housing (mortgage, rent, property taxes)
        - utilities (electric, water, gas, internet, phone)
        - groceries (supermarkets, food stores)
        - dining (restaurants, cafes, food delivery)
        - transportation (gas, public transit, car services, parking)
        - healthcare (medical bills, pharmacy, insurance)
        - entertainment (movies, streaming services, events)
        - shopping (retail, online purchases, clothing)
        - personal (haircuts, gym, personal care)
        - education (tuition, books, courses)
        - travel (flights, hotels, vacation expenses)
        - savings (transfers to savings, investments)
        - debt (credit card payments, loan payments)
        - miscellaneous (anything that doesn't fit above)
        
        Transaction details:
        Description: {description}
        Amount: ${amount:.2f}
        Date: {date}
        
        Respond in JSON format with only 'category' and 'confidence' keys.
        Example: {{"category": "groceries", "confidence": 0.85}}
        """
        
        try:
            response = self._get_ai_response(prompt, json_response=True)
            if response and 'category' in response and 'confidence' in response:
                return response
            else:
                logger.warning(f"Invalid AI categorization response: {response}")
                return {'category': 'uncategorized', 'confidence': 0.0}
        except Exception as e:
            logger.error(f"Error during AI categorization: {str(e)}")
            return {'category': 'uncategorized', 'confidence': 0.0}
            
    def generate_insights(self, transactions_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate financial insights based on transaction data.
        
        Args:
            transactions_summary (dict): Summary of transaction data
            
        Returns:
            dict: Financial insights and recommendations
        """
        if not self.is_enabled() or not self.capabilities['spending_insights']:
            return {'insights': []}
            
        # Format the transaction summary data
        summary_str = json.dumps(transactions_summary, indent=2)
        
        prompt = f"""
        Analyze this financial transaction summary data and provide 3-5 key insights about spending patterns,
        unusual expenses, potential savings opportunities, and financial trends.
        
        Transaction Summary:
        {summary_str}
        
        Respond in JSON format with an 'insights' array containing objects with 'title' and 'description' fields.
        Example:
        {{
          "insights": [
            {{
              "title": "Dining expenses increased by 25%",
              "description": "Your spending on restaurants and takeout has increased significantly compared to previous months."
            }},
            ...
          ]
        }}
        """
        
        try:
            response = self._get_ai_response(prompt, json_response=True)
            if response and 'insights' in response:
                return response
            else:
                logger.warning(f"Invalid AI insights response: {response}")
                return {'insights': []}
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return {'insights': []}
            
    def generate_budget_recommendations(self, income: float, expenses: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate budget recommendations based on income and expense data.
        
        Args:
            income (float): Total income
            expenses (dict): Expenses by category
            
        Returns:
            dict: Budget recommendations
        """
        if not self.is_enabled() or not self.capabilities['budget_recommendations']:
            return {'recommendations': []}
            
        # Format the expense data
        expenses_str = json.dumps(expenses, indent=2)
        
        prompt = f"""
        Create personalized budget recommendations based on the following financial data.
        Use the 50/30/20 rule (50% needs, 30% wants, 20% savings) as a general guideline.
        
        Monthly Income: ${income:.2f}
        
        Current Monthly Expenses by Category:
        {expenses_str}
        
        Respond in JSON format with a 'recommendations' array containing objects with 'category', 'current_amount',
        'recommended_amount', and 'explanation' fields.
        Example:
        {{
          "recommendations": [
            {{
              "category": "dining",
              "current_amount": 350.00,
              "recommended_amount": 250.00,
              "explanation": "Reducing dining out expenses by $100 would bring this category within the recommended range."
            }},
            ...
          ]
        }}
        """
        
        try:
            response = self._get_ai_response(prompt, json_response=True)
            if response and 'recommendations' in response:
                return response
            else:
                logger.warning(f"Invalid AI budget recommendations response: {response}")
                return {'recommendations': []}
        except Exception as e:
            logger.error(f"Error generating AI budget recommendations: {str(e)}")
            return {'recommendations': []}
            
    def financial_assistant(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Financial assistant that can answer questions about budgeting and financial data.
        
        Args:
            user_query (str): User's question
            context (dict, optional): Optional context data
            
        Returns:
            str: Assistant's response
        """
        if not self.is_enabled() or not self.capabilities['financial_assistant']:
            return "AI financial assistant is not enabled."
            
        context_str = ""
        if context:
            context_str = f"Context:\n{json.dumps(context, indent=2)}\n\n"
            
        prompt = f"""
        You are a helpful financial assistant. Answer the following question about budgeting, finances, or the user's
        financial data provided in the context.
        
        {context_str}
        
        User question: {user_query}
        
        Provide a clear, concise, and helpful response. If you don't have enough information to answer accurately,
        say so and suggest what additional information would be helpful.
        """
        
        try:
            response = self._get_ai_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Error in financial assistant: {str(e)}")
            return "Sorry, I was unable to process your question at this time."
            
    def _get_ai_response(self, prompt: str, json_response: bool = False) -> Union[str, Dict]:
        """
        Get a response from the configured AI provider.
        
        Args:
            prompt (str): The prompt to send to the AI
            json_response (bool): Whether to parse the response as JSON
            
        Returns:
            Union[str, dict]: The AI's response as string or parsed JSON
        """
        if self.provider == 'claude':
            return self._get_claude_response(prompt, json_response)
        elif self.provider == 'openai':
            return self._get_openai_response(prompt, json_response)
        elif self.provider == 'local':
            return self._get_local_response(prompt, json_response)
        else:
            return "AI integration is not enabled."
            
    def _get_claude_response(self, prompt: str, json_response: bool = False) -> Union[str, Dict]:
        """Get a response from Claude API."""
        if not self.claude_config['api_key']:
            return "Claude API key is not configured."
            
        headers = {
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01',
            'x-api-key': self.claude_config['api_key']
        }
        
        data = {
            'model': self.claude_config['model'],
            'max_tokens': self.claude_config['max_tokens'],
            'temperature': self.claude_config['temperature'],
            'system': "You are a helpful financial assistant that provides accurate and concise information about personal finance and budgeting.",
            'messages': [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=self.claude_config['timeout']
            )
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data['content'][0]['text']
            
            # Extract JSON if requested
            if json_response:
                return self._extract_json(response_text)
            return response_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Claude API error: {str(e)}")
            raise
            
    def _get_openai_response(self, prompt: str, json_response: bool = False) -> Union[str, Dict]:
        """Get a response from OpenAI API."""
        if not self.openai_config['api_key']:
            return "OpenAI API key is not configured."
            
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.openai_config['api_key']}"
        }
        
        response_format = {"type": "json_object"} if json_response else None
        
        data = {
            'model': self.openai_config['model'],
            'messages': [
                {"role": "system", "content": "You are a helpful financial assistant that provides accurate and concise information about personal finance and budgeting."},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': self.openai_config['max_tokens'],
            'temperature': self.openai_config['temperature']
        }
        
        if response_format:
            data['response_format'] = response_format
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=self.openai_config['timeout']
            )
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data['choices'][0]['message']['content']
            
            # Extract JSON if requested and not using response_format
            if json_response and not response_format:
                return self._extract_json(response_text)
            elif json_response:
                return json.loads(response_text)
            return response_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
            
    def _get_local_response(self, prompt: str, json_response: bool = False) -> Union[str, Dict]:
        """Get a response from a local API (e.g., Ollama)."""
        if not self.local_config['api_url']:
            return "Local model API URL is not configured."
            
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.local_config['model'],
            'prompt': prompt,
            'stream': False
        }
        
        try:
            response = requests.post(
                self.local_config['api_url'],
                headers=headers,
                json=data,
                timeout=self.local_config['timeout']
            )
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data.get('response', '')
            
            # Extract JSON if requested
            if json_response:
                return self._extract_json(response_text)
            return response_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Local API error: {str(e)}")
            raise
            
    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from a text response.
        
        Args:
            text (str): Text that may contain JSON
            
        Returns:
            dict: Extracted JSON or empty dict if not found
        """
        try:
            # Try to parse the whole text as JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON using regex
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```|({[\s\S]*})', text)
            
            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse extracted JSON: {json_str}")
                    
            # Fallback: try to find any JSON-like structure
            try:
                import ast
                for line in text.split('\n'):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        # Replace single quotes with double quotes for JSON compatibility
                        line = line.replace("'", '"')
                        return json.loads(line)
            except (json.JSONDecodeError, SyntaxError, ValueError):
                pass
                
            logger.warning(f"Could not extract JSON from response: {text[:100]}...")
            return {}