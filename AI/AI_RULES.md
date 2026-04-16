# 🤖 AI Rules for Miracle Coins CoinSync Pro

> **CRITICAL**: All AI agents working on this project MUST follow these rules for consistency, traceability, and proper memory management.

---

ALWAYS MAKE SURE YOU CHECK MEMORY BEFORE PERFORMING ANY TASK, AND UPDATING MEMORY AFTER TASK IS OVER.
## 🧠 Memory System Rules

ALWAYS MAKE SURE YOU CHECK MEMORY BEFORE PERFORMING ANY TASK, AND UPDATING MEMORY AFTER TASK IS OVER.

***   IMPORTANT ***    *** IMPORTANT ***  *** IMPORTANT ***
ALWAYS READ AND UPDATE THE RELATED TASK TO THE PROJECT YOU ARE WORKING ON, IF THERE IS NO TASK THEN CREATE ONE, AND GET CONFIRMATION FROM THE USER OF HOW THAT PART IS SUPPOSED TO WORK IF ITS NOT CLEAR

### **MANDATORY Memory Usage**
1. **ALWAYS read memory before starting any work**
   - Load `AI/memory/coinsync/state.json` for current environment
   - Load `AI/memory/coinsync/decisions.json` for architectural decisions
   - Load `AI/memory/coinsync/issues.json` for known problems
   - Load relevant `AI/memory/coinsync/features/*.json` for feature-specific rules

2. **NEVER contradict approved decisions**
   - Check `decisions.json` before making architectural choices
   - If you disagree, propose a new decision with status "proposed"
   - Never modify historical decision entries

3. **ALWAYS update memory after completing work**
   - Update `state.json` if you change environment/flags
   - Add new decisions to `decisions.json` if you make architectural choices
   - Update `issues.json` if you discover or resolve problems
   - Update relevant `features/*.json` if you change behavior
   - Append to `tasks/log.jsonl` with summary of changes

3  **IF your unsure ask, dont assume**
   - Don't just assume if your unsure, ask.

4 *** Clean up after yourself ***
   - Delete test files
   - Delete any how to or instructional mds after we are done(Not Including AI folder)



### **Memory File Structure**
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

## 📋 Task Template Rules

### **MANDATORY Task Documentation**
1. **ALWAYS create a task file** following `AI/task_template.md`
2. **Use proper task ID format**: `MC-XXX` (e.g., MC-001, MC-CAT-001)
3. **Include all required sections**:
   - Metadata (ID, owner, date, branch, dependencies)
   - Task summary (one sentence)
   - Current context
   - Goals & acceptance criteria
   - Implementation plan
   - Testing strategy
   - Deliverables
   - Review criteria
   - Memory notes
   - DevOps checklist

### **Task File Naming Convention**
- Format: `MC-XXX-descriptive-name.md`
- Examples:
  - `MC-001-auth-integration.md`
  - `MC-CAT-001-category-management.md`
  - `MC-SHP-001-shopify-integration.md`

---

## 🏗️ Development Rules

### **Code Quality Standards**
- **MANDATORY**: All code must use TypeScript with strict type checking
- **MANDATORY**: All API responses must be properly typed
- **MANDATORY**: All form data must use Zod schemas for validation
- **MANDATORY**: All database models must have corresponding TypeScript interfaces
- **MANDATORY**: All function parameters and return types must be explicitly typed
- **MANDATORY**: Use enums for all status fields and constants
- **MANDATOR***: Don't have huge pages, seperate concerns where applicable
- **MANDATOR***: When breaking up code use good naming/folder conventions and document it in task manager

### **API Design Rules**
- **MANDATORY**: Use versioned endpoints (`/api/v1/...`)
- **MANDATORY**: All endpoints must use Pydantic models for request/response validation
- **MANDATORY**: All database operations must use typed repositories
- **MANDATORY**: All business logic must be in service classes
- **MANDATORY**: All API responses must follow consistent error handling patterns

### **Database Rules**
- **MANDATORY**: All database models must use SQLAlchemy with proper typing
- **MANDATORY**: All database operations must use parameterized statements
- **MANDATORY**: All migrations must be tested
- **MANDATORY**: All database queries must be optimized

### **Frontend Rules**
- **MANDATORY**: All components must be functional components with TypeScript
- **MANDATORY**: Use React Query for all API state management
- **MANDATORY**: Implement proper error boundaries and loading states
- **MANDATORY**: All user inputs must be validated with Zod schemas
- **MANDATORY**: Use proper TypeScript generics for reusable components

---

## 🔒 Security Rules

### **Authentication & Authorization**
- **MANDATORY**: All admin routes must verify JWT tokens
- **MANDATORY**: All file uploads must be validated and typed
- **MANDATORY**: All user inputs must be sanitized
- **MANDATORY**: No secrets in memory files (use environment variables)

### **Data Protection**
- **MANDATORY**: All sensitive data must be encrypted
- **MANDATORY**: All API calls must be logged for audit purposes
- **MANDATORY**: All user actions must be tracked

---

## 🧪 Testing Rules

### **Test Coverage Requirements**
- **MANDATORY**: All new features must have corresponding tests
- **MANDATORY**: Test coverage must be above 80%
- **MANDATORY**: All API endpoints must have integration tests
- **MANDATORY**: All business logic must have unit tests
- **MANDATORY**: All TypeScript types must be tested for correctness

### **Test Types Required**
- **Unit Tests**: Individual functions/components
- **Integration Tests**: API endpoints and database
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Response times and scalability

---

## 📁 File Organization Rules

### **Backend Structure**
```
backend/app/
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
├── routers/          # API endpoints
├── utils/            # Utility functions
└── tasks/            # Background tasks
```

### **Frontend Structure**
```
frontend/
├── components/       # React components
├── pages/           # Next.js pages
├── lib/             # API client and utilities
├── types/           # TypeScript type definitions
└── styles/          # CSS and styling
```

### **AI Structure**
```
AI/
├── memory/          # Memory system files
├── tasks/           # Task documentation
└── docs/            # Project documentation
```

---

## 🚀 Deployment Rules

### **Environment Configuration**
- **MANDATORY**: All environment variables must be properly typed
- **MANDATORY**: All configuration must be validated at startup
- **MANDATORY**: All database migrations must be tested
- **MANDATORY**: All API versions must be properly documented

### **Performance Requirements**
- **MANDATORY**: All database queries must be optimized
- **MANDATORY**: All API responses must be paginated when appropriate
- **MANDATORY**: All images must be properly optimized
- **MANDATORY**: All API calls must have proper loading states

---

## 📝 Documentation Rules

### **Code Documentation**
- **MANDATORY**: All TypeScript interfaces must be documented
- **MANDATORY**: All API endpoints must have OpenAPI documentation
- **MANDATORY**: All complex business logic must be commented
- **MANDATORY**: All AI evaluation logic must be documented

### **Memory Documentation**
- **MANDATORY**: All memory changes must be documented in task logs
- **MANDATORY**: All architectural decisions must include rationale
- **MANDATORY**: All feature changes must update relevant memory files

---

## 🔄 Workflow Rules

### **Before Starting Work**
1. **Read memory files** (state.json, decisions.json, issues.json, relevant features/*.json)
2. **Check existing tasks** for similar work
3. **Create task file** following template
4. **Plan implementation** according to memory rules

### **During Development**
1. **Follow code quality standards**
2. **Update memory** as you make changes
3. **Write tests** for all new functionality
4. **Document decisions** in memory system

### **After Completing Work**
1. **Update memory files** with changes
2. **Append task log** with summary
3. **Run all tests** and fix any issues
4. **Update documentation** as needed

---

## ⚠️ Critical Reminders

### **NEVER Do These Things**
- ❌ Skip reading memory before starting work
- ❌ Contradict approved architectural decisions
- ❌ Store secrets in memory files
- ❌ Skip updating memory after changes
- ❌ Create tasks without proper documentation
- ❌ Deploy without running tests
- ❌ Modify historical decision entries

### **ALWAYS Do These Things**
- ✅ Read memory before starting
- ✅ Follow task template for all work
- ✅ Update memory after changes
- ✅ Write comprehensive tests
- ✅ Document architectural decisions
- ✅ Use proper TypeScript typing
- ✅ Follow security best practices

---

## 🎯 Project-Specific Rules

### **Miracle Coins CoinSync Pro Context**
- **Project**: Admin-only coin inventory management system
- **Backend**: FastAPI on port 13000
- **Frontend**: Next.js on port 8100
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: Stream-Line AI integration
- **AI Services**: Pricing agent, scam detection, market analysis
- **Integrations**: Shopify, GoldAPI, future eBay/eBay

### **Business Rules**
- **Individual Tracking**: Each coin tracked individually even in bulk
- **Profit Margins**: 50-60% general silver, 30% over spot, 20% under spot
- **Pricing Strategy**: 30% over spot generally, profit margin focused
- **Inventory Scale**: 5-10k coins
- **Multi-Channel**: Shopify, in-store, auction, direct sales

---

## 📞 Emergency Procedures

### **If You Break Something**
1. **Stop immediately** and assess the damage
2. **Check memory** for rollback procedures
3. **Document the issue** in issues.json
4. **Create a fix task** following template
5. **Test thoroughly** before deploying fix

### **If Memory is Inconsistent**
1. **Prefer state.json** for environment/runtime
2. **Prefer decisions.json** for policy/architecture
3. **Prefer issues.json** for problem tracking
4. **Create new issue** in issues.json if conflict persists
5. **Continue with safest assumption** until resolved

---

**Remember**: These rules exist to ensure consistency, maintainability, and proper documentation across all AI agents working on this project. Following them is not optional - it's essential for project success.

---

**Last Updated**: 2025-01-28  
**Version**: 1.0  
**Project**: Miracle Coins CoinSync Pro
