# MC-006: Stream-Line Authentication Integration

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-006 |
| **Owner / Agent** | BuilderAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/auth-integration |
| **Dependencies** | MC-001 (System Scaffolding) |
| **Related Issues** | Authentication Integration |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary
> Replace mock JWT authentication with real Stream-Line authentication integration for secure admin-only access.

---

## 2️⃣ 🧩 Current Context
The system currently uses mock JWT authentication for development purposes. The backend has a placeholder `verify_admin_token` function that returns a mock admin user. The frontend stores a mock token in localStorage.

**Current State:**
- Backend: Mock JWT verification in `main.py`
- Frontend: Mock token handling in `lib/api.ts`
- Database: User authentication not connected to Stream-Line
- Security: No real authentication validation

**Why This Task is Needed:**
- Production deployment requires real authentication
- Admin-only access must be properly enforced
- User management needs Stream-Line integration
- Security audit requires proper JWT validation

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Integrate with Stream-Line JWT authentication
- [ ] Verify `user.isAdmin` status from JWT token
- [ ] Implement proper token validation and refresh
- [ ] Secure all admin-only endpoints
- [ ] Handle authentication errors gracefully

### Acceptance Criteria
- [ ] Works with real Stream-Line JWT tokens
- [ ] Passes TypeScript type checks and linting
- [ ] All endpoints properly authenticated
- [ ] Admin-only access enforced
- [ ] Token expiration handled correctly
- [ ] Authentication errors return proper HTTP status codes
- [ ] Frontend handles authentication state properly
- [ ] Comprehensive test coverage for auth flows

---

## 4️⃣ 🏗️ Implementation Plan

### Backend Implementation
1. **Create JWT Service** (`app/services/jwt_service.py`)
   - Implement JWT token validation
   - Parse Stream-Line user claims
   - Verify admin status
   - Handle token expiration

2. **Update Authentication Middleware** (`main.py`)
   - Replace mock `verify_admin_token` with real JWT validation
   - Add proper error handling for invalid tokens
   - Implement token refresh logic

3. **Add User Model** (`app/models.py`)
   - Create User model for Stream-Line integration
   - Store user information from JWT claims
   - Link users to audit logs

4. **Update Repositories** (`app/repositories_typed.py`)
   - Add UserRepository for user management
   - Update audit logging to use real user IDs

### Frontend Implementation
1. **Update API Client** (`lib/api.ts`)
   - Implement real JWT token handling
   - Add token refresh logic
   - Handle authentication errors

2. **Create Auth Context** (`contexts/AuthContext.tsx`)
   - Manage authentication state
   - Provide login/logout functionality
   - Handle token expiration

3. **Update Login Page** (`pages/login.tsx`)
   - Integrate with Stream-Line login flow
   - Handle authentication responses
   - Redirect to dashboard on success

4. **Add Auth Guards** (`components/AuthGuard.tsx`)
   - Protect admin-only routes
   - Redirect unauthenticated users
   - Handle loading states

### Configuration
1. **Environment Variables** (`.env`)
   - Add Stream-Line JWT public key
   - Configure authentication endpoints
   - Set token refresh settings

2. **Type Definitions** (`types/auth.ts`)
   - Define JWT token structure
   - Create user interface types
   - Add authentication state types

---

## 5️⃣ 🧪 Testing

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | JWT service validation | Valid token, invalid token, expired token, malformed token |
| **Unit** | User admin status check | Admin user, non-admin user, missing admin claim |
| **Integration** | API endpoint authentication | Authenticated request, unauthenticated request, expired token |
| **Integration** | Token refresh flow | Successful refresh, failed refresh, network error |
| **End-to-end** | Login flow | Successful login, failed login, admin access, non-admin access |
| **End-to-end** | Protected routes | Access with valid token, access without token, expired token |

### Test Data
```json
{
  "valid_admin_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "valid_user_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "expired_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "invalid_token": "invalid.jwt.token"
}
```

---

## 6️⃣ 📂 Deliverables

### Backend Files
- `app/services/jwt_service.py` - JWT validation service
- `app/models/user.py` - User model for Stream-Line integration
- `app/repositories/user_repository.py` - User data access
- `app/schemas/auth.py` - Authentication schemas
- `app/middleware/auth.py` - Authentication middleware
- `tests/test_auth.py` - Authentication tests

### Frontend Files
- `contexts/AuthContext.tsx` - Authentication context
- `components/AuthGuard.tsx` - Route protection component
- `hooks/useAuth.ts` - Authentication hook
- `types/auth.ts` - Authentication type definitions
- `lib/auth.ts` - Authentication utilities
- `__tests__/auth.test.tsx` - Authentication tests

### Configuration Files
- `.env.example` - Updated environment variables
- `backend/env.example` - Backend environment variables
- `docs/auth-integration.md` - Authentication documentation

### Documentation
- API documentation updates for authentication
- Frontend authentication flow documentation
- Security considerations and best practices

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [ ] TypeScript types properly defined for all auth components
- [ ] Error handling comprehensive and user-friendly
- [ ] Code follows established patterns and conventions
- [ ] Proper logging for authentication events
- [ ] Security best practices implemented

### Functionality
- [ ] JWT token validation works correctly
- [ ] Admin status verification accurate
- [ ] Token refresh flow functional
- [ ] Authentication errors handled gracefully
- [ ] Frontend authentication state managed properly

### Security
- [ ] No sensitive data exposed in logs
- [ ] Proper HTTP status codes for auth failures
- [ ] Token storage secure (httpOnly cookies recommended)
- [ ] CSRF protection implemented
- [ ] Rate limiting on authentication endpoints

### Testing
- [ ] Unit tests cover all authentication logic
- [ ] Integration tests verify API authentication
- [ ] End-to-end tests cover complete auth flows
- [ ] Test coverage above 90% for auth components
- [ ] Security tests verify proper access control

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "authentication": {
    "provider": "streamline",
    "method": "jwt",
    "admin_claim": "isAdmin",
    "user_claim": "user_id",
    "token_refresh": "enabled",
    "cookie_storage": "recommended"
  },
  "security": {
    "jwt_validation": "required",
    "admin_verification": "mandatory",
    "token_expiration": "handled",
    "error_responses": "standardized"
  },
  "integration_points": {
    "backend": "jwt_service",
    "frontend": "auth_context",
    "database": "user_model",
    "api": "auth_middleware"
  }
}
```

### Key Implementation Notes
- Stream-Line JWT tokens contain `isAdmin` boolean claim
- User ID is available in `user_id` claim
- Token expiration should be handled gracefully
- Admin-only endpoints must verify `isAdmin` status
- Frontend should store tokens securely (consider httpOnly cookies)

### Reusable Patterns
- JWT validation service pattern
- Authentication context pattern
- Route protection pattern
- Token refresh pattern
- Error handling pattern

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [ ] Verify `user.isAdmin` before any write operation
- [ ] Use versioned endpoints (/api/v1/...)
- [ ] Commit authentication changes separately
- [ ] Keep PRs atomic and type-safe
- [ ] Log authentication events using structured logging
- [ ] Run authentication tests before merging
- [ ] Update API documentation for auth endpoints
- [ ] Ensure environment variables are properly typed
- [ ] Validate JWT token structure matches Stream-Line format
- [ ] Test with real Stream-Line tokens in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Task Version:** v1.0  
**Date:** 2025-01-27




