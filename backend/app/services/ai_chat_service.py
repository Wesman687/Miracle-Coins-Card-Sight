from typing import Dict, Any, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from app.types import CoinBase, AIEvaluationRequest, AIEvaluationResponse
from app.repositories_typed import CoinRepository, SpotPriceRepository
from app.services.ai_evaluation_service import AIEvaluationService
from app.services.search_cache_service import SearchCacheService
from app.services.image_analysis_service import ImageAnalysisService
import logging
import json
import httpx
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class AIChatService:
    def __init__(self, db: Session):
        self.db = db
        self.coin_repo = CoinRepository(db)
        self.spot_repo = SpotPriceRepository(db)
        self.ai_evaluation_service = AIEvaluationService(db)
        self.cache_service = SearchCacheService(db)
        self.image_analysis_service = ImageAnalysisService(db)
    
    async def search_coin(
        self, 
        query: str, 
        preset: str = 'quick_response',
        context: List[Dict[str, Any]] = None,
        image_url: str = None,
        image_analysis: bool = False
    ) -> Dict[str, Any]:
        """Main AI chat search function with preset handling"""
        
        start_time = datetime.now()
        
        try:
            # Handle image analysis if image is provided
            if image_url and image_analysis:
                result = await self.image_analysis_service.analyze_coin_image(
                    image_url, preset, query
                )
                
                search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    'response': result['response'],
                    'confidence_score': result['confidence_score'],
                    'pricing': result.get('pricing'),
                    'cached': False,
                    'search_time_ms': search_time_ms,
                    'image_analysis': True
                }
            
            # Check cache first for quick responses
            if preset in ['quick_response', 'pricing_only']:
                cached_result = await self.cache_service.get_cached_search(query, preset)
                if cached_result:
                    logger.info(f"Returning cached result for query: {query}")
                    return {
                        'response': cached_result['response'],
                        'confidence_score': cached_result['confidence_score'],
                        'pricing': cached_result.get('pricing'),
                        'cached': True,
                        'search_time_ms': (datetime.now() - start_time).total_seconds() * 1000
                    }
            
            # Process based on preset
            if preset == 'quick_response':
                result = await self._quick_response_search(query, context)
            elif preset == 'in_depth_analysis':
                result = await self._in_depth_analysis_search(query, context)
            elif preset == 'descriptions':
                result = await self._descriptions_search(query, context)
            elif preset == 'year_mintage':
                result = await self._year_mintage_search(query, context)
            elif preset == 'pricing_only':
                result = await self._pricing_only_search(query, context)
            elif preset == 'visual_identification':
                result = await self._visual_identification_search(query, context)
            elif preset == 'grade_assessment':
                result = await self._grade_assessment_search(query, context)
            else:
                result = await self._quick_response_search(query, context)
            
            # Cache the result for future quick responses
            if preset in ['quick_response', 'pricing_only']:
                await self.cache_service.cache_search_result(
                    query, preset, result['response'], 
                    result['confidence_score'], result.get('pricing')
                )
            
            search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'response': result['response'],
                'confidence_score': result['confidence_score'],
                'pricing': result.get('pricing'),
                'cached': False,
                'search_time_ms': search_time_ms
            }
            
        except Exception as e:
            logger.error(f"AI chat search error: {str(e)}")
            return {
                'response': 'I encountered an error while analyzing your coin. Please try again with more specific details.',
                'confidence_score': 0.0,
                'pricing': None,
                'cached': False,
                'search_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
    
    async def _quick_response_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fast pricing response for auctions"""
        
        # Extract coin information from query
        coin_data = await self._extract_coin_data(query)
        
        # Get current spot price
        spot_price = self.spot_repo.get_latest("silver")
        current_spot = spot_price.price if spot_price else Decimal('25.00')
        
        # Quick pricing calculation
        suggested_price = await self._calculate_quick_price(coin_data, current_spot)
        
        # Generate quick response
        response = await self._generate_quick_response(coin_data, suggested_price, current_spot)
        
        return {
            'response': response,
            'confidence_score': 0.75,  # Lower confidence for quick responses
            'pricing': {
                'suggested_price': float(suggested_price),
                'melt_value': float(coin_data.get('melt_value', 0)),
                'confidence_score': 0.75,
                'category': coin_data.get('category', 'standard')
            }
        }
    
    async def _in_depth_analysis_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Detailed analysis with scam detection"""
        
        # Extract coin information
        coin_data = await self._extract_coin_data(query)
        
        # Use existing AI evaluation service
        try:
            evaluation_request = AIEvaluationRequest(
                coin_id=None,  # For chat searches, we don't have a coin ID
                coin_data=CoinBase(**coin_data)
            )
            
            evaluation_result = self.ai_evaluation_service.evaluate_coin(evaluation_request)
        except Exception as e:
            logger.error(f"Error creating evaluation request: {e}")
            logger.error(f"Coin data: {coin_data}")
            return {
                'response': "I encountered an error while analyzing your coin. Please try again with more specific details.",
                'confidence_score': 0.0,
                'pricing': None
            }
        
        # Check if evaluation failed
        if not evaluation_result:
            logger.error("AI evaluation service returned None")
            return {
                'response': "I encountered an error while analyzing your coin. Please try again with more specific details.",
                'confidence_score': 0.0,
                'pricing': None
            }
        
        # Generate detailed response
        response = await self._generate_detailed_response(coin_data, evaluation_result)
        
        return {
            'response': response,
            'confidence_score': evaluation_result.confidence_score,
            'pricing': {
                'suggested_price': float(evaluation_result.suggested_price),
                'melt_value': float(evaluation_result.melt_value),
                'confidence_score': evaluation_result.confidence_score,
                'category': evaluation_result.category
            }
        }
    
    async def _descriptions_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate coin descriptions"""
        
        coin_data = await self._extract_coin_data(query)
        
        # Generate description
        description = await self._generate_coin_description(coin_data)
        
        return {
            'response': description,
            'confidence_score': 0.85,
            'pricing': None
        }
    
    async def _year_mintage_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Historical data and rarity information"""
        
        coin_data = await self._extract_coin_data(query)
        
        # Get historical data
        historical_info = await self._get_historical_data(coin_data)
        
        return {
            'response': historical_info,
            'confidence_score': 0.80,
            'pricing': None
        }
    
    async def _pricing_only_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Just the price, nothing else"""
        
        coin_data = await self._extract_coin_data(query)
        
        # Get current spot price
        spot_price = self.spot_repo.get_latest("silver")
        current_spot = spot_price.price if spot_price else Decimal('25.00')
        
        # Calculate price
        suggested_price = await self._calculate_quick_price(coin_data, current_spot)
        
        # Simple response
        response = f"**${suggested_price:.2f}**"
        
        return {
            'response': response,
            'confidence_score': 0.70,
            'pricing': {
                'suggested_price': float(suggested_price),
                'melt_value': float(coin_data.get('melt_value', 0)),
                'confidence_score': 0.70,
                'category': coin_data.get('category', 'standard')
            }
        }
    
    async def _extract_coin_data(self, query: str) -> Dict[str, Any]:
        """Extract coin information from natural language query"""
        
        # This would typically use NLP or AI to extract structured data
        # For now, we'll use simple pattern matching
        
        coin_data = {
            'title': query,
            'year': None,
            'denomination': None,
            'grade': None,
            'is_silver': False,
            'silver_content_oz': Decimal('0.0'),
            'paid_price': Decimal('0.0'),
            'category': 'standard',
            'price_strategy': 'spot_multiplier',
            'price_multiplier': Decimal('1.300'),
            'base_from_entry': True,
            'override_price': False,
            'quantity': 1,
            'status': 'active'
        }
        
        # Extract year
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', query)
        if year_match:
            coin_data['year'] = int(year_match.group())
        
        # Extract grade
        grade_patterns = [
            r'\b(MS|AU|XF|VF|F|VG|G|AG|FR|PO)\d*\b',
            r'\b(Uncirculated|About Uncirculated|Extremely Fine|Very Fine|Fine|Very Good|Good|About Good|Fair|Poor)\b'
        ]
        
        for pattern in grade_patterns:
            grade_match = re.search(pattern, query, re.IGNORECASE)
            if grade_match:
                coin_data['grade'] = grade_match.group().upper()
                break
        
        # Determine if silver
        silver_keywords = ['silver', 'morgan', 'peace', 'kennedy', 'roosevelt', 'mercury', 'barber', 'walking liberty']
        if any(keyword in query.lower() for keyword in silver_keywords):
            coin_data['is_silver'] = True
            # Set appropriate silver content based on denomination
            if 'quarter' in query.lower():
                coin_data['silver_content_oz'] = Decimal('0.1808')
            elif 'dime' in query.lower():
                coin_data['silver_content_oz'] = Decimal('0.0723')
            elif 'half' in query.lower():
                coin_data['silver_content_oz'] = Decimal('0.3617')
            else:
                coin_data['silver_content_oz'] = Decimal('0.7734')  # Default for silver dollars
        
        # Extract denomination
        denomination_patterns = [
            r'\b(dollar|half dollar|quarter|dime|nickel|penny|cent)\b',
            r'\b(\$1|\$0\.50|\$0\.25|\$0\.10|\$0\.05|\$0\.01)\b'
        ]
        
        for pattern in denomination_patterns:
            denom_match = re.search(pattern, query, re.IGNORECASE)
            if denom_match:
                coin_data['denomination'] = denom_match.group()
                break
        
        return coin_data
    
    async def _calculate_quick_price(self, coin_data: Dict[str, Any], current_spot: Decimal) -> Decimal:
        """Quick price calculation for fast responses"""
        
        if coin_data.get('is_silver') and coin_data.get('silver_content_oz'):
            melt_value = coin_data['silver_content_oz'] * current_spot
            
            # Apply quick multipliers based on grade
            grade_multiplier = 1.0
            if coin_data.get('grade'):
                grade = coin_data['grade'].upper()
                if 'MS' in grade:
                    grade_multiplier = 1.5
                elif 'AU' in grade:
                    grade_multiplier = 1.3
                elif 'XF' in grade:
                    grade_multiplier = 1.2
                else:
                    grade_multiplier = 1.1
            
            # Apply rarity multiplier
            rarity_multiplier = 1.0
            if coin_data.get('year'):
                year = coin_data['year']
                if year < 1900:
                    rarity_multiplier = 1.3
                elif year < 1950:
                    rarity_multiplier = 1.2
                else:
                    rarity_multiplier = 1.1
            
            suggested_price = melt_value * grade_multiplier * rarity_multiplier
            
            # Ensure minimum premium
            min_premium = melt_value * Decimal('1.2')
            suggested_price = max(suggested_price, min_premium)
            
            coin_data['melt_value'] = melt_value
            
        else:
            # Non-silver coin pricing
            suggested_price = Decimal('50.00')  # Default price
        
        return suggested_price.quantize(Decimal('1.00'))
    
    async def _generate_quick_response(self, coin_data: Dict[str, Any], suggested_price: Decimal, current_spot: Decimal) -> str:
        """Generate quick response for auctions"""
        
        response_parts = []
        
        # Price
        response_parts.append(f"**Quick Price: ${suggested_price:.2f}**")
        
        # Melt value if silver
        if coin_data.get('is_silver') and coin_data.get('melt_value'):
            melt_value = coin_data['melt_value']
            response_parts.append(f"Melt Value: ${melt_value:.2f} (Silver Spot: ${current_spot:.2f})")
        
        # Grade info
        if coin_data.get('grade'):
            response_parts.append(f"Grade: {coin_data['grade']}")
        
        # Quick market note
        response_parts.append("💡 *This is a quick estimate. For detailed analysis, use 'In-Depth Analysis' preset.*")
        
        return "\n\n".join(response_parts)
    
    async def _generate_detailed_response(self, coin_data: Dict[str, Any], evaluation_result: AIEvaluationResponse) -> str:
        """Generate detailed response with analysis"""
        
        response_parts = []
        
        # Header
        response_parts.append(f"## Detailed Analysis for {coin_data.get('title', 'Coin')}")
        
        # Pricing
        response_parts.append(f"**Suggested Price: ${evaluation_result.suggested_price:.2f}**")
        response_parts.append(f"Confidence: {evaluation_result.confidence_score:.0%}")
        
        # Market analysis
        if evaluation_result.market_analysis:
            response_parts.append(f"**Market Analysis:**\n{evaluation_result.market_analysis}")
        
        # AI notes
        if evaluation_result.ai_notes:
            response_parts.append(f"**AI Notes:**\n{evaluation_result.ai_notes}")
        
        # Selling recommendation
        if evaluation_result.selling_recommendation:
            response_parts.append(f"**Selling Recommendation:**\n{evaluation_result.selling_recommendation}")
        
        return "\n\n".join(response_parts)
    
    async def _generate_coin_description(self, coin_data: Dict[str, Any]) -> str:
        """Generate coin description"""
        
        description_parts = []
        
        # Basic info
        if coin_data.get('year'):
            description_parts.append(f"**Year:** {coin_data['year']}")
        
        if coin_data.get('denomination'):
            description_parts.append(f"**Denomination:** {coin_data['denomination']}")
        
        if coin_data.get('grade'):
            description_parts.append(f"**Grade:** {coin_data['grade']}")
        
        # Material info
        if coin_data.get('is_silver'):
            description_parts.append("**Material:** Silver")
            if coin_data.get('silver_content_oz'):
                description_parts.append(f"**Silver Content:** {coin_data['silver_content_oz']} oz")
        
        # Description
        description_parts.append("**Description:** This coin appears to be a collectible piece with potential numismatic value.")
        
        return "\n".join(description_parts)
    
    async def _get_historical_data(self, coin_data: Dict[str, Any]) -> str:
        """Get historical data and rarity information"""
        
        response_parts = []
        
        # Year info
        if coin_data.get('year'):
            year = coin_data['year']
            response_parts.append(f"**Year:** {year}")
            
            # Historical context
            if year < 1900:
                response_parts.append("**Era:** Pre-1900 (Classic period)")
            elif year < 1950:
                response_parts.append("**Era:** Early 20th Century")
            else:
                response_parts.append("**Era:** Modern period")
        
        # Rarity assessment
        response_parts.append("**Rarity Assessment:**")
        response_parts.append("- Historical significance: Moderate to High")
        response_parts.append("- Mintage: Varies by year and mint")
        response_parts.append("- Survival rate: Depends on grade and storage")
        
        # Market trends
        response_parts.append("**Market Trends:**")
        response_parts.append("- Collectible coins generally appreciate over time")
        response_parts.append("- Grade and condition significantly affect value")
        response_parts.append("- Market demand fluctuates with economic conditions")
        
        return "\n".join(response_parts)
    
    async def _visual_identification_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Visual identification search"""
        
        # Extract coin information from query
        coin_data = await self._extract_coin_data(query)
        
        # Generate visual identification response
        response = await self._generate_visual_identification_response(coin_data)
        
        return {
            'response': response,
            'confidence_score': 0.75,
            'pricing': None
        }
    
    async def _grade_assessment_search(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Grade assessment search"""
        
        # Extract coin information from query
        coin_data = await self._extract_coin_data(query)
        
        # Generate grade assessment response
        response = await self._generate_grade_assessment_response(coin_data)
        
        return {
            'response': response,
            'confidence_score': 0.70,
            'pricing': None
        }
    
    async def _generate_visual_identification_response(self, coin_data: Dict[str, Any]) -> str:
        """Generate visual identification response"""
        
        response_parts = []
        
        # Header
        response_parts.append("## Visual Identification")
        
        # Basic info
        if coin_data.get('year'):
            response_parts.append(f"**Year:** {coin_data['year']}")
        
        if coin_data.get('denomination'):
            response_parts.append(f"**Denomination:** {coin_data['denomination']}")
        
        if coin_data.get('grade'):
            response_parts.append(f"**Grade:** {coin_data['grade']}")
        
        # Visual characteristics
        response_parts.append("\n**Visual Characteristics:**")
        response_parts.append("- Coin appears to be in good condition")
        response_parts.append("- Surface details are visible")
        response_parts.append("- Strike quality appears adequate")
        
        # Identification notes
        response_parts.append("\n**Identification Notes:**")
        response_parts.append("- This is a preliminary identification based on description")
        response_parts.append("- For accurate identification, please upload a clear image")
        response_parts.append("- Consider professional authentication for valuable coins")
        
        return "\n".join(response_parts)
    
    async def _generate_grade_assessment_response(self, coin_data: Dict[str, Any]) -> str:
        """Generate grade assessment response"""
        
        response_parts = []
        
        # Header
        response_parts.append("## Grade Assessment")
        
        # Grade estimate
        grade = coin_data.get('grade', 'Unknown')
        response_parts.append(f"**Estimated Grade:** {grade}")
        
        # Grade factors
        response_parts.append("\n**Grade Factors:**")
        response_parts.append("- Strike quality: Good")
        response_parts.append("- Surface preservation: Good")
        response_parts.append("- Eye appeal: Good")
        
        # Recommendations
        response_parts.append("\n**Recommendations:**")
        response_parts.append("- For accurate grading, consider professional certification")
        response_parts.append("- Multiple angles and better lighting would improve assessment")
        response_parts.append("- Consider the coin's strike quality and surface preservation")
        
        return "\n".join(response_parts)
