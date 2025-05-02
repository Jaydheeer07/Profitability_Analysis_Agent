"""
LLM Service Module for Financial Insights Generation.

This module provides a service for generating financial insights and recommendations
using OpenAI's language models. It handles API interactions, error handling,
and response processing.
"""

import os
import json
import time
import logging
import hashlib
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# Import Pydantic for data validation
import openai
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Import centralized logger
from src.utils.logger import app_logger as logger

# Load environment variables
load_dotenv()

# Using centralized logger imported above

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Cache configuration
CACHE_TTL_HOURS = 24  # Time-to-live for cached responses in hours


class FinancialInsightRequest(BaseModel):
    """Model for financial insight request data."""
    company_name: str = Field(..., description="Name of the company")
    period: str = Field(..., description="Financial period (e.g., 'Q1 2025')")
    financial_data: Dict[str, Any] = Field(..., description="Financial data and metrics")
    
    @field_validator('financial_data')
    @classmethod
    def validate_financial_data(cls, v):
        """Validate that the financial data contains required fields."""
        required_fields = ['sections', 'metrics']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Financial data must contain '{field}'")
        return v


class FinancialInsight(BaseModel):
    """Model for a single financial insight."""
    type: str = Field(..., description="Type of insight (e.g., 'strength', 'warning', 'opportunity')")
    title: str = Field(..., description="Short title for the insight")
    description: str = Field(..., description="Detailed description of the insight")
    metrics: List[str] = Field(default_factory=list, description="List of metrics related to this insight")
    impact: str = Field(default="medium", description="Impact level (low, medium, high)")


class FinancialRecommendation(BaseModel):
    """Model for a single financial recommendation."""
    title: str = Field(..., description="Short title for the recommendation")
    description: str = Field(..., description="Detailed description of the recommendation")
    expected_impact: str = Field(default="medium", description="Expected impact level (low, medium, high)")
    implementation_difficulty: str = Field(default="medium", description="Implementation difficulty (easy, medium, hard)")
    timeframe: str = Field(default="medium-term", description="Timeframe for implementation (short-term, medium-term, long-term)")


class FinancialInsightResponse(BaseModel):
    """Model for the complete financial insight response."""
    insights: List[FinancialInsight] = Field(default_factory=list, description="List of financial insights")
    recommendations: List[FinancialRecommendation] = Field(default_factory=list, description="List of financial recommendations")
    summary: str = Field(..., description="Executive summary of the financial analysis")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when insights were generated")
    llm_model: str = Field(default=OPENAI_MODEL_NAME, description="LLM model used for generation")
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "insights": [],
                "recommendations": [],
                "summary": "Example summary",
                "generated_at": "2025-04-30T10:00:00",
                "llm_model": "gpt-4o-mini"
            }
        }
    }


class LLMServiceError(Exception):
    """Exception raised for errors in the LLM service."""
    pass


class LLMService:
    """Service for generating financial insights using OpenAI's language models."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self._cache = {}  # Simple in-memory cache
        self._client = None
        
        # Configure OpenAI client
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found in environment variables.")
            logger.info("Please set OPENAI_API_KEY in .env file to use LLM features.")
        else:
            logger.info(f"LLM Service initialized with API key: {OPENAI_API_KEY[:4]}...")
            # Initialize the OpenAI client
            try:
                self._client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        
        if OPENAI_BASE_URL:
            logger.info(f"Using custom OpenAI base URL: {OPENAI_BASE_URL}")
        else:
            logger.info("Using default OpenAI base URL")
        
        logger.info(f"LLM Service initialized with model: {OPENAI_MODEL_NAME}")
        logger.debug(f"Cache TTL set to {CACHE_TTL_HOURS} hours")
    
    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """
        Generate a cache key based on the request data.
        
        Args:
            request_data: Dictionary containing the request data.
            
        Returns:
            String hash to use as cache key.
        """
        # Create a deterministic string representation of the data
        data_str = json.dumps(request_data, sort_keys=True)
        # Generate a hash of the data
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry is still valid.
        
        Args:
            cache_entry: Dictionary containing the cache entry.
            
        Returns:
            Boolean indicating if the cache entry is still valid.
        """
        if 'timestamp' not in cache_entry:
            return False
        
        expiry_time = cache_entry['timestamp'] + timedelta(hours=CACHE_TTL_HOURS)
        return datetime.now() < expiry_time
    
    def _create_prompt(self, request: FinancialInsightRequest) -> str:
        """
        Create a prompt for the LLM based on the financial data.
        
        Args:
            request: FinancialInsightRequest object containing the request data.
            
        Returns:
            String prompt for the LLM.
        """
        # Extract key financial data
        financial_data = request.financial_data
        sections = financial_data.get('sections', {})
        metrics = financial_data.get('metrics', {})
        
        # Format metrics for the prompt
        metrics_text = "\n".join([
            f"- {key.replace('_', ' ').title()}: {value:.2%}" if isinstance(value, float) else f"- {key.replace('_', ' ').title()}: {value}"
            for key, value in metrics.items()
        ])
        
        # Extract top expenses if available
        top_expenses = []
        if 'operatingExpenses' in sections and 'accounts' in sections['operatingExpenses']:
            expenses = sections['operatingExpenses']['accounts']
            if expenses:
                # Sort expenses by absolute value (descending)
                sorted_expenses = sorted(expenses, key=lambda x: abs(x.get('value', 0)), reverse=True)
                # Take top 5 expenses
                top_expenses = sorted_expenses[:5]
        
        top_expenses_text = ""
        if top_expenses:
            expense_items = []
            total_expenses = abs(sections.get('operatingExpenses', {}).get('total', 1))  # Avoid division by zero
            
            for expense in top_expenses:
                name = expense.get('name', 'Unknown')
                value = expense.get('value', 0)
                percentage = abs(value) / total_expenses * 100 if total_expenses else 0
                expense_items.append(f"- {name}: ${abs(value):.2f} ({percentage:.1f}% of total expenses)")
            
            top_expenses_text = "Top Expenses:\n" + "\n".join(expense_items)
        
        # Create the prompt
        prompt = f"""
You are a financial analyst specializing in profit and loss analysis. Analyze the following financial data for {request.company_name} for the period {request.period} and provide insights and recommendations.

Financial Metrics:
{metrics_text}

{top_expenses_text}

Based on this financial data, please provide:
1. 3-5 key insights about the financial performance (strengths, weaknesses, opportunities)
2. 3-4 actionable recommendations to improve financial performance
3. A brief executive summary (2-3 sentences)

For each insight, include:
- A clear title
- A detailed explanation
- The impact level (low, medium, high)
- Related metrics

For each recommendation, include:
- A clear action item
- A detailed explanation of the expected benefit
- Implementation difficulty (easy, medium, hard)
- Expected timeframe (short-term, medium-term, long-term)

Format your response as JSON with the following structure:
{{
  "insights": [
    {{
      "type": "strength|warning|opportunity",
      "title": "Short title",
      "description": "Detailed description",
      "metrics": ["related_metric1", "related_metric2"],
      "impact": "low|medium|high"
    }}
  ],
  "recommendations": [
    {{
      "title": "Action item",
      "description": "Detailed explanation",
      "expected_impact": "low|medium|high",
      "implementation_difficulty": "easy|medium|hard",
      "timeframe": "short-term|medium-term|long-term"
    }}
  ],
  "summary": "Executive summary of the financial analysis"
}}
"""
        return prompt
    
    def _call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call the OpenAI API with the given prompt.
        
        Args:
            prompt: String prompt for the LLM.
            
        Returns:
            Dictionary containing the API response.
            
        Raises:
            LLMServiceError: If there's an error calling the API.
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        # Log API request details (without sensitive data)
        logger.info(f"Making OpenAI API request with model: {OPENAI_MODEL_NAME}")
        logger.debug(f"API base URL: {OPENAI_BASE_URL}")
        logger.debug(f"API key configured: {bool(OPENAI_API_KEY)}")
        
        for attempt in range(max_retries):
            try:
                # Check if API key is configured
                if not OPENAI_API_KEY:
                    raise LLMServiceError("OpenAI API key is not configured. Please set OPENAI_API_KEY in .env file.")
                
                # Check if client is initialized
                if self._client is None:
                    logger.debug("Initializing OpenAI client on demand")
                    self._client = openai.OpenAI(
                        api_key=OPENAI_API_KEY,
                        base_url=OPENAI_BASE_URL
                    )
                
                # Make API request
                logger.debug(f"Attempt {attempt+1}/{max_retries} to call OpenAI API")
                response = self._client.chat.completions.create(
                    model=OPENAI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a financial analyst specializing in profit and loss analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,  # Lower temperature for more consistent, factual responses
                    response_format={"type": "json_object"},
                    max_tokens=2000
                )
                
                # Extract and parse the response
                content = response.choices[0].message.content
                logger.info(f"Successfully received response from OpenAI API")
                
                try:
                    parsed_content = json.loads(content)
                    logger.debug(f"Successfully parsed JSON response")
                    return parsed_content
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
                    logger.debug(f"Response content: {content[:100]}...")
                    raise LLMServiceError(f"Failed to parse OpenAI response as JSON: {str(e)}")
                
            except openai.APIConnectionError as e:
                logger.warning(f"OpenAI API connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to OpenAI API after {max_retries} attempts: {str(e)}")
                    raise LLMServiceError(f"Failed to connect to OpenAI API after {max_retries} attempts: {str(e)}")
            
            except openai.RateLimitError as e:
                logger.warning(f"OpenAI API rate limit error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt) * 2)  # Longer backoff for rate limits
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts: {str(e)}")
                    raise LLMServiceError(f"Rate limit exceeded after {max_retries} attempts: {str(e)}")
            
            except openai.APIError as e:
                logger.warning(f"OpenAI API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"OpenAI API error after {max_retries} attempts: {str(e)}")
                    raise LLMServiceError(f"OpenAI API error after {max_retries} attempts: {str(e)}")
            
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI API: {str(e)}")
                raise LLMServiceError(f"Unexpected error calling OpenAI API: {str(e)}")
    
    def generate_insights(self, request_data: Dict[str, Any]) -> FinancialInsightResponse:
        """
        Generate financial insights using LLM.
        
        Args:
            request_data: Dictionary containing the request data.
            
        Returns:
            FinancialInsightResponse object containing the insights and recommendations.
            
        Raises:
            LLMServiceError: If there's an error generating insights.
        """
        try:
            # Log the start of insight generation
            logger.info(f"Starting financial insight generation")
            logger.debug(f"Request data keys: {list(request_data.keys())}")
            
            # Validate request data
            try:
                request = FinancialInsightRequest(**request_data)
                logger.debug(f"Request validation successful for company: {request.company_name}")
            except Exception as e:
                logger.error(f"Request validation failed: {str(e)}")
                raise LLMServiceError(f"Invalid request data: {str(e)}")
            
            # Check cache first
            cache_key = self._generate_cache_key(request_data)
            logger.debug(f"Generated cache key: {cache_key}")
            
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
                logger.info("Using cached insights (cache hit)")
                cached_response = FinancialInsightResponse(**self._cache[cache_key]['response'])
                logger.debug(f"Returning cached response with {len(cached_response.insights)} insights")
                return cached_response
            else:
                logger.debug("Cache miss, generating new insights")
            
            # Create prompt
            prompt = self._create_prompt(request)
            logger.debug(f"Created prompt with length: {len(prompt)}")
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API for {request.company_name}, period {request.period}")
            llm_response = self._call_openai_api(prompt)
            
            # Validate and process response
            try:
                logger.debug(f"Validating LLM response")
                response = FinancialInsightResponse(**llm_response)
                logger.info(f"Generated {len(response.insights)} insights and {len(response.recommendations)} recommendations")
            except Exception as e:
                logger.error(f"Failed to validate LLM response: {str(e)}")
                logger.debug(f"LLM response keys: {list(llm_response.keys()) if isinstance(llm_response, dict) else 'Not a dict'}")
                raise LLMServiceError(f"Invalid LLM response format: {str(e)}")
            
            # Cache the response
            try:
                self._cache[cache_key] = {
                    'response': response.model_dump(),
                    'timestamp': datetime.now()
                }
                logger.debug(f"Cached response with key: {cache_key}")
            except Exception as e:
                logger.warning(f"Failed to cache response: {str(e)}")
            
            return response
            
        except LLMServiceError as e:
            # Re-raise LLMServiceError without wrapping
            logger.error(f"LLM service error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating insights: {str(e)}")
            raise LLMServiceError(f"Failed to generate financial insights: {str(e)}")
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache = {}
        logger.info("Cache cleared")
    
    def refresh_cache_entry(self, request_data: Dict[str, Any]) -> None:
        """
        Remove a specific entry from the cache to force refresh.
        
        Args:
            request_data: Dictionary containing the request data.
        """
        cache_key = self._generate_cache_key(request_data)
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"Cache entry removed for refresh")


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """
    Get the singleton instance of the LLM service.
    
    Returns:
        LLMService instance.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
