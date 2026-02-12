# Deployment Instructions

## Current Status
- ✅ Frontend: Deployed on Vercel at https://edu-sms.vercel.app
- ✅ Backend: Deployed on Render at https://edusms-ke1l.onrender.com
- ❌ Connection: Frontend cannot reach backend (404 errors)

## Issue
The frontend is making API calls but getting 404 errors because the Vercel environment variable is not set correctly.

## Solution

### Step 1: Update Vercel Environment Variables
1. Go to https://vercel.com/dashboard
2. Select your project: `edu-sms`
3. Go to **Settings** → **Environment Variables**
4. Find or add `NEXT_PUBLIC_API_URL`
5. Set value to: `https://edusms-ke1l.onrender.com`
6. Apply to: **Production**, **Preview**, and **Development**
7. Click **Save**

### Step 2: Redeploy Frontend
After updating environment variables:
1. Go to **Deployments** tab
2. Click on the latest deployment
3. Click **Redeploy** button
4. Wait for build to complete

### Step 3: Verify Backend is Running
Test backend health:
```bash
curl https://edusms-ke1l.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "EduCore API",
  "version": "1.0.0"
}
```

### Step 4: Test API Endpoints
```bash
# Test principal dashboard endpoint
curl https://edusms-ke1l.onrender.com/api/v1/principal-dashboard/staff

# Should return 401 (Unauthorized) - this is correct, means endpoint exists
```

## Local Development

To run locally with the deployed backend:

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend (if needed)
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Environment Variables Reference

### Frontend (.env)
```env
NEXT_PUBLIC_SUPABASE_URL=https://bdaiectbtlwpdkprocef.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=https://edusms-ke1l.onrender.com
```

### Backend (.env)
```env
SUPABASE_URL=https://bdaiectbtlwpdkprocef.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET_KEY=your_secret_key
DEBUG=false
CORS_ORIGINS=["https://edu-sms.vercel.app","http://localhost:3000"]
```

## Troubleshooting

### Issue: 404 Errors
- **Cause**: Frontend environment variable not set in Vercel
- **Fix**: Update `NEXT_PUBLIC_API_URL` in Vercel settings and redeploy

### Issue: CORS Errors
- **Cause**: Backend CORS not configured for frontend domain
- **Fix**: Add frontend URL to `CORS_ORIGINS` in backend environment

### Issue: 401 Unauthorized
- **Cause**: No authentication token or invalid token
- **Fix**: This is expected for protected endpoints. Login first to get token.

### Issue: Backend Sleeping (Render Free Tier)
- **Cause**: Render free tier sleeps after 15 minutes of inactivity
- **Fix**: First request will wake it up (takes 30-60 seconds)

## Next Steps After Deployment

1. **Create Test Users**: Use Supabase dashboard to create test accounts
2. **Test All Roles**: Login as Principal, Teacher, Office Admin, Parent
3. **Verify Data Flow**: Check that all CRUD operations work
4. **Monitor Logs**: Check Vercel and Render logs for errors
5. **Performance**: Monitor response times and optimize if needed

## Production Checklist

- [ ] Backend environment variables set in Render
- [ ] Frontend environment variables set in Vercel
- [ ] CORS configured correctly
- [ ] Database schema deployed to Supabase
- [ ] RLS policies enabled
- [ ] Test users created
- [ ] All 4 roles tested (Principal, Teacher, Office Admin, Parent)
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Logs monitored

## Support

If issues persist:
1. Check Vercel deployment logs
2. Check Render application logs
3. Verify Supabase connection
4. Test API endpoints directly with curl/Postman
5. Check browser console for detailed errors
