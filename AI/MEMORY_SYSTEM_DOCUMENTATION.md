# 📁 Memory System Structure Documentation
> **Project**: Miracle Coins CoinSync Pro  
> **Date**: 2025-01-28  
> **Status**: Updated and Corrected  

---

## 🎯 **Corrected Memory File Structure**

The memory system is located in `AI/memory/coinsync/` with the following structure:

```
AI/memory/coinsync/
├── state.json              # Current environment & flags
├── decisions.json          # Architectural decisions  
├── issues.json             # Known problems
├── features/
│   ├── pricing.json        # Pricing system rules
│   ├── marketplaces.json   # Shopify/eBay integration
│   ├── categories.json     # Category management
│   ├── collections.json    # Collection management
│   ├── inventory.json      # Inventory tracking
│   ├── sales.json          # Sales management
│   ├── alerts.json         # Alert system
│   └── images.json         # Image system rules
└── tasks/
    └── log.jsonl          # Chronological task log
```

---

## 📋 **Memory File Contents**

### **Core Memory Files**

#### **`state.json`** - System State
- **Purpose**: Current environment configuration and runtime flags
- **Contents**: 
  - Project configuration (ports, database, Redis)
  - Authentication settings
  - Channel configurations (Shopify, eBay, etc.)
  - Business rules and profit margins
  - AI services status
  - Database migration status
- **Last Updated**: 2025-01-28T01:30:00Z

#### **`decisions.json`** - Architectural Decisions
- **Purpose**: Approved architectural decisions and their rationale
- **Contents**:
  - Decision ID, title, rationale
  - Status (approved/completed/resolved)
  - Decision date and impacts
  - Key decisions include:
    - Individual coin tracking
    - Profit margin strategy
    - Multi-channel sales
    - Collections-only system
    - Flexible pricing strategies
- **Last Updated**: 2025-01-28

#### **`issues.json`** - Known Problems
- **Purpose**: Track known issues, technical debt, and performance considerations
- **Contents**:
  - Known issues with priority and status
  - Technical debt items
  - Performance considerations
  - Solutions and resolutions
- **Last Updated**: 2025-01-28

### **Feature-Specific Memory Files**

#### **`features/pricing.json`** - Pricing System
- Default multipliers and strategies
- Profit margin configurations
- AI evaluation settings
- Spot price integration

#### **`features/collections.json`** - Collection Management
- Collections-only system configuration
- Shopify integration settings
- Pricing strategy per collection
- UI features and API endpoints

#### **`features/inventory.json`** - Inventory Management
- Individual tracking settings
- Multi-location support
- Dead stock analysis criteria
- Bulk operations configuration

#### **`features/sales.json`** - Sales Management
- Sales channel configurations
- Revenue forecasting settings
- Sales tracking rules
- Customer information handling

#### **`features/alerts.json`** - Alert System
- Alert rule types and configurations
- Notification channels
- Product-specific thresholds
- Action types and settings

#### **`features/images.json`** - Image System
- Upload process workflow
- Image processing features
- Storage configuration
- Database schema for images

#### **`features/marketplaces.json`** - Marketplace Integration
- Shopify integration details
- eBay configuration (planned)
- Webhook handling
- Sync data mappings

#### **`features/categories.json`** - Category Management
- Auto-SKU generation rules
- Category prefixes and codes
- Metadata system configuration
- Shopify integration settings

---

## 🔧 **Memory System Usage**

### **Reading Memory Files**
```bash
# Core system files
AI/memory/coinsync/state.json
AI/memory/coinsync/decisions.json  
AI/memory/coinsync/issues.json

# Feature-specific files
AI/memory/coinsync/features/pricing.json
AI/memory/coinsync/features/collections.json
AI/memory/coinsync/features/inventory.json
# ... etc
```

### **Updating Memory Files**
- **State changes**: Update `state.json`
- **New decisions**: Add to `decisions.json`
- **Issues found/resolved**: Update `issues.json`
- **Feature changes**: Update relevant `features/*.json`
- **Task completion**: Append to `tasks/log.jsonl`

---

## ⚠️ **Important Notes**

1. **File Locations**: Memory files are directly in `AI/memory/coinsync/`, NOT in a `system/` subdirectory
2. **Consistency**: All AI agents must use the same memory file structure
3. **Updates**: Always update memory files after making changes
4. **Decisions**: Never contradict approved decisions in `decisions.json`
5. **Issues**: Document all problems in `issues.json` for tracking

---

## 🚀 **Next Steps**

1. **Verify Structure**: Confirm all memory files exist in correct locations
2. **Update Documentation**: Ensure all references use correct paths
3. **Test Access**: Verify AI agents can read memory files correctly
4. **Maintain Consistency**: Keep memory files synchronized across all agents

---

**Documentation Updated**: 2025-01-28  
**Status**: Corrected and Complete  
**Next Review**: After next major system change
