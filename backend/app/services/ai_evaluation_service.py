from typing import Dict, Any, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from app.types import CoinBase, AIEvaluationRequest, AIEvaluationResponse
from app.repositories_typed import CoinRepository, SpotPriceRepository
import logging
import json
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class AIEvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.coin_repo = CoinRepository(db)
        self.spot_repo = SpotPriceRepository(db)
    
    def evaluate_coin(self, request: AIEvaluationRequest) -> AIEvaluationResponse:
        """Evaluate coin and provide AI-powered suggestions"""
        try:
            # Get current spot price
            spot_price = self.spot_repo.get_latest("silver")
            current_spot = spot_price.price if spot_price else Decimal('25.00')
            
            # Analyze coin data
            analysis = self._analyze_coin_data(request.coin_data, current_spot)
            
            # Generate pricing suggestion
            suggested_price = self._calculate_suggested_price(
                request.coin_data, 
                current_spot, 
                analysis
            )
            
            # Determine selling recommendation
            selling_recommendation = self._determine_selling_strategy(
                request.coin_data, 
                analysis
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                request.coin_data, 
                analysis
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                request.coin_data, 
                suggested_price, 
                selling_recommendation, 
                analysis
            )
            
            return AIEvaluationResponse(
                suggested_price=suggested_price,
                confidence_score=confidence_score,
                selling_recommendation=selling_recommendation,
                reasoning=reasoning,
                market_analysis=analysis
            )
            
        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            # Return fallback response
            return AIEvaluationResponse(
                suggested_price=request.coin_data.paid_price or Decimal('50.00'),
                confidence_score=0.5,
                selling_recommendation="individual",
                reasoning="Unable to perform full analysis. Using basic pricing.",
                market_analysis={"error": str(e)}
            )
    
    def _analyze_coin_data(self, coin_data: CoinBase, current_spot: Decimal) -> Dict[str, Any]:
        """Analyze coin data for market insights"""
        analysis = {
            "coin_type": "silver" if coin_data.is_silver else "non-silver",
            "rarity_score": 0.5,
            "condition_score": 0.7,
            "market_demand": "medium",
            "historical_performance": "stable",
            "grade_premium": 0.0,
            "year_significance": 0.0,
            "mint_mark_premium": 0.0
        }
        
        # Analyze grade
        if coin_data.grade:
            grade_score = self._analyze_grade(coin_data.grade)
            analysis["grade_premium"] = grade_score
            analysis["condition_score"] = grade_score
        
        # Analyze year significance
        if coin_data.year:
            year_score = self._analyze_year_significance(coin_data.year)
            analysis["year_significance"] = year_score
        
        # Analyze mint mark
        if coin_data.mint_mark:
            mint_score = self._analyze_mint_mark_premium(coin_data.mint_mark)
            analysis["mint_mark_premium"] = mint_score
        
        # Analyze title for rarity indicators
        title_lower = coin_data.title.lower()
        if any(word in title_lower for word in ["rare", "scarce", "limited", "proof", "uncirculated"]):
            analysis["rarity_score"] = 0.8
            analysis["market_demand"] = "high"
        
        # Calculate melt value if silver
        if coin_data.is_silver and coin_data.silver_content_oz:
            melt_value = coin_data.silver_content_oz * current_spot
            analysis["melt_value"] = float(melt_value)
            analysis["melt_premium_potential"] = 1.5 if melt_value < 100 else 1.3
        
        return analysis
    
    def _analyze_grade(self, grade: str) -> float:
        """Analyze coin grade for premium calculation"""
        grade_lower = grade.lower()
        
        # MS grades
        if grade_lower.startswith('ms'):
            try:
                ms_number = int(grade_lower[2:])
                if ms_number >= 65:
                    return 0.9
                elif ms_number >= 60:
                    return 0.7
                else:
                    return 0.5
            except:
                return 0.6
        
        # AU grades
        elif grade_lower.startswith('au'):
            try:
                au_number = int(grade_lower[2:])
                if au_number >= 58:
                    return 0.6
                else:
                    return 0.4
            except:
                return 0.5
        
        # XF grades
        elif grade_lower.startswith('xf'):
            return 0.3
        
        # VF grades
        elif grade_lower.startswith('vf'):
            return 0.2
        
        # Proof grades
        elif 'proof' in grade_lower:
            return 0.95
        
        return 0.5
    
    def _analyze_year_significance(self, year: int) -> float:
        """Analyze year significance for premium calculation"""
        current_year = datetime.now().year
        
        # Very old coins (pre-1900)
        if year < 1900:
            return 0.8
        
        # Key years for US coins
        key_years = [1921, 1933, 1964, 1976, 2000]
        if year in key_years:
            return 0.7
        
        # Recent years
        if year > current_year - 10:
            return 0.3
        
        # Mid-century
        if 1950 <= year <= 1980:
            return 0.5
        
        return 0.4
    
    def _analyze_mint_mark_premium(self, mint_mark: str) -> float:
        """Analyze mint mark for premium calculation"""
        mint_lower = mint_mark.lower()
        
        # Carson City mint (CC) - highest premium
        if mint_lower == 'cc':
            return 0.9
        
        # San Francisco mint (S) - high premium
        if mint_lower == 's':
            return 0.7
        
        # Denver mint (D) - medium premium
        if mint_lower == 'd':
            return 0.5
        
        # Philadelphia mint (P) - standard
        if mint_lower == 'p':
            return 0.3
        
        return 0.4
    
    def _calculate_suggested_price(self, coin_data: CoinBase, current_spot: Decimal, analysis: Dict[str, Any]) -> Decimal:
        """Calculate AI-suggested price"""
        base_price = coin_data.paid_price or Decimal('50.00')
        
        # If it's a silver coin, calculate melt-based pricing
        if coin_data.is_silver and coin_data.silver_content_oz:
            melt_value = coin_data.silver_content_oz * current_spot
            
            # Apply grade premium
            grade_multiplier = 1.0 + analysis.get("grade_premium", 0.0)
            
            # Apply rarity premium
            rarity_multiplier = 1.0 + analysis.get("rarity_score", 0.5) * 0.5
            
            # Apply year significance
            year_multiplier = 1.0 + analysis.get("year_significance", 0.0) * 0.3
            
            # Apply mint mark premium
            mint_multiplier = 1.0 + analysis.get("mint_mark_premium", 0.0) * 0.4
            
            # Calculate suggested price
            suggested_price = melt_value * grade_multiplier * rarity_multiplier * year_multiplier * mint_multiplier
            
            # Ensure minimum premium over melt
            min_premium = melt_value * Decimal('1.2')
            suggested_price = max(suggested_price, min_premium)
            
        else:
            # For non-silver coins, use analysis-based pricing
            base_multiplier = 1.0 + analysis.get("rarity_score", 0.5) * 0.8
            grade_multiplier = 1.0 + analysis.get("grade_premium", 0.0) * 0.6
            year_multiplier = 1.0 + analysis.get("year_significance", 0.0) * 0.4
            
            suggested_price = base_price * base_multiplier * grade_multiplier * year_multiplier
        
        # Round to nearest dollar
        return suggested_price.quantize(Decimal('1.00'))
    
    def _determine_selling_strategy(self, coin_data: CoinBase, analysis: Dict[str, Any]) -> str:
        """Determine if coin should be sold individually or in bulk"""
        # Factors favoring individual sale
        individual_factors = 0
        bulk_factors = 0
        
        # High grade coins should be sold individually
        if analysis.get("grade_premium", 0.0) > 0.7:
            individual_factors += 2
        
        # Rare coins should be sold individually
        if analysis.get("rarity_score", 0.5) > 0.7:
            individual_factors += 2
        
        # Significant years should be sold individually
        if analysis.get("year_significance", 0.0) > 0.6:
            individual_factors += 1
        
        # High mint mark premium should be sold individually
        if analysis.get("mint_mark_premium", 0.0) > 0.6:
            individual_factors += 1
        
        # High melt value should be sold individually
        if analysis.get("melt_value", 0) > 100:
            individual_factors += 1
        
        # Multiple coins favor bulk sale
        if coin_data.quantity > 5:
            bulk_factors += 2
        elif coin_data.quantity > 2:
            bulk_factors += 1
        
        # Low value coins favor bulk sale
        if analysis.get("melt_value", 0) < 50:
            bulk_factors += 1
        
        if individual_factors > bulk_factors:
            return "individual"
        elif bulk_factors > individual_factors:
            return "bulk"
        else:
            return "either"
    
    def _calculate_confidence_score(self, coin_data: CoinBase, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for the evaluation"""
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if coin_data.grade:
            confidence += 0.1
        if coin_data.year:
            confidence += 0.1
        if coin_data.mint_mark:
            confidence += 0.1
        if coin_data.description:
            confidence += 0.05
        
        # Silver coins with content info = higher confidence
        if coin_data.is_silver and coin_data.silver_content_oz:
            confidence += 0.15
        
        # Paid price helps with confidence
        if coin_data.paid_price:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_reasoning(self, coin_data: CoinBase, suggested_price: Decimal, selling_recommendation: str, analysis: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the suggestions"""
        reasoning_parts = []
        
        # Price reasoning
        if coin_data.is_silver and coin_data.silver_content_oz:
            melt_value = coin_data.silver_content_oz * Decimal('25.00')  # Approximate
            premium_over_melt = (suggested_price / melt_value - 1) * 100
            reasoning_parts.append(f"Based on {coin_data.silver_content_oz} oz silver content, suggesting ${suggested_price} ({premium_over_melt:.1f}% premium over melt).")
        else:
            reasoning_parts.append(f"Suggested price of ${suggested_price} based on coin analysis.")
        
        # Grade reasoning
        if coin_data.grade and analysis.get("grade_premium", 0.0) > 0.5:
            reasoning_parts.append(f"Grade {coin_data.grade} commands a premium in the market.")
        
        # Rarity reasoning
        if analysis.get("rarity_score", 0.5) > 0.7:
            reasoning_parts.append("Coin shows characteristics of rarity and high demand.")
        
        # Year reasoning
        if coin_data.year and analysis.get("year_significance", 0.0) > 0.6:
            reasoning_parts.append(f"Year {coin_data.year} is significant in numismatic history.")
        
        # Mint mark reasoning
        if coin_data.mint_mark and analysis.get("mint_mark_premium", 0.0) > 0.6:
            reasoning_parts.append(f"Mint mark '{coin_data.mint_mark}' adds collector value.")
        
        # Selling strategy reasoning
        if selling_recommendation == "individual":
            reasoning_parts.append("Recommend selling individually to maximize value from collectors.")
        elif selling_recommendation == "bulk":
            reasoning_parts.append("Recommend bulk sale for efficiency and volume pricing.")
        else:
            reasoning_parts.append("Either individual or bulk sale could work depending on market conditions.")
        
        return " ".join(reasoning_parts)


