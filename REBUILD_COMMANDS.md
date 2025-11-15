# Commands to Rebuild and Push to Heroku

## Quick Rebuild and Deploy

```bash
# 1. Make sure you're in the project directory
cd "C:\Users\Muhammad Uzair\Documents\GitHub\Expiry-Date-Detector"

# 2. Build and push the container (this will rebuild from Dockerfile)
heroku container:push web --app expiry-date-detector

# 3. Release the new version
heroku container:release web --app expiry-date-detector

# 4. (Optional) View logs to verify deployment
heroku logs --tail --app expiry-date-detector
```

## All-in-One Command (PowerShell)

```powershell
heroku container:push web --app expiry-date-detector; heroku container:release web --app expiry-date-detector
```

## Verify Deployment

```bash
# Open your app in browser
heroku open --app expiry-date-detector

# Check app status
heroku ps --app expiry-date-detector

# View recent logs
heroku logs --tail --app expiry-date-detector
```

## Notes

- The `container:push` command will automatically rebuild the Docker image from your Dockerfile
- Only changed layers will be rebuilt (thanks to Docker layer caching)
- The build may take 5-10 minutes due to large ML dependencies
- After pushing, you must run `container:release` to deploy the new version

