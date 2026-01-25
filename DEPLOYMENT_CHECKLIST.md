# Render Deployment Checklist

## ✅ Post-Deployment Verification

### 1. Health Check
Visit: `https://your-app.onrender.com/health`
- Should return: `{"ok": true, "db": "ok"}`

### 2. Database Initialization
The database should auto-initialize on first request. Check:
- Visit: `https://your-app.onrender.com/`
- Should redirect to login page (database created)

### 3. Admin Dashboard Access
Visit: `https://your-app.onrender.com/admin`
- Should show overview page (if `ADMIN_MODE` is not set to `false`)

### 4. Model Loading
Check Render logs for:
```
Info: XGBoost model loaded with X feature columns
Info: Random Forest model loaded with X feature columns
```
If you see warnings about missing models, ensure model files are in the repo.

## 🔧 Environment Variables (Render Dashboard)

Set these in Render → Your Service → Environment:

| Variable | Value | Required |
|----------|-------|----------|
| `ADMIN_MODE` | `true` (or leave unset) | Optional |
| `SCORING_API_URL` | `https://frankscore-backend.onrender.com` | Optional |
| `TENANT_CLIENT_ID` | Your client ID | Optional |
| `TENANT_CLIENT_SECRET` | Your secret | Optional |
| `TENANT_HMAC_SECRET` | Your HMAC secret | Optional |
| `PYTHON_VERSION` | `3.10.0` | Set in render.yaml |

## ⚠️ Important Notes

### SQLite on Render
- **Ephemeral Storage**: SQLite database resets on each deploy
- **Solution**: Use PostgreSQL for production (recommended)
- **Current**: Database reinitializes on startup (data lost on restart)

### Model Files
- Ensure `models/xgb_model.joblib` and `models/random_forest.joblib` are in your Git repo
- If files are large (>100MB), consider Git LFS or cloud storage

### Static Files
- Static files (`/static`) should work automatically
- Templates should render correctly

## 🐛 Troubleshooting

### Issue: Database errors
**Solution**: Database auto-initializes. If errors persist, check file permissions.

### Issue: Models not loading
**Solution**: 
1. Check if model files exist in repo
2. Check Render logs for file paths
3. Verify model files are committed to Git

### Issue: Admin dashboard not accessible
**Solution**: 
1. Check `ADMIN_MODE` environment variable
2. Default is accessible (only blocked if `ADMIN_MODE=false`)
3. Check Render logs for errors

### Issue: External API not working
**Solution**:
1. Verify `SCORING_API_URL` is correct
2. Check `TENANT_CLIENT_ID`, `TENANT_CLIENT_SECRET`, `TENANT_HMAC_SECRET` are set
3. Check network connectivity in Render logs

## 📊 Monitoring

### Check Application Logs
Render Dashboard → Your Service → Logs

Look for:
- ✅ "XGBoost model loaded"
- ✅ "Random Forest model loaded"
- ✅ "Database initialized"
- ❌ Any error messages

### Test Endpoints
```bash
# Health check
curl https://your-app.onrender.com/health

# Login (create user first via signup)
curl -X POST https://your-app.onrender.com/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

## 🚀 Next Steps

1. **Set up PostgreSQL** (recommended for production)
2. **Configure environment variables** in Render dashboard
3. **Test full assessment flow** end-to-end
4. **Monitor admin dashboard** for model performance
5. **Set up database backups** if using SQLite temporarily

