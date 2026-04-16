# Miracle Coins Integration with Streamline AI Auth

## Overview
Miracle Coins will use the same authentication system as Streamline AI, allowing seamless user management across both platforms.

## Database Setup ✅
- **Database Name**: `Miracle-Coins`
- **User**: `Miracle-Coins`
- **Password**: `your_db_password_here`
- **Host**: `localhost:5432`

## Domain Strategy ✅
**Recommendation**: Use separate domain `miracle-coins.com`

### Why this works:
1. **Cross-domain cookies**: Your auth system uses cookies without domain restrictions
2. **JWT tokens**: Work seamlessly across domains
3. **CORS configured**: Added support for miracle-coins.com and subdomains
4. **No conflicts**: Each domain can have its own branding while sharing auth

## Authentication Flow
1. User logs in on either `stream-lineai.com` or `miracle-coins.com`
2. JWT token is created with shared `ENCRYPTION_KEY`
3. Cookie is set without domain restriction
4. User can access both platforms with same login

## Configuration Files
- `miracle-coins.env.example` - Environment configuration for Miracle Coins
- Updated `backend/main.py` - CORS configuration for miracle-coins.com domains

## Next Steps
1. **Frontend Setup**: Create Miracle Coins frontend that calls your Streamline backend
2. **Domain Setup**: Configure DNS for miracle-coins.com to point to your server
3. **SSL Certificates**: Set up SSL for miracle-coins.com
4. **Email Setup**: Configure email accounts for Miracle Coins

## API Endpoints
Your Miracle Coins frontend can use these Streamline AI endpoints:
- `POST /api/login` - User authentication
- `POST /api/logout` - User logout
- `GET /api/user/me` - Get current user info
- All other Streamline AI API endpoints

## Database Schema
The Miracle Coins database will be separate but can use the same User model structure if needed. You can:
1. Use completely separate models for coin-specific data
2. Reference users by ID from the main Streamline database
3. Create coin-specific user extensions

## Security Notes
- Same `ENCRYPTION_KEY` ensures JWT compatibility
- CORS properly configured for cross-domain requests
- Cookies work across domains without security issues
- Each platform can have separate admin controls
