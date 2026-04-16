-- Migration: Add Financial Management Tables
-- Description: Creates tables for financial management, P&L statements, cash flow, and pricing strategies
-- Date: 2025-01-27

-- Financial Periods Table
CREATE TABLE IF NOT EXISTS financial_periods (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    sales_revenue DECIMAL(12,2) DEFAULT 0,
    other_revenue DECIMAL(12,2) DEFAULT 0,
    cost_of_goods DECIMAL(12,2) DEFAULT 0,
    operating_expenses DECIMAL(12,2) DEFAULT 0,
    other_expenses DECIMAL(12,2) DEFAULT 0,
    gross_profit DECIMAL(12,2) DEFAULT 0,
    net_profit DECIMAL(12,2) DEFAULT 0,
    profit_margin DECIMAL(5,2) DEFAULT 0,
    notes TEXT,
    adjustments JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cash Flow Table
CREATE TABLE IF NOT EXISTS cash_flow (
    id SERIAL PRIMARY KEY,
    period_id INTEGER REFERENCES financial_periods(id),
    operating_cash_flow DECIMAL(12,2) DEFAULT 0,
    investing_cash_flow DECIMAL(12,2) DEFAULT 0,
    financing_cash_flow DECIMAL(12,2) DEFAULT 0,
    net_cash_flow DECIMAL(12,2) DEFAULT 0,
    beginning_cash DECIMAL(12,2) DEFAULT 0,
    ending_cash DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pricing Strategies Table
CREATE TABLE IF NOT EXISTS pricing_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL CHECK (strategy_type IN ('spot_plus_percentage', 'profit_margin_target', 'competitive')),
    base_multiplier DECIMAL(5,2),
    min_profit_margin DECIMAL(5,2),
    max_profit_margin DECIMAL(5,2),
    category_overrides JSONB,
    active BOOLEAN DEFAULT TRUE,
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Pricing Updates Table
CREATE TABLE IF NOT EXISTS pricing_updates (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES pricing_strategies(id),
    coin_id BIGINT NOT NULL REFERENCES coins(id),
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    price_change DECIMAL(10,2),
    change_percentage DECIMAL(5,2),
    update_reason VARCHAR(200),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100)
);

-- Financial Metrics Table
CREATE TABLE IF NOT EXISTS financial_metrics (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    sales_revenue DECIMAL(12,2) DEFAULT 0,
    revenue_growth DECIMAL(5,2) DEFAULT 0,
    total_costs DECIMAL(12,2) DEFAULT 0,
    cost_of_goods DECIMAL(12,2) DEFAULT 0,
    operating_expenses DECIMAL(12,2) DEFAULT 0,
    gross_profit DECIMAL(12,2) DEFAULT 0,
    net_profit DECIMAL(12,2) DEFAULT 0,
    gross_profit_margin DECIMAL(5,2) DEFAULT 0,
    net_profit_margin DECIMAL(5,2) DEFAULT 0,
    operating_cash_flow DECIMAL(12,2) DEFAULT 0,
    net_cash_flow DECIMAL(12,2) DEFAULT 0,
    inventory_value DECIMAL(12,2) DEFAULT 0,
    inventory_turnover DECIMAL(5,2) DEFAULT 0,
    return_on_investment DECIMAL(5,2) DEFAULT 0,
    return_on_assets DECIMAL(5,2) DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Expense Categories Table
CREATE TABLE IF NOT EXISTS expense_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category_type VARCHAR(50) NOT NULL CHECK (category_type IN ('operating', 'cost_of_goods', 'other')),
    monthly_budget DECIMAL(10,2),
    annual_budget DECIMAL(12,2),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES expense_categories(id),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    description TEXT,
    vendor VARCHAR(200),
    reference_number VARCHAR(100),
    expense_date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'paid', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_financial_periods_type ON financial_periods(period_type);
CREATE INDEX IF NOT EXISTS idx_financial_periods_start ON financial_periods(start_date);
CREATE INDEX IF NOT EXISTS idx_financial_periods_end ON financial_periods(end_date);

CREATE INDEX IF NOT EXISTS idx_cash_flow_period_id ON cash_flow(period_id);

CREATE INDEX IF NOT EXISTS idx_pricing_strategies_name ON pricing_strategies(name);
CREATE INDEX IF NOT EXISTS idx_pricing_strategies_type ON pricing_strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_pricing_strategies_active ON pricing_strategies(active);

CREATE INDEX IF NOT EXISTS idx_pricing_updates_strategy_id ON pricing_updates(strategy_id);
CREATE INDEX IF NOT EXISTS idx_pricing_updates_coin_id ON pricing_updates(coin_id);
CREATE INDEX IF NOT EXISTS idx_pricing_updates_applied_at ON pricing_updates(applied_at);

CREATE INDEX IF NOT EXISTS idx_financial_metrics_period_type ON financial_metrics(period_type);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_period_start ON financial_metrics(period_start);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_period_end ON financial_metrics(period_end);

CREATE INDEX IF NOT EXISTS idx_expense_categories_name ON expense_categories(name);
CREATE INDEX IF NOT EXISTS idx_expense_categories_type ON expense_categories(category_type);
CREATE INDEX IF NOT EXISTS idx_expense_categories_active ON expense_categories(active);

CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_expenses_expense_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);
CREATE INDEX IF NOT EXISTS idx_expenses_period_start ON expenses(period_start);
CREATE INDEX IF NOT EXISTS idx_expenses_period_end ON expenses(period_end);

-- Insert Default Expense Categories
INSERT INTO expense_categories (name, category_type, description) VALUES
('Rent', 'operating', 'Store rent and utilities'),
('Salaries', 'operating', 'Employee salaries and benefits'),
('Marketing', 'operating', 'Advertising and promotional expenses'),
('Insurance', 'operating', 'Business insurance premiums'),
('Professional Services', 'operating', 'Legal, accounting, and consulting fees'),
('Equipment', 'operating', 'Equipment purchases and maintenance'),
('Supplies', 'operating', 'Office supplies and materials'),
('Travel', 'operating', 'Business travel expenses'),
('Coin Acquisition', 'cost_of_goods', 'Cost of purchasing coins and bullion'),
('Shipping', 'cost_of_goods', 'Shipping and handling costs'),
('Packaging', 'cost_of_goods', 'Packaging materials'),
('Other', 'other', 'Miscellaneous expenses')
ON CONFLICT (name) DO NOTHING;

-- Insert Default Pricing Strategies
INSERT INTO pricing_strategies (name, strategy_type, base_multiplier, min_profit_margin, max_profit_margin, created_by) VALUES
('Standard Silver Pricing', 'spot_plus_percentage', 1.30, 0.20, 0.60, 'system'),
('Premium Collector Pricing', 'profit_margin_target', NULL, 0.50, 1.00, 'system'),
('Bulk Pricing', 'spot_plus_percentage', 1.15, 0.15, 0.40, 'system'),
('Competitive Pricing', 'competitive', NULL, 0.10, 0.80, 'system')
ON CONFLICT DO NOTHING;

-- Add Comments for Documentation
COMMENT ON TABLE financial_periods IS 'Financial periods for P&L statements and reporting';
COMMENT ON TABLE cash_flow IS 'Cash flow analysis for financial periods';
COMMENT ON TABLE pricing_strategies IS 'Pricing strategies for dynamic pricing';
COMMENT ON TABLE pricing_updates IS 'History of pricing updates applied to coins';
COMMENT ON TABLE financial_metrics IS 'Aggregated financial metrics for different time periods';
COMMENT ON TABLE expense_categories IS 'Categories for expense tracking and budgeting';
COMMENT ON TABLE expenses IS 'Individual expense records';

COMMENT ON COLUMN financial_periods.profit_margin IS 'Net profit margin percentage';
COMMENT ON COLUMN pricing_strategies.base_multiplier IS 'Base multiplier for spot pricing (e.g., 1.30 for 30% over spot)';
COMMENT ON COLUMN pricing_strategies.min_profit_margin IS 'Minimum profit margin (e.g., 0.20 for 20%)';
COMMENT ON COLUMN pricing_strategies.max_profit_margin IS 'Maximum profit margin (e.g., 0.60 for 60%)';
COMMENT ON COLUMN pricing_strategies.category_overrides IS 'Category-specific pricing overrides';
COMMENT ON COLUMN pricing_updates.price_change IS 'Absolute price change amount';
COMMENT ON COLUMN pricing_updates.change_percentage IS 'Percentage change in price';
COMMENT ON COLUMN expenses.status IS 'Expense approval status: pending, approved, paid, rejected';
COMMENT ON COLUMN expenses.reference_number IS 'Invoice number, receipt number, or other reference';
COMMENT ON COLUMN expenses.period_start IS 'Start of the accounting period this expense belongs to';
COMMENT ON COLUMN expenses.period_end IS 'End of the accounting period this expense belongs to';


