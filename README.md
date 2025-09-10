# EcoCI - AI-Powered GitHub CI/CD Optimization Agent

[![Deployed on Smithery](https://img.shields.io/badge/Deployed%20on-Smithery-6e3bea?style=for-the-badge)](https://ecoci-mcp.smithery.ai)

EcoCI is an AI-powered agent that continuously audits your GitHub repositories and CI/CD pipelines for waste (cost + carbon), generates concrete fixes, and notifies your team with one-click approve/merge functionality.

## 🌐 MCP Server

Our MCP (Multi-Component Protocol) Server is deployed on Smithery and provides a secure, scalable API for agent communication:

🔗 **MCP Server URL**: [https://ecoci-mcp.smithery.ai](https://ecoci-mcp.smithery.ai)

### API Documentation
- [Swagger UI](https://ecoci-mcp.smithery.ai/api/docs)
- [ReDoc](https://ecoci-mcp.smithery.ai/api/redoc)

For detailed documentation about the MCP Server implementation, see [MCP_SERVER.md](MCP_SERVER.md).

## 🎯 Features

- **Automated Repository Audits**: Scans GitHub repositories for inefficiencies in CI/CD pipelines, Docker configurations, and repository settings
- **Carbon Impact Analysis**: Estimates the carbon footprint of your CI/CD processes and suggests optimizations
- **Auto-Fix PRs**: Creates targeted pull requests with specific, actionable improvements
- **Slack Integration**: Delivers concise summaries and one-click approval workflows directly to your team's Slack
- **Secure Authentication**: Utilizes Descope Outbound Apps for secure, token-based authentication with GitHub and Slack

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker
- GitHub Account with admin access to repositories
- Slack Workspace with admin permissions
- [Smithery](https://smithery.ai) account (for deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ecoci.git
   cd ecoci
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd ../frontend
   npm install
   ```

4. Configure environment variables:
   Copy the example environment file and update with your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
   
   Required environment variables:
   ```
   # GitHub
   GITHUB_APP_ID=your_github_app_id
   GITHUB_APP_PRIVATE_KEY=your_github_private_key
   GITHUB_WEBHOOK_SECRET=your_github_webhook_secret
   
   # Slack
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   SLACK_SIGNING_SECRET=your-slack-signing-secret
   
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/ecoci
   
   # Security
   SECRET_KEY=your-secret-key-here
   
   # MCP Server
   MCP_SERVER_ENABLED=True
   DATABASE_URL=sqlite:///./ecoci.db
   ```

### Running Locally

1. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at `http://localhost:3000`

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React, TypeScript, Tailwind CSS
- **Database**: SQLite (development), PostgreSQL (production)
- **CI/CD**: GitHub Actions
- **Containerization**: Docker
- **Authentication**: Descope
- **Deployment**: AWS ECS (Elastic Container Service)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/ecoci/issues).

## 📧 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - your.email@example.com

Project Link: [https://github.com/yourusername/ecoci](https://github.com/yourusername/ecoci)
