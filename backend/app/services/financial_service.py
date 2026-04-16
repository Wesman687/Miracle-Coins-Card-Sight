from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from app.models.financial import (
    FinancialPeriod, CashFlow, PricingStrategy, PricingUpdate,
    FinancialMetrics, ExpenseCategory, Expense
)
from app.models import Coin
from app.models.sales import Sale, SalesChannel
from app.schemas.financial import (
    PLStatementResponse, CashFlowAnalysisResponse, FinancialDashboardResponse,
    PricingStrategyResponse, FinancialMetricsResponse
)

logger = logging.getLogger(__name__)

class FinancialService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_p_l_statement(
        self,
        start_date: date,
        end_date: date
    ) -> PLStatementResponse:
        """Generate P&L statement for a specific period"""
        
        # Get sales data for the period
        sales_data = self.db.query(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).all()
        
        # Calculate revenue
        total_revenue = sum(sale.sale_price for sale in sales_data)
        sales_revenue = total_revenue  # All revenue is from sales for now
        other_revenue = Decimal('0')  # No other revenue sources yet
        
        # Calculate cost of goods sold
        cost_of_goods = sum(sale.sale_price - sale.profit for sale in sales_data)
        
        # Calculate gross profit
        gross_profit = total_revenue - cost_of_goods
        gross_profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        # Get operating expenses (placeholder - would come from expense tracking)
        operating_expenses = Decimal('1000')  # Placeholder value
        
        # Calculate operating profit
        operating_profit = gross_profit - operating_expenses
        operating_margin = (operating_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        # Other expenses
        other_expenses = Decimal('0')
        
        # Calculate net profit
        net_profit = operating_profit - other_expenses
        net_profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        # Calculate growth (compare with previous period)
        previous_period_start = start_date - (end_date - start_date)
        previous_sales = self.db.query(Sale).filter(
            and_(
                Sale.sold_at >= previous_period_start,
                Sale.sold_at < start_date
            )
        ).all()
        
        previous_revenue = sum(sale.sale_price for sale in previous_sales)
        revenue_growth = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else Decimal('0')
        
        # Calculate profit growth
        previous_profit = sum(sale.profit for sale in previous_sales)
        profit_growth = ((net_profit - previous_profit) / previous_profit * 100) if previous_profit > 0 else Decimal('0')
        
        # Calculate expense ratio
        expense_ratio = ((operating_expenses + other_expenses) / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        return PLStatementResponse(
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            period_name=f"{start_date.strftime('%B %Y')}",
            total_revenue=total_revenue,
            sales_revenue=sales_revenue,
            other_revenue=other_revenue,
            cost_of_goods=cost_of_goods,
            gross_profit=gross_profit,
            gross_profit_margin=gross_profit_margin,
            operating_expenses=operating_expenses,
            operating_profit=operating_profit,
            operating_margin=operating_margin,
            other_expenses=other_expenses,
            net_profit=net_profit,
            net_profit_margin=net_profit_margin,
            revenue_growth=revenue_growth,
            profit_growth=profit_growth,
            expense_ratio=expense_ratio
        )
    
    def get_cash_flow_analysis(
        self,
        start_date: date,
        end_date: date,
        period_type: str = "monthly"
    ) -> CashFlowAnalysisResponse:
        """Get cash flow analysis for a period"""
        
        # Operating Activities
        sales_cash_inflow = self.db.query(func.sum(Sale.sale_price)).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).scalar() or Decimal('0')
        
        expense_cash_outflow = Decimal('1000')  # Placeholder - would come from expense tracking
        operating_cash_flow = sales_cash_inflow - expense_cash_outflow
        
        # Investing Activities
        inventory_investment = self.db.query(func.sum(Coin.paid_price * Coin.quantity)).filter(
            and_(
                Coin.created_at >= start_date,
                Coin.created_at <= end_date
            )
        ).scalar() or Decimal('0')
        
        equipment_investment = Decimal('0')  # Placeholder
        investing_cash_flow = -(inventory_investment + equipment_investment)
        
        # Financing Activities
        owner_investment = Decimal('0')  # Placeholder
        loan_proceeds = Decimal('0')  # Placeholder
        financing_cash_flow = owner_investment + loan_proceeds
        
        # Net Cash Flow
        net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow
        
        # Beginning and ending cash (placeholder values)
        beginning_cash = Decimal('10000')  # Placeholder
        ending_cash = beginning_cash + net_cash_flow
        
        # Cash Flow Ratios
        total_revenue = sales_cash_inflow
        operating_cash_flow_margin = (operating_cash_flow / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        # Cash conversion cycle (placeholder calculation)
        cash_conversion_cycle = Decimal('30')  # 30 days placeholder
        
        return CashFlowAnalysisResponse(
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            period_name=f"{start_date.strftime('%B %Y')}",
            operating_cash_flow=operating_cash_flow,
            sales_cash_inflow=sales_cash_inflow,
            expense_cash_outflow=expense_cash_outflow,
            investing_cash_flow=investing_cash_flow,
            inventory_investment=inventory_investment,
            equipment_investment=equipment_investment,
            financing_cash_flow=financing_cash_flow,
            owner_investment=owner_investment,
            loan_proceeds=loan_proceeds,
            net_cash_flow=net_cash_flow,
            beginning_cash=beginning_cash,
            ending_cash=ending_cash,
            operating_cash_flow_margin=operating_cash_flow_margin,
            cash_conversion_cycle=cash_conversion_cycle
        )
    
    def create_pricing_strategy(
        self,
        name: str,
        strategy_type: str,
        base_multiplier: Optional[Decimal] = None,
        min_profit_margin: Optional[Decimal] = None,
        max_profit_margin: Optional[Decimal] = None,
        category_overrides: Optional[Dict] = None,
        created_by: str = "system"
    ) -> PricingStrategy:
        """Create a new pricing strategy"""
        
        strategy = PricingStrategy(
            name=name,
            strategy_type=strategy_type,
            base_multiplier=base_multiplier,
            min_profit_margin=min_profit_margin,
            max_profit_margin=max_profit_margin,
            category_overrides=category_overrides,
            created_by=created_by
        )
        
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        
        return strategy
    
    def apply_pricing_strategy(
        self,
        strategy_id: int,
        coin_ids: Optional[List[int]] = None,
        applied_by: str = "system"
    ) -> Dict[str, Any]:
        """Apply pricing strategy to coins"""
        
        strategy = self.db.query(PricingStrategy).filter(PricingStrategy.id == strategy_id).first()
        if not strategy:
            raise ValueError("Pricing strategy not found")
        
        # Get coins to update
        query = self.db.query(Coin)
        if coin_ids:
            query = query.filter(Coin.id.in_(coin_ids))
        else:
            query = query.filter(Coin.status == "active")
        
        coins = query.all()
        
        updates_applied = 0
        errors = []
        
        for coin in coins:
            try:
                old_price = coin.computed_price
                
                # Apply strategy based on type
                if strategy.strategy_type == "spot_plus_percentage":
                    if coin.entry_melt and strategy.base_multiplier:
                        new_price = coin.entry_melt * strategy.base_multiplier
                    else:
                        continue
                
                elif strategy.strategy_type == "profit_margin_target":
                    if coin.paid_price and strategy.min_profit_margin:
                        target_margin = strategy.min_profit_margin
                        new_price = coin.paid_price * (1 + target_margin)
                    else:
                        continue
                
                elif strategy.strategy_type == "competitive":
                    # Placeholder for competitive pricing logic
                    new_price = coin.computed_price or coin.paid_price * Decimal('1.3')
                
                else:
                    continue
                
                # Apply category overrides if specified
                if strategy.category_overrides and coin.category:
                    category_override = strategy.category_overrides.get(coin.category)
                    if category_override:
                        if 'multiplier' in category_override:
                            new_price = new_price * Decimal(str(category_override['multiplier']))
                        elif 'margin' in category_override:
                            if coin.paid_price:
                                new_price = coin.paid_price * (1 + Decimal(str(category_override['margin'])))
                
                # Apply min/max profit margin constraints
                if coin.paid_price and strategy.min_profit_margin:
                    min_price = coin.paid_price * (1 + strategy.min_profit_margin)
                    new_price = max(new_price, min_price)
                
                if coin.paid_price and strategy.max_profit_margin:
                    max_price = coin.paid_price * (1 + strategy.max_profit_margin)
                    new_price = min(new_price, max_price)
                
                # Update coin price
                coin.computed_price = new_price
                
                # Create pricing update record
                price_change = new_price - old_price if old_price else Decimal('0')
                change_percentage = (price_change / old_price * 100) if old_price else Decimal('0')
                
                pricing_update = PricingUpdate(
                    strategy_id=strategy_id,
                    coin_id=coin.id,
                    old_price=old_price,
                    new_price=new_price,
                    price_change=price_change,
                    change_percentage=change_percentage,
                    update_reason=f"Applied strategy: {strategy.name}",
                    applied_by=applied_by
                )
                
                self.db.add(pricing_update)
                updates_applied += 1
                
            except Exception as e:
                errors.append(f"Error updating coin {coin.id}: {str(e)}")
        
        # Update strategy applied timestamp
        strategy.applied_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "coins_updated": updates_applied,
            "total_coins": len(coins),
            "errors": errors
        }
    
    def calculate_financial_metrics(
        self,
        start_date: date,
        end_date: date,
        period_type: str = "monthly"
    ) -> FinancialMetrics:
        """Calculate and store financial metrics for a period"""
        
        # Get sales data
        sales = self.db.query(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).all()
        
        # Revenue metrics
        total_revenue = sum(sale.sale_price for sale in sales)
        sales_revenue = total_revenue
        
        # Calculate revenue growth
        previous_period_start = start_date - (end_date - start_date)
        previous_sales = self.db.query(Sale).filter(
            and_(
                Sale.sold_at >= previous_period_start,
                Sale.sold_at < start_date
            )
        ).all()
        
        previous_revenue = sum(sale.sale_price for sale in previous_sales)
        revenue_growth = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else Decimal('0')
        
        # Cost metrics
        cost_of_goods = sum(sale.sale_price - sale.profit for sale in sales)
        operating_expenses = Decimal('1000')  # Placeholder
        total_costs = cost_of_goods + operating_expenses
        
        # Profit metrics
        gross_profit = total_revenue - cost_of_goods
        net_profit = gross_profit - operating_expenses
        
        gross_profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        net_profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        # Cash flow metrics
        operating_cash_flow = total_revenue - operating_expenses
        net_cash_flow = operating_cash_flow  # Simplified
        
        # Inventory metrics
        inventory_value = self.db.query(func.sum(Coin.computed_price * Coin.quantity)).scalar() or Decimal('0')
        
        # Calculate inventory turnover
        inventory_turnover = (cost_of_goods / inventory_value) if inventory_value > 0 else Decimal('0')
        
        # Return metrics
        return_on_investment = (net_profit / inventory_value * 100) if inventory_value > 0 else Decimal('0')
        return_on_assets = return_on_investment  # Simplified
        
        # Create metrics record
        metrics = FinancialMetrics(
            period_type=period_type,
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            total_revenue=total_revenue,
            sales_revenue=sales_revenue,
            revenue_growth=revenue_growth,
            total_costs=total_costs,
            cost_of_goods=cost_of_goods,
            operating_expenses=operating_expenses,
            gross_profit=gross_profit,
            net_profit=net_profit,
            gross_profit_margin=gross_profit_margin,
            net_profit_margin=net_profit_margin,
            operating_cash_flow=operating_cash_flow,
            net_cash_flow=net_cash_flow,
            inventory_value=inventory_value,
            inventory_turnover=inventory_turnover,
            return_on_investment=return_on_investment,
            return_on_assets=return_on_assets
        )
        
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        
        return metrics
    
    def get_financial_dashboard(
        self,
        start_date: date,
        end_date: date
    ) -> FinancialDashboardResponse:
        """Get comprehensive financial dashboard data"""
        
        # Generate P&L statement
        pl_statement = self.generate_p_l_statement(start_date, end_date)
        
        # Get cash flow analysis
        cash_flow_analysis = self.get_cash_flow_analysis(start_date, end_date)
        
        # Calculate KPIs
        kpis = {
            "revenue": float(pl_statement.total_revenue),
            "gross_profit_margin": float(pl_statement.gross_profit_margin),
            "net_profit_margin": float(pl_statement.net_profit_margin),
            "revenue_growth": float(pl_statement.revenue_growth),
            "operating_cash_flow": float(cash_flow_analysis.operating_cash_flow),
            "inventory_turnover": 12.0,  # Placeholder
            "return_on_investment": 15.0  # Placeholder
        }
        
        # Generate trends (simplified) - Convert Decimal to float for JSON serialization
        revenue_trend = [
            {"period": "Jan", "value": float(pl_statement.total_revenue * Decimal('0.8'))},
            {"period": "Feb", "value": float(pl_statement.total_revenue * Decimal('0.9'))},
            {"period": "Mar", "value": float(pl_statement.total_revenue)}
        ]
        
        profit_trend = [
            {"period": "Jan", "value": float(pl_statement.net_profit * Decimal('0.7'))},
            {"period": "Feb", "value": float(pl_statement.net_profit * Decimal('0.85'))},
            {"period": "Mar", "value": float(pl_statement.net_profit)}
        ]
        
        expense_trend = [
            {"period": "Jan", "value": float(pl_statement.operating_expenses * Decimal('1.1'))},
            {"period": "Feb", "value": float(pl_statement.operating_expenses * Decimal('1.05'))},
            {"period": "Mar", "value": float(pl_statement.operating_expenses)}
        ]
        
        # Generate alerts
        financial_alerts = []
        
        if pl_statement.net_profit_margin < 10:
            financial_alerts.append({
                "type": "warning",
                "message": "Net profit margin below 10%",
                "severity": "medium"
            })
        
        if pl_statement.revenue_growth < 0:
            financial_alerts.append({
                "type": "error",
                "message": "Revenue declining",
                "severity": "high"
            })
        
        return FinancialDashboardResponse(
            current_period=pl_statement,
            cash_flow_analysis=cash_flow_analysis,
            kpis=kpis,
            revenue_trend=revenue_trend,
            profit_trend=profit_trend,
            expense_trend=expense_trend,
            financial_alerts=financial_alerts
        )


