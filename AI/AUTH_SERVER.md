# Authorization integration guide

This document describes how authentication and authorization work in the Whatnot subscription / AutoPrint stack, and how **another service, desktop app, or script** should obtain and use credentials.

The design centers on a **central auth server** (Stream-line). This Next.js app mostly **proxies** auth calls or **re-validates** tokens by calling that server. **JWT verification happens only on the auth server** (this app does not verify signatures locally; it delegates to `GET /api/auth/me`).

---

## 1. Canonical auth base URL

All user session validation ultimately targets:

| Setting | Purpose |
|--------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the auth / API server (used by this repo at build/runtime). |

**Default in code** (if the env var is unset): `https://server.stream-lineai.com`

External processes should use the **same base URL** your deployed app uses, so tokens are issued and validated in one place.

---

## 2. User session token (Bearer)

### What it is

- After login (or registration, depending on backend response), the client receives a **`token`** string (treated as a session/JWT by the auth server).
- Every authenticated API call uses:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

- The browser app stores this in **`localStorage` under the key `auth_token`** (see `lib/api-client.ts`). Non-browser processes should store the token in their own secure storage.

### How validation works (conceptually)

1. Client sends `Authorization: Bearer <token>` to an endpoint.
2. This app’s API route (or the auth server) calls **`GET {API_BASE}/api/auth/me`** with the same header.
3. If the auth server returns **200** with a `user` object, the token is valid; otherwise it is invalid or expired.

There is **no local JWT secret** in this Next.js app for user tokens—validation is always **remote** via the auth server.

---

## 3. Obtaining a token (login)

### 3a. Through this Next.js app (browser / same-origin clients)

**Endpoint:** `POST /api/auth/login` (on the Next.js deployment, e.g. `https://your-app.com/api/auth/login`)

**Body (JSON):**

```json
{
  "email": "user@example.com",
  "password": "..."
}
```

The route forwards the body to **`POST {API_BASE}/api/auth/login`** and returns the auth server’s JSON as-is. On success, responses include a **`token`** field (and **`user`**) per `lib/api-client.ts`.

**CORS:** Login is restricted to an allowlist of origins (localhost ports, production domains). If your process runs in a browser from a **new origin**, you must add that origin to the allowlist in `app/api/auth/login/route.ts` (and related auth routes) or call the auth server directly (3b).

### 3b. Directly against the auth server (servers, scripts, trusted backends)

**Endpoint:** `POST {API_BASE}/api/auth/login`

Use the same JSON body. Read **`token`** from the response for subsequent `Bearer` requests.

This avoids CORS and is the usual choice for **server-to-server** or **desktop** flows that can call the API base URL directly.

---

## 4. Validating a token / loading the current user

### 4a. Auth server (recommended for backends)

**Endpoint:** `GET {API_BASE}/api/auth/me`

**Headers:**

```http
Authorization: Bearer <token>
```

**Success:** `200` with JSON containing **`user`** (shape may include `id`, `email`, `name` / `username`, `permissions`, etc.).

**Failure:** `401` (or other non-OK) if the token is missing, invalid, or expired.

This is exactly what `validateTokenServerSide` uses in `lib/server-auth.ts`.

### 4b. Through this Next.js app — `GET /api/auth/me` (proxy)

**Endpoint:** `GET https://<your-next-app>/api/auth/me`

Forward the client’s **`Authorization`** header unchanged. The route proxies to `{API_BASE}/api/auth/me` and returns the same status and body.

**CORS:** Reflects an **allowlist** of origins (same pattern as login). Not open to `*` for missing auth.

Use this when a **browser** already talks only to your Next origin and you want to avoid calling the auth server from the browser (CORS).

### 4c. Through this Next.js app — `POST /api/auth/validate-token` (machine-friendly)

**Endpoint:** `POST https://<your-next-app>/api/auth/validate-token`

**Purpose:** Intended for **other services** (e.g. license server) that send a token in the body instead of an `Authorization` header.

**Body:**

```json
{
  "session_token": "<same token string as Bearer>"
}
```

**Success (`200`):**

```json
{
  "valid": true,
  "user": {
    "user_id": 123,
    "id": 123,
    "email": "user@example.com",
    "username": "optional"
  }
}
```

**Failure:** `400` if `session_token` is missing; `401` with `{ "valid": false, "error": "..." }` for invalid/expired token.

**CORS:** `Access-Control-Allow-Origin: *` on this route (see `app/api/auth/validate-token/route.ts`), so browser or arbitrary origins can call it if needed.

Internally this still calls **`GET {API_BASE}/api/auth/me`** with `Authorization: Bearer <session_token>`.

---

## 5. Calling protected routes on this Next.js app

Most protected **app** API routes follow this pattern:

1. Read `Authorization: Bearer <token>` from the request.
2. Call `validateTokenServerSide(token)` (or `verifyToken`), which hits **`{API_BASE}/api/auth/me`**.
3. If `null`, respond **`401`**.
4. Optionally enforce **admin** (see below).

**Example consumer code (any language):**

```http
POST https://<your-next-app>/api/feedback
Authorization: Bearer <token>
Content-Type: application/json

{ "type": "suggestion", "title": "...", "description": "..." }
```

If the token is invalid, you get `401` with a JSON `detail` message.

Routes under `/api/admin/*` typically require both a **valid token** and **admin** privileges (section 6).

---

## 6. Admin authorization (not a separate token type)

Admin access is **not** a different JWT. The same **user Bearer token** is used.

After the token is validated, the app checks whether **`user.email`** is in a **hard-coded allowlist** in `lib/admin-auth.ts` (`isAdminEmail` / `checkAdminStatus`).

- If the user is authenticated but **not** in the list → **`403`** (`Admin access required` or similar).
- Some routes use `verifyAdminToken`, which combines **verify token** + **admin email check**.

**For integrators:** To use admin APIs, you must log in as an account whose email is configured as admin in that file (or the deployment’s fork of it).

**Separate from user JWT:** Some admin flows also call other systems (e.g. license server) using **`ADMIN_API_KEY`** (`X-API-Key`). That key is **server-side only** in this Next app’s environment—**not** something end users or browsers receive. Do not confuse it with the user `Bearer` token.

---

## 7. Other auth-related mechanisms (reference)

| Mechanism | Role |
|-----------|------|
| **`CrossAppAuthSDK`** (`lib/sdk/core/CrossAppAuthSDK.ts`) | Optional SDK for **cross-app** flows; uses endpoints like `/api/cross-app/auth` on a configured `apiBase`. Different from the simple `login` → `token` → `Bearer` flow above, but may still produce tokens understood by the same platform. |
| **`NOTIFICATION_API_KEY` / auth server email API** | Outbound email via auth server; `api_key` in JSON body—not used as a user session. |
| **Stripe routes** | e.g. `create-checkout-session` validates the user by calling **`{API_BASE}/api/auth/me`** with the request’s `Authorization` header before creating Stripe objects. |

---

## 8. Quick decision table for “another process”

| Your process | Suggested approach |
|--------------|-------------------|
| Backend service with no browser | Login: `POST {API_BASE}/api/auth/login`. Validate: `GET {API_BASE}/api/auth/me` with `Bearer`. |
| Service that already talks to this Next app and prefers JSON body | `POST /api/auth/validate-token` with `{ "session_token": "..." }`. |
| Browser on your Next app origin | `POST /api/auth/login`, store `token`, then `GET /api/auth/me` or call other `/api/*` with `Bearer`. |
| Browser on a different origin | Add origin to CORS allowlists in this repo **or** use auth server directly if CORS there allows it **or** proxy via your own backend. |
| Admin automation | Same `Bearer` token as user, but email must be in admin allowlist; plus server may need `ADMIN_API_KEY` when calling license server, etc. |

---

## 9. Security notes for integrators

- Treat the **token like a password**: HTTPS only, minimal logging, short-lived storage on clients where possible.
- **Refresh:** If the auth server supports refresh, use its documented flow; this repo’s web client primarily stores a single `auth_token` and revalidates via `/api/auth/me`.
- **401 handling:** Clear the stored token and re-login (or refresh) when `/api/auth/me` or protected routes return 401.

---

## 10. Source files (for maintainers)

| Concern | Location |
|---------|----------|
| Server-side token validation | `lib/server-auth.ts` |
| Admin email allowlist | `lib/admin-auth.ts` |
| Login / me / validate-token proxies | `app/api/auth/login/route.ts`, `app/api/auth/me/route.ts`, `app/api/auth/validate-token/route.ts` |
| Client token storage and login | `lib/api-client.ts` |

This document reflects the behavior of the codebase as of the last update; if routes or env names change, prefer the referenced files as the source of truth.
