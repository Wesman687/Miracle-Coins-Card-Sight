from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from decimal import Decimal

class FinancialPeriod(Base):
    __tablename__ = "financial_periods"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Revenue breakdown
    total_revenue = Column(Numeric(12, 2), default=Decimal('0'))
    sales_revenue = Column(Numeric(12, 2), default=Decimal('0'))
    other_revenue = Column(Numeric(12, 2), default=Decimal('0'))
    
    # Cost breakdown
    cost_of_goods = Column(Numeric(12, 2), default=Decimal('0'))
    operating_expenses = Column(Numeric(12, 2), default=Decimal('0'))
    other_expenses = Column(Numeric(12, 2), default=Decimal('0'))
    
    # Calculated fields
    gross_profit = Column(Numeric(12, 2), default=Decimal('0'))
    net_profit = Column(Numeric(12, 2), default=Decimal('0'))
    profit_margin = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional data
    notes = Column(Text)
    adjustments = Column(JSON)  # Manual adjustments
    
    # Relationships
    cash_flows = relationship("CashFlow", back_populates="period")

class CashFlow(Base):
    __tablename__ = "cash_flow"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id"))
    
    # Cash flow categories
    operating_cash_flow = Column(Numeric(12, 2), default=Decimal('0'))
    investing_cash_flow = Column(Numeric(12, 2), default=Decimal('0'))
    financing_cash_flow = Column(Numeric(12, 2), default=Decimal('0'))
    
    # Calculated fields
    net_cash_flow = Column(Numeric(12, 2), default=Decimal('0'))
    beginning_cash = Column(Numeric(12, 2), default=Decimal('0'))
    ending_cash = Column(Numeric(12, 2), default=Decimal('0'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    period = relationship("FinancialPeriod", back_populates="cash_flows")

class PricingStrategy(Base):
    __tablename__ = "pricing_strategies"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # spot_plus_percentage, profit_margin_target, competitive
    
    # Strategy parameters
    base_multiplier = Column(Numeric(5, 2))  # e.g., 1.30 for 30% over spot
    min_profit_margin = Column(Numeric(5, 2))  # e.g., 0.20 for 20% minimum
    max_profit_margin = Column(Numeric(5, 2))  # e.g., 0.60 for 60% maximum
    
    # Category overrides
    category_overrides = Column(JSON)  # Different strategies per category
    
    # Active status
    active = Column(Boolean, default=True)
    applied_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relationships
    pricing_updates = relationship("PricingUpdate", back_populates="strategy")

class PricingUpdate(Base):
    __tablename__ = "pricing_updates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("pricing_strategies.id"))
    coin_id = Column(Integer, ForeignKey("coins.id"))
    
    # Price changes
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    price_change = Column(Numeric(10, 2))
    change_percentage = Column(Numeric(5, 2))
    
    # Update metadata
    update_reason = Column(String(200))
    applied_at = Column(DateTime, default=datetime.utcnow)
    applied_by = Column(String(100))
    
    # Relationships
    strategy = relationship("PricingStrategy", back_populates="pricing_updates")
    # coin = relationship("Coin")  # Temporarily disabled

class FinancialMetrics(Base):
    __tablename__ = "financial_metrics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Time period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Revenue metrics
    total_revenue = Column(Numeric(12, 2), default=Decimal('0'))
    sales_revenue = Column(Numeric(12, 2), default=Decimal('0'))
    revenue_growth = Column(Numeric(5, 2), default=Decimal('0'))  # Percentage growth
    
    # Cost metrics
    total_costs = Column(Numeric(12, 2), default=Decimal('0'))
    cost_of_goods = Column(Numeric(12, 2), default=Decimal('0'))
    operating_expenses = Column(Numeric(12, 2), default=Decimal('0'))
    
    # Profit metrics
    gross_profit = Column(Numeric(12, 2), default=Decimal('0'))
    net_profit = Column(Numeric(12, 2), default=Decimal('0'))
    gross_profit_margin = Column(Numeric(5, 2), default=Decimal('0'))
    net_profit_margin = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Cash flow metrics
    operating_cash_flow = Column(Numeric(12, 2), default=Decimal('0'))
    net_cash_flow = Column(Numeric(12, 2), default=Decimal('0'))
    
    # Inventory metrics
    inventory_value = Column(Numeric(12, 2), default=Decimal('0'))
    inventory_turnover = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Calculated metrics
    return_on_investment = Column(Numeric(5, 2), default=Decimal('0'))
    return_on_assets = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient queries
    __table_args__ = (
        {'extend_existing': True}
    )

class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    category_type = Column(String(50), nullable=False)  # operating, cost_of_goods, other
    
    # Budget tracking
    monthly_budget = Column(Numeric(10, 2))
    annual_budget = Column(Numeric(12, 2))
    
    # Status
    active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = relationship("Expense", back_populates="category")

class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("expense_categories.id"), nullable=False)
    
    # Expense details
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    vendor = Column(String(200))
    reference_number = Column(String(100))  # Invoice number, receipt number, etc.
    
    # Date and period
    expense_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, paid, rejected
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Relationships
    category = relationship("ExpenseCategory", back_populates="expenses")


