# Deploying to Heroku using Container Registry

This guide will help you deploy your Expiry Date Detector application to Heroku using the Container Registry.

## Prerequisites

1. **Heroku CLI** installed ([Download here](https://devcenter.heroku.com/articles/heroku-cli))
2. **Docker** installed ([Download here](https://www.docker.com/products/docker-desktop))
3. A Heroku account ([Sign up here](https://signup.heroku.com/))

## Step-by-Step Deployment

### 1. Login to Heroku

```bash
heroku login
```

### 2. Login to Heroku Container Registry

```bash
heroku container:login
```

### 3. Create a Heroku App (if you haven't already)

```bash
heroku create your-app-name
```

Replace `your-app-name` with your desired app name (or leave it blank to auto-generate).

### 4. Build and Push Container

```bash
heroku container:push web
```

This command will:
- Build your Docker image using the Dockerfile
- Push it to Heroku's Container Registry
- Tag it for your app

### 5. Release the Container

```bash
heroku container:release web
```

This deploys your containerized application to Heroku.

### 6. Verify Deployment

```bash
heroku open
```

This will open your app in the browser. You should see the API root endpoint.

## Updating Your App

Whenever you make changes to your code:

1. **Build and push again:**
   ```bash
   heroku container:push web
   ```

2. **Release the new version:**
   ```bash
   heroku container:release web
   ```

## Useful Commands

- **View logs:**
  ```bash
  heroku logs --tail
  ```

- **Check app status:**
  ```bash
  heroku ps
  ```

- **Scale dynos (if needed):**
  ```bash
  heroku ps:scale web=1
  ```

- **Set environment variables (if needed):**
  ```bash
  heroku config:set KEY=value
  ```

## Important Notes

1. **First deployment may take longer** - EasyOCR needs to download model files on first run, which can take several minutes.

2. **Memory requirements** - This app uses ML models (EasyOCR, PyTorch) which require significant memory. Consider using a Performance-L dyno or higher if you encounter memory issues.

3. **Dyno types** - Free dynos are no longer available. You'll need at least a Basic dyno ($7/month) or Eco dyno ($5/month).

4. **Request timeout** - Heroku has a 30-second timeout for HTTP requests. Large images or slow processing may timeout. Consider:
   - Optimizing image size before upload
   - Using background jobs for processing
   - Increasing dyno size for better performance

## Troubleshooting

### Build fails
- Check Dockerfile syntax
- Ensure all dependencies are in requirements.txt
- Check Heroku logs: `heroku logs --tail`

### App crashes on startup
- Check logs: `heroku logs --tail`
- Verify PORT environment variable is being used
- Ensure all system dependencies are installed in Dockerfile

### Out of memory errors
- Upgrade to a larger dyno type
- Consider optimizing the EasyOCR model loading

## API Endpoints

Once deployed, your API will be available at:
- `https://your-app-name.herokuapp.com/` - Root endpoint
- `https://your-app-name.herokuapp.com/docs` - Interactive API documentation
- `https://your-app-name.herokuapp.com/upload` - POST endpoint for image upload

