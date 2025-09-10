# Deployment Guide

## Deploying to Smithery

1. **Prepare your repository**
   - Ensure all your code is committed and pushed to your GitHub repository
   - Make sure all required environment variables are documented in `.env.example`

2. **Deploy to Smithery**
   - Go to [Smithery](https://smithery.ai/new)
   - Connect your GitHub account
   - Select your repository (`ecoci`)
   - Configure the deployment:
     - **Build Command**: `pip install -r backend/requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Environment Variables**: Copy from your `.env` file
   - Click "Deploy"

3. **Get your Smithery URL**
   - After deployment is complete, you'll receive a URL like `https://your-app-name.smithery.ai`
   - This is your MCP server endpoint

4. **Update Webhook URLs**
   - Update your GitHub webhook to point to: `https://your-app-name.smithery.ai/api/v1/webhooks/github`
   - Update your Slack app's Event Subscriptions to point to: `https://your-app-name.smithery.ai/api/v1/webhooks/slack`

## Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/ecoci.git
cd ecoci

# Set up the backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the server
uvicorn app.main:app --reload
```

## Environment Variables

See [.env.example](.env.example) for all required environment variables.
