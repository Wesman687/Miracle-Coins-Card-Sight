from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.database import get_db
from app.models.financial import (
    FinancialPeriod, CashFlow, PricingStrategy, PricingUpdate,
    FinancialMetrics, ExpenseCategory, Expense
)
from app.schemas.financial import (
    FinancialPeriodCreate, FinancialPeriodResponse, CashFlowCreate, CashFlowResponse,
    PricingStrategyCreate, PricingStrategyResponse, PricingUpdateResponse,
    FinancialMetricsResponse, PLStatementResponse, CashFlowAnalysisResponse,
    FinancialDashboardResponse, ExpenseCategoryCreate, ExpenseCategoryResponse,
    ExpenseCreate, ExpenseResponse
)
from app.services.financial_service import FinancialService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/financial", tags=["financial"])

@router.get("/dashboard", response_model=FinancialDashboardResponse)
async def get_financial_dashboard(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get comprehensive financial dashboard"""
    
    financial_service = FinancialService(db)
    
    if not start_date:
        start_date = date.today().replace(day=1)  # First day of current month
    if not end_date:
        end_date = date.today()
    
    dashboard_data = await financial_service.get_financial_dashboard(
        start_date=start_date,
        end_date=end_date
    )
    
    return dashboard_data

@router.get("/p-l", response_model=PLStatementResponse)
async def get_p_l_statement(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get P&L statement for a period"""
    
    financial_service = FinancialService(db)
    
    if not start_date:
        start_date = date.today().replace(day=1)  # First day of current month
    if not end_date:
        end_date = date.today()
    
    pl_statement = await financial_service.generate_p_l_statement(
        start_date=start_date,
        end_date=end_date
    )
    
    return pl_statement

@router.get("/cash-flow", response_model=CashFlowAnalysisResponse)
async def get_cash_flow_analysis(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    period_type: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get cash flow analysis for a period"""
    
    financial_service = FinancialService(db)
    
    if not start_date:
        start_date = date.today().replace(day=1)  # First day of current month
    if not end_date:
        end_date = date.today()
    
    cash_flow_analysis = await financial_service.get_cash_flow_analysis(
        start_date=start_date,
        end_date=end_date,
        period_type=period_type
    )
    
    return cash_flow_analysis

@router.get("/metrics", response_model=List[FinancialMetricsResponse])
async def get_financial_metrics(
    period_type: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    limit: int = Query(12, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get historical financial metrics"""
    
    metrics = db.query(FinancialMetrics).filter(
        FinancialMetrics.period_type == period_type
    ).order_by(FinancialMetrics.period_end.desc()).limit(limit).all()
    
    return metrics

@router.post("/metrics/calculate")
async def calculate_financial_metrics(
    start_date: date,
    end_date: date,
    period_type: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Calculate and store financial metrics for a period"""
    
    financial_service = FinancialService(db)
    
    metrics = await financial_service.calculate_financial_metrics(
        start_date=start_date,
        end_date=end_date,
        period_type=period_type
    )
    
    return metrics

@router.get("/pricing-strategies", response_model=List[PricingStrategyResponse])
async def get_pricing_strategies(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all pricing strategies"""
    
    query = db.query(PricingStrategy)
    if active_only:
        query = query.filter(PricingStrategy.active == True)
    
    strategies = query.order_by(PricingStrategy.created_at.desc()).all()
    return strategies

@router.post("/pricing-strategies", response_model=PricingStrategyResponse)
async def create_pricing_strategy(
    strategy_data: PricingStrategyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new pricing strategy"""
    
    financial_service = FinancialService(db)
    
    strategy = await financial_service.create_pricing_strategy(
        name=strategy_data.name,
        strategy_type=strategy_data.strategy_type,
        base_multiplier=strategy_data.base_multiplier,
        min_profit_margin=strategy_data.min_profit_margin,
        max_profit_margin=strategy_data.max_profit_margin,
        category_overrides=strategy_data.category_overrides,
        created_by=current_user.get("username", "admin")
    )
    
    return strategy

@router.post("/pricing-strategies/{strategy_id}/apply")
async def apply_pricing_strategy(
    strategy_id: int,
    coin_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Apply pricing strategy to coins"""
    
    financial_service = FinancialService(db)
    
    try:
        result = await financial_service.apply_pricing_strategy(
            strategy_id=strategy_id,
            coin_ids=coin_ids,
            applied_by=current_user.get("username", "admin")
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pricing-strategies/{strategy_id}/updates", response_model=List[PricingUpdateResponse])
async def get_pricing_updates(
    strategy_id: int,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get pricing updates for a strategy"""
    
    updates = db.query(PricingUpdate).filter(
        PricingUpdate.strategy_id == strategy_id
    ).order_by(PricingUpdate.applied_at.desc()).limit(limit).all()
    
    return updates

@router.put("/pricing-strategies/{strategy_id}", response_model=PricingStrategyResponse)
async def update_pricing_strategy(
    strategy_id: int,
    strategy_data: PricingStrategyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update a pricing strategy"""
    
    strategy = db.query(PricingStrategy).filter(PricingStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Pricing strategy not found")
    
    # Update strategy
    strategy.name = strategy_data.name
    strategy.strategy_type = strategy_data.strategy_type
    strategy.base_multiplier = strategy_data.base_multiplier
    strategy.min_profit_margin = strategy_data.min_profit_margin
    strategy.max_profit_margin = strategy_data.max_profit_margin
    strategy.category_overrides = strategy_data.category_overrides
    
    db.commit()
    db.refresh(strategy)
    
    return strategy

@router.delete("/pricing-strategies/{strategy_id}")
async def delete_pricing_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a pricing strategy (soft delete by deactivating)"""
    
    strategy = db.query(PricingStrategy).filter(PricingStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Pricing strategy not found")
    
    # Soft delete by deactivating
    strategy.active = False
    
    db.commit()
    
    return {"message": "Pricing strategy deactivated"}

@router.get("/expense-categories", response_model=List[ExpenseCategoryResponse])
async def get_expense_categories(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all expense categories"""
    
    query = db.query(ExpenseCategory)
    if active_only:
        query = query.filter(ExpenseCategory.active == True)
    
    categories = query.all()
    return categories

@router.post("/expense-categories", response_model=ExpenseCategoryResponse)
async def create_expense_category(
    category_data: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new expense category"""
    
    # Check if category name already exists
    existing = db.query(ExpenseCategory).filter(
        ExpenseCategory.name == category_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Expense category name already exists")
    
    category = ExpenseCategory(
        name=category_data.name,
        description=category_data.description,
        category_type=category_data.category_type,
        monthly_budget=category_data.monthly_budget,
        annual_budget=category_data.annual_budget
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category

@router.get("/expenses", response_model=List[ExpenseResponse])
async def get_expenses(
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get expenses with optional filters"""
    
    query = db.query(Expense)
    
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    if status:
        query = query.filter(Expense.status == status)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    expenses = query.order_by(Expense.expense_date.desc()).limit(limit).all()
    
    return expenses

@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new expense"""
    
    # Validate category exists
    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == expense_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")
    
    expense = Expense(
        category_id=expense_data.category_id,
        amount=expense_data.amount,
        description=expense_data.description,
        vendor=expense_data.vendor,
        reference_number=expense_data.reference_number,
        expense_date=expense_data.expense_date,
        period_start=expense_data.period_start,
        period_end=expense_data.period_end,
        created_by=current_user.get("username", "admin")
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    return expense

@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update expense status"""
    
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    expense.status = status
    if status == "approved":
        expense.approved_by = current_user.get("username", "admin")
        expense.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(expense)
    
    return expense


