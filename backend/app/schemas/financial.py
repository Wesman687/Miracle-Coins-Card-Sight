from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class FinancialPeriodBase(BaseModel):
    period_type: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: datetime
    notes: Optional[str] = None
    adjustments: Optional[Dict[str, Any]] = None

class FinancialPeriodCreate(FinancialPeriodBase):
    pass

class FinancialPeriodResponse(FinancialPeriodBase):
    id: int
    total_revenue: Decimal
    sales_revenue: Decimal
    other_revenue: Decimal
    cost_of_goods: Decimal
    operating_expenses: Decimal
    other_expenses: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CashFlowBase(BaseModel):
    period_id: int
    operating_cash_flow: Decimal = Field(default=Decimal('0'))
    investing_cash_flow: Decimal = Field(default=Decimal('0'))
    financing_cash_flow: Decimal = Field(default=Decimal('0'))
    beginning_cash: Decimal = Field(default=Decimal('0'))

class CashFlowCreate(CashFlowBase):
    pass

class CashFlowResponse(CashFlowBase):
    id: int
    net_cash_flow: Decimal
    ending_cash: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True

class PricingStrategyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    strategy_type: str = Field(..., pattern="^(spot_plus_percentage|profit_margin_target|competitive)$")
    base_multiplier: Optional[Decimal] = None
    min_profit_margin: Optional[Decimal] = None
    max_profit_margin: Optional[Decimal] = None
    category_overrides: Optional[Dict[str, Any]] = None

class PricingStrategyCreate(PricingStrategyBase):
    pass

class PricingStrategyResponse(PricingStrategyBase):
    id: int
    active: bool
    applied_at: Optional[datetime]
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True

class PricingUpdateResponse(BaseModel):
    id: int
    strategy_id: int
    coin_id: int
    old_price: Optional[Decimal]
    new_price: Optional[Decimal]
    price_change: Optional[Decimal]
    change_percentage: Optional[Decimal]
    update_reason: Optional[str]
    applied_at: datetime
    applied_by: str
    
    class Config:
        from_attributes = True

class FinancialMetricsResponse(BaseModel):
    period_type: str
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    sales_revenue: Decimal
    revenue_growth: Decimal
    total_costs: Decimal
    cost_of_goods: Decimal
    operating_expenses: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    gross_profit_margin: Decimal
    net_profit_margin: Decimal
    operating_cash_flow: Decimal
    net_cash_flow: Decimal
    inventory_value: Decimal
    inventory_turnover: Decimal
    return_on_investment: Decimal
    return_on_assets: Decimal
    calculated_at: datetime
    
    class Config:
        from_attributes = True

class PLStatementResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    period_name: str
    
    # Revenue
    total_revenue: Decimal
    sales_revenue: Decimal
    other_revenue: Decimal
    
    # Costs
    cost_of_goods: Decimal
    gross_profit: Decimal
    gross_profit_margin: Decimal
    
    # Operating Expenses
    operating_expenses: Decimal
    operating_profit: Decimal
    operating_margin: Decimal
    
    # Other Expenses
    other_expenses: Decimal
    net_profit: Decimal
    net_profit_margin: Decimal
    
    # Additional Metrics
    revenue_growth: Decimal
    profit_growth: Decimal
    expense_ratio: Decimal

class CashFlowAnalysisResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    period_name: str
    
    # Operating Activities
    operating_cash_flow: Decimal
    sales_cash_inflow: Decimal
    expense_cash_outflow: Decimal
    
    # Investing Activities
    investing_cash_flow: Decimal
    inventory_investment: Decimal
    equipment_investment: Decimal
    
    # Financing Activities
    financing_cash_flow: Decimal
    owner_investment: Decimal
    loan_proceeds: Decimal
    
    # Net Cash Flow
    net_cash_flow: Decimal
    beginning_cash: Decimal
    ending_cash: Decimal
    
    # Cash Flow Ratios
    operating_cash_flow_margin: Decimal
    cash_conversion_cycle: Decimal

class ExpenseCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: str = Field(..., pattern="^(operating|cost_of_goods|other)$")
    monthly_budget: Optional[Decimal] = None
    annual_budget: Optional[Decimal] = None

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    vendor: Optional[str] = None
    reference_number: Optional[str] = None
    expense_date: datetime
    period_start: datetime
    period_end: datetime

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    status: str
    created_at: datetime
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class FinancialDashboardResponse(BaseModel):
    # Current Period Metrics
    current_period: PLStatementResponse
    
    # Cash Flow Analysis
    cash_flow_analysis: CashFlowAnalysisResponse
    
    # Key Performance Indicators
    kpis: Dict[str, Any]
    
    # Trends
    revenue_trend: List[Dict[str, Any]]
    profit_trend: List[Dict[str, Any]]
    expense_trend: List[Dict[str, Any]]
    
    # Alerts
    financial_alerts: List[Dict[str, Any]]

class BudgetAnalysisResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    
    # Budget vs Actual
    budget_vs_actual: List[Dict[str, Any]]
    
    # Variance Analysis
    total_budget: Decimal
    total_actual: Decimal
    total_variance: Decimal
    variance_percentage: Decimal
    
    # Category Analysis
    category_analysis: List[Dict[str, Any]]
    
    # Recommendations
    recommendations: List[str]


