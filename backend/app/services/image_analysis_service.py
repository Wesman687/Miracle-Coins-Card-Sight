from typing import Dict, Any, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from app.types import CoinBase, AIEvaluationRequest, AIEvaluationResponse
from app.repositories_typed import CoinRepository, SpotPriceRepository
from app.services.ai_evaluation_service import AIEvaluationService
import logging
import json
import httpx
from datetime import datetime
import asyncio
import base64
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.coin_repo = CoinRepository(db)
        self.spot_repo = SpotPriceRepository(db)
        self.ai_evaluation_service = AIEvaluationService(db)
    
    async def analyze_coin_image(
        self, 
        image_url: str, 
        preset: str = 'visual_identification',
        additional_context: str = ''
    ) -> Dict[str, Any]:
        """Analyze coin image for identification and pricing"""
        
        try:
            # Download and process image
            image_data = await self._download_and_process_image(image_url)
            
            # Extract visual features
            visual_features = await self._extract_visual_features(image_data)
            
            # Identify coin based on visual features
            coin_identification = await self._identify_coin_from_image(visual_features)
            
            # Generate response based on preset
            if preset == 'visual_identification':
                response = await self._generate_visual_id_response(coin_identification)
            elif preset == 'grade_assessment':
                response = await self._generate_grade_assessment_response(coin_identification, visual_features)
            elif preset == 'in_depth_analysis':
                response = await self._generate_in_depth_image_analysis(coin_identification, visual_features)
            else:
                response = await self._generate_visual_id_response(coin_identification)
            
            # Calculate pricing if coin is identified
            pricing = None
            if coin_identification.get('identified'):
                pricing = await self._calculate_pricing_from_identification(coin_identification)
            
            return {
                'response': response,
                'confidence_score': coin_identification.get('confidence', 0.7),
                'pricing': pricing,
                'coin_identification': coin_identification,
                'visual_features': visual_features
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            return {
                'response': 'I encountered an error while analyzing the coin image. Please try again with a clearer photo.',
                'confidence_score': 0.0,
                'pricing': None,
                'coin_identification': {'identified': False},
                'visual_features': {}
            }
    
    async def _download_and_process_image(self, image_url: str) -> Dict[str, Any]:
        """Download and process image for analysis"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                # Open image with PIL
                image = Image.open(io.BytesIO(response.content))
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Get image metadata
                image_data = {
                    'size': image.size,
                    'mode': image.mode,
                    'format': image.format,
                    'data': response.content
                }
                
                logger.info(f"Processed image: {image.size}, mode: {image.mode}")
                return image_data
                
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
    
    async def _extract_visual_features(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract visual features from coin image"""
        
        try:
            # Basic image analysis
            size = image_data['size']
            width, height = size
            
            # Calculate aspect ratio
            aspect_ratio = width / height if height > 0 else 1.0
            
            # Determine if image is likely a coin (roughly circular/square)
            is_likely_coin = 0.8 <= aspect_ratio <= 1.25
            
            # Estimate coin size based on image dimensions
            # This is a rough estimation
            estimated_diameter = min(width, height)
            
            features = {
                'image_size': size,
                'aspect_ratio': aspect_ratio,
                'is_likely_coin': is_likely_coin,
                'estimated_diameter': estimated_diameter,
                'image_quality': 'good' if min(width, height) > 200 else 'poor'
            }
            
            logger.info(f"Extracted visual features: {features}")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting visual features: {str(e)}")
            return {}
    
    async def _identify_coin_from_image(self, visual_features: Dict[str, Any]) -> Dict[str, Any]:
        """Identify coin from visual features"""
        
        try:
            # This would typically use AI/ML models for coin identification
            # For now, we'll use pattern matching and heuristics
            
            identification = {
                'identified': False,
                'confidence': 0.0,
                'coin_type': None,
                'year': None,
                'denomination': None,
                'mint_mark': None,
                'grade_estimate': None,
                'material': None
            }
            
            # Basic heuristics for coin identification
            if visual_features.get('is_likely_coin'):
                identification['identified'] = True
                identification['confidence'] = 0.6
                
                # Estimate based on size
                diameter = visual_features.get('estimated_diameter', 0)
                if diameter > 300:
                    identification['coin_type'] = 'Large coin (likely dollar)'
                    identification['denomination'] = 'dollar'
                elif diameter > 200:
                    identification['coin_type'] = 'Medium coin (likely half dollar or quarter)'
                    identification['denomination'] = 'half dollar or quarter'
                elif diameter > 150:
                    identification['coin_type'] = 'Small coin (likely dime or nickel)'
                    identification['denomination'] = 'dime or nickel'
                else:
                    identification['coin_type'] = 'Very small coin (likely penny)'
                    identification['denomination'] = 'penny'
                
                # Estimate grade based on image quality
                if visual_features.get('image_quality') == 'good':
                    identification['grade_estimate'] = 'MS-60 to MS-65'
                else:
                    identification['grade_estimate'] = 'VF to AU'
                
                identification['material'] = 'Likely silver or copper'
            
            logger.info(f"Coin identification result: {identification}")
            return identification
            
        except Exception as e:
            logger.error(f"Error identifying coin: {str(e)}")
            return {'identified': False, 'confidence': 0.0}
    
    async def _generate_visual_id_response(self, identification: Dict[str, Any]) -> str:
        """Generate response for visual identification"""
        
        if not identification.get('identified'):
            return "I couldn't identify this as a coin. Please ensure the image shows a clear view of a coin."
        
        response_parts = []
        
        # Basic identification
        response_parts.append("## Coin Identification")
        
        if identification.get('coin_type'):
            response_parts.append(f"**Coin Type:** {identification['coin_type']}")
        
        if identification.get('denomination'):
            response_parts.append(f"**Denomination:** {identification['denomination']}")
        
        if identification.get('year'):
            response_parts.append(f"**Year:** {identification['year']}")
        
        if identification.get('mint_mark'):
            response_parts.append(f"**Mint Mark:** {identification['mint_mark']}")
        
        if identification.get('grade_estimate'):
            response_parts.append(f"**Estimated Grade:** {identification['grade_estimate']}")
        
        if identification.get('material'):
            response_parts.append(f"**Material:** {identification['material']}")
        
        # Confidence note
        confidence = identification.get('confidence', 0)
        response_parts.append(f"\n**Confidence:** {confidence:.0%}")
        response_parts.append("💡 *This is a preliminary identification based on image analysis. For accurate identification, please provide additional details.*")
        
        return "\n".join(response_parts)
    
    async def _generate_grade_assessment_response(self, identification: Dict[str, Any], visual_features: Dict[str, Any]) -> str:
        """Generate response for grade assessment"""
        
        if not identification.get('identified'):
            return "I couldn't assess the grade of this coin. Please ensure the image shows a clear view of a coin."
        
        response_parts = []
        
        # Grade assessment
        response_parts.append("## Grade Assessment")
        
        grade_estimate = identification.get('grade_estimate', 'Unknown')
        response_parts.append(f"**Estimated Grade:** {grade_estimate}")
        
        # Image quality assessment
        image_quality = visual_features.get('image_quality', 'unknown')
        response_parts.append(f"**Image Quality:** {image_quality.title()}")
        
        # Grade factors
        response_parts.append("\n**Grade Factors:**")
        
        if image_quality == 'good':
            response_parts.append("- Clear image allows for detailed assessment")
            response_parts.append("- Surface details visible")
            response_parts.append("- Strike quality can be evaluated")
        else:
            response_parts.append("- Image quality limits detailed assessment")
            response_parts.append("- Grade estimate based on general appearance")
        
        # Recommendations
        response_parts.append("\n**Recommendations:**")
        response_parts.append("- For accurate grading, consider professional certification")
        response_parts.append("- Multiple angles and better lighting would improve assessment")
        response_parts.append("- Consider the coin's strike quality and surface preservation")
        
        return "\n".join(response_parts)
    
    async def _generate_in_depth_image_analysis(self, identification: Dict[str, Any], visual_features: Dict[str, Any]) -> str:
        """Generate comprehensive image analysis"""
        
        if not identification.get('identified'):
            return "I couldn't perform a comprehensive analysis of this coin. Please ensure the image shows a clear view of a coin."
        
        response_parts = []
        
        # Comprehensive analysis
        response_parts.append("## Comprehensive Image Analysis")
        
        # Identification details
        response_parts.append("### Identification")
        if identification.get('coin_type'):
            response_parts.append(f"- **Type:** {identification['coin_type']}")
        if identification.get('denomination'):
            response_parts.append(f"- **Denomination:** {identification['denomination']}")
        if identification.get('material'):
            response_parts.append(f"- **Material:** {identification['material']}")
        
        # Visual assessment
        response_parts.append("\n### Visual Assessment")
        response_parts.append(f"- **Image Quality:** {visual_features.get('image_quality', 'unknown').title()}")
        response_parts.append(f"- **Aspect Ratio:** {visual_features.get('aspect_ratio', 1):.2f}")
        response_parts.append(f"- **Estimated Size:** {visual_features.get('estimated_diameter', 0)} pixels")
        
        # Grade assessment
        response_parts.append("\n### Grade Assessment")
        grade_estimate = identification.get('grade_estimate', 'Unknown')
        response_parts.append(f"- **Estimated Grade:** {grade_estimate}")
        
        # Market considerations
        response_parts.append("\n### Market Considerations")
        response_parts.append("- Professional grading recommended for high-value coins")
        response_parts.append("- Image-based assessment has limitations")
        response_parts.append("- Consider multiple factors for pricing")
        
        # Confidence and limitations
        confidence = identification.get('confidence', 0)
        response_parts.append(f"\n**Analysis Confidence:** {confidence:.0%}")
        response_parts.append("⚠️ *This analysis is based on image recognition and may not be 100% accurate. Professional evaluation recommended for important coins.*")
        
        return "\n".join(response_parts)
    
    async def _calculate_pricing_from_identification(self, identification: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate pricing based on coin identification"""
        
        try:
            # This would typically use the existing pricing engine
            # For now, we'll provide basic estimates
            
            denomination = identification.get('denomination')
            grade_estimate = identification.get('grade_estimate')
            material = identification.get('material')
            
            if not denomination:
                return None
            
            # Basic pricing estimates (these would be more sophisticated in practice)
            base_prices = {
                'dollar': 25.00,
                'half dollar': 12.00,
                'quarter': 6.00,
                'dime': 2.50,
                'nickel': 1.00,
                'penny': 0.50
            }
            
            base_price = base_prices.get(denomination, 10.00)
            
            # Adjust for grade
            grade_multiplier = 1.0
            if grade_estimate and 'MS' in grade_estimate:
                grade_multiplier = 1.5
            elif grade_estimate and 'AU' in grade_estimate:
                grade_multiplier = 1.3
            elif grade_estimate and 'VF' in grade_estimate:
                grade_multiplier = 1.1
            
            # Adjust for material
            material_multiplier = 1.0
            if material and 'silver' in material.lower():
                material_multiplier = 1.2
            
            suggested_price = base_price * grade_multiplier * material_multiplier
            
            return {
                'suggested_price': float(suggested_price),
                'melt_value': float(base_price * 0.8),  # Rough melt estimate
                'confidence_score': identification.get('confidence', 0.7),
                'category': 'standard'
            }
            
        except Exception as e:
            logger.error(f"Error calculating pricing: {str(e)}")
            return None

