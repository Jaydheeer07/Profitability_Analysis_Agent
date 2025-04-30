"""
Helper module for financial insights generation.

This module provides utility functions for preparing financial data
for the LLM service and processing the responses.
"""

import json
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.utils.llm_service import get_llm_service, LLMServiceError, FinancialInsightResponse
from src.utils.logger import app_logger as logger

def prepare_financial_data_for_llm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare financial data for the LLM service.
    
    Args:
        data: The profit and loss data dictionary.
        
    Returns:
        Dictionary containing the prepared request data for the LLM service.
    """
    logger.info("Preparing financial data for LLM analysis")
    
    # Extract company name and period
    company_name = data.get('companyName', 'Unknown Company')
    period = data.get('period', 'Current Period')
    logger.debug(f"Company: {company_name}, Period: {period}")
    
    # Check for required data
    if 'sections' not in data:
        logger.warning("Missing 'sections' in financial data")
    if 'metrics' not in data:
        logger.warning("Missing 'metrics' in financial data")
    
    # Create the request data
    request_data = {
        "company_name": company_name,
        "period": period,
        "financial_data": {
            "sections": data.get('sections', {}),
            "metrics": data.get('metrics', {})
        }
    }
    
    logger.debug(f"Prepared request data with keys: {list(request_data.keys())}")
    logger.debug(f"Financial data sections: {list(request_data['financial_data']['sections'].keys())}")
    
    return request_data

def generate_llm_insights(data: Dict[str, Any], use_llm: bool = True) -> Optional[FinancialInsightResponse]:
    """
    Generate insights using the LLM service.
    
    Args:
        data: The profit and loss data dictionary.
        use_llm: Whether to use the LLM service or not.
        
    Returns:
        FinancialInsightResponse object or None if there's an error.
    """
    logger.info("Starting LLM insights generation process")
    
    if not use_llm:
        logger.info("LLM insights generation skipped (use_llm=False)")
        return None
    
    # Check if data is valid
    if not data:
        logger.error("Cannot generate insights: empty financial data")
        return None
    
    if not isinstance(data, dict):
        logger.error(f"Invalid data type: {type(data)}. Expected dictionary.")
        return None
    
    try:
        # Log data structure (without sensitive values)
        logger.debug(f"Financial data contains keys: {list(data.keys())}")
        if 'companyName' in data:
            logger.info(f"Generating insights for company: {data['companyName']}")
        if 'period' in data:
            logger.info(f"Period: {data['period']}")
        
        # Prepare data for LLM
        logger.debug("Preparing request data for LLM service")
        request_data = prepare_financial_data_for_llm(data)
        
        # Get LLM service and generate insights
        logger.debug("Getting LLM service instance")
        llm_service = get_llm_service()
        
        logger.info("Calling LLM service to generate insights")
        start_time = datetime.now()
        response = llm_service.generate_insights(request_data)
        end_time = datetime.now()
        
        # Log success and timing information
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Successfully generated insights in {duration:.2f} seconds")
        logger.info(f"Generated {len(response.insights)} insights and {len(response.recommendations)} recommendations")
        
        # Log insight types (for debugging)
        insight_types = [insight.type for insight in response.insights]
        logger.debug(f"Insight types: {insight_types}")
        
        return response
        
    except LLMServiceError as e:
        logger.error(f"Error generating LLM insights: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in generate_llm_insights: {str(e)}")
        logger.debug(f"Exception details: {traceback.format_exc()}")
        return None

def format_insight_for_display(insight: Dict[str, Any]) -> str:
    """
    Format an insight for display in the dashboard.
    
    Args:
        insight: Dictionary containing the insight data.
        
    Returns:
        Formatted string for display.
    """
    logger.debug(f"Formatting insight for display: {insight.get('title', 'Untitled')}")
    
    # Add emoji based on insight type
    insight_type = insight.get('type', 'info').lower()
    
    if insight_type == "strength":
        emoji = "✅"
    elif insight_type == "warning":
        emoji = "⚠️"
    elif insight_type == "opportunity":
        emoji = "💡"
    else:
        emoji = "ℹ️"
        logger.debug(f"Unknown insight type: {insight_type}, using default emoji")
    
    # Format the insight
    title = insight.get('title', 'Untitled Insight')
    description = insight.get('description', 'No description provided')
    formatted = f"{emoji} **{title}**: {description}"
    
    # Add impact level if available
    impact = insight.get('impact')
    if impact:
        impact_emoji = "🔴" if impact == "high" else "🟠" if impact == "medium" else "🟢"
        formatted += f"\n   *Impact: {impact_emoji} {impact.title()}*"
    
    logger.debug(f"Formatted insight with emoji: {emoji}")
    return formatted

def format_recommendation_for_display(recommendation: Dict[str, Any]) -> str:
    """
    Format a recommendation for display in the dashboard.
    
    Args:
        recommendation: Dictionary containing the recommendation data.
        
    Returns:
        Formatted string for display.
    """
    logger.debug(f"Formatting recommendation for display: {recommendation.get('title', 'Untitled')}")
    
    # Add emoji based on difficulty
    difficulty = recommendation.get('implementation_difficulty', 'medium').lower()
    
    if difficulty == "easy":
        emoji = "🟢"
    elif difficulty == "medium":
        emoji = "🟠"
    elif difficulty == "hard":
        emoji = "🔴"
    else:
        emoji = "ℹ️"
        logger.debug(f"Unknown difficulty level: {difficulty}, using default emoji")
    
    # Format the recommendation
    title = recommendation.get('title', 'Untitled Recommendation')
    description = recommendation.get('description', 'No description provided')
    formatted = f"{emoji} **{title}**: {description}"
    
    # Add impact and timeframe
    impact = recommendation.get('expected_impact', 'medium')
    timeframe = recommendation.get('timeframe', 'medium-term')
    
    # Format metadata line
    metadata = []
    if impact:
        impact_emoji = "🔴" if impact == "high" else "🟠" if impact == "medium" else "🟢"
        metadata.append(f"Impact: {impact_emoji} {impact.title()}")
    if timeframe:
        metadata.append(f"Timeframe: {timeframe.title()}")
    if difficulty:
        metadata.append(f"Difficulty: {difficulty.title()}")
    
    formatted += f"\n   *{' | '.join(metadata)}*"
    
    logger.debug(f"Formatted recommendation with emoji: {emoji}")
    return formatted
