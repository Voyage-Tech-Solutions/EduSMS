# EduSMS Troubleshooting Guide

## Current Errors & Solutions

### 1. CORS Policy Error ❌

**Error:**
```
Access to fetch at 'https://edusms-ke1l.onrender.com/schools/classes' from origin 'https://edu-sms.vercel.app' has been blocked by CORS policy
```

**Root Cause:** Backend CORS configuration doesn't include the deployed frontend URL.

**Solution:**
1. Update `.env` file with all allowed origins:
```env
CORS_ORIGINS=["http://localhost:3000","https://edu-sms.vercel.app","https://edusms-ke1l.onrender.com"]
```

2. Redeploy backend to Render with updated environment variables

3. Verify CORS headers in browser DevTools Network tab:
   - `Access-Control-Allow-Origin` should be present
   - `Access-Control-Allow-Credentials: true`

---

### 2. 404 Not Found Errors ❌

**Errors:**
```
GET https://edu-sms.vercel.app/api/v1/fees/summary 404
GET https://edu-sms.vercel.app/api/v1/fees/invoices? 404
GET https://edu-sms.vercel.app/api/v1/documents/documents? 404
```

**Root Cause:** Frontend is calling wrong API URL (Vercel URL instead of Render backend URL).

**Solution:**
Check frontend `.env` file:
```env
NEXT_PUBLIC_API_URL=https://edusms-ke1l.onrender.com/api/v1
```

NOT:
```env
NEXT_PUBLIC_API_URL=https://edu-sms.vercel.app/api/v1  ❌
```

---

### 3. Select Component Empty Value Error ❌

**Error:**
```
Uncaught Error: A <Select.Item /> must have a value prop that is not an empty string
```

**Root Cause:** React Select component receiving empty string as value.

**Solution:**
Find Select.Item components and ensure they have valid values:

```tsx
// ❌ Bad
<SelectItem value="">Select option</SelectItem>

// ✅ Good
<SelectItem value="placeholder" disabled>Select option</SelectItem>
// OR
{options.length > 0 && options.map(opt => (
  <SelectItem key={opt.id} value={opt.id}>{opt.name}</SelectItem>
))}
```

---

### 4. JSON Parse Error ❌

**Error:**
```
Uncaught (in promise) SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

**Root Cause:** API returning HTML (404 page) instead of JSON.

**Solution:**
1. Verify API endpoints exist in backend
2. Check authentication tokens are valid
3. Ensure correct API base URL is configured

---

## Deployment Checklist

### Backend (Render)

- [ ] Environment variables set:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `JWT_SECRET_KEY`
  - `CORS_ORIGINS` (JSON array string)
  - `DEBUG=false`

- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Health check: `https://edusms-ke1l.onrender.com/health`

### Frontend (Vercel)

- [ ] Environment variables set:
  - `NEXT_PUBLIC_API_URL=https://edusms-ke1l.onrender.com/api/v1`
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

- [ ] Build command: `npm run build`
- [ ] Output directory: `.next`
- [ ] Install command: `npm install`

---

## Quick Fixes

### Fix CORS Immediately

**On Render Dashboard:**
1. Go to your backend service
2. Environment → Add Variable
3. Key: `CORS_ORIGINS`
4. Value: `["http://localhost:3000","https://edu-sms.vercel.app"]`
5. Save & Redeploy

### Fix API URL in Frontend

**On Vercel Dashboard:**
1. Go to your project settings
2. Environment Variables
3. Edit `NEXT_PUBLIC_API_URL`
4. Set to: `https://edusms-ke1l.onrender.com/api/v1`
5. Redeploy

---

## Testing After Fixes

### 1. Test CORS
```bash
curl -H "Origin: https://edu-sms.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://edusms-ke1l.onrender.com/api/v1/health
```

Should return CORS headers.

### 2. Test API Connectivity
```bash
curl https://edusms-ke1l.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "app": "EduCore API",
  "version": "1.0.0"
}
```

### 3. Test Frontend API Calls
Open browser console on `https://edu-sms.vercel.app` and run:
```javascript
console.log(process.env.NEXT_PUBLIC_API_URL)
```

Should output: `https://edusms-ke1l.onrender.com/api/v1`

---

## Common Issues

### Issue: "Failed to fetch"
- **Check:** Is backend running? Visit health endpoint
- **Check:** Is API URL correct in frontend?
- **Check:** Are CORS headers present?

### Issue: "401 Unauthorized"
- **Check:** Is user logged in?
- **Check:** Is JWT token valid?
- **Check:** Is token being sent in Authorization header?

### Issue: "500 Internal Server Error"
- **Check:** Backend logs on Render
- **Check:** Database connection (Supabase)
- **Check:** Environment variables are set

---

## Monitoring

### Backend Logs (Render)
```
https://dashboard.render.com → Your Service → Logs
```

### Frontend Logs (Vercel)
```
https://vercel.com → Your Project → Deployments → View Function Logs
```

### Browser DevTools
- Network tab: Check request/response
- Console tab: Check JavaScript errors
- Application tab: Check localStorage for tokens

---

## Emergency Rollback

If deployment breaks:

**Render:**
```
Dashboard → Service → Manual Deploy → Select previous commit
```

**Vercel:**
```
Dashboard → Deployments → Previous deployment → Promote to Production
```
