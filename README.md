# Saarthi Telegram Bot

A Telegram bot designed to help users report accessibility issues in their surroundings. The bot integrates with Google's Gemini AI for natural language processing and connects to a Django backend for data persistence.

## 🚀 Features

- **User Authentication**: Complete registration and login system with JWT token management
- **Location-based Reporting**: Users can share their GPS location for accurate report positioning
- **AI-powered Analysis**: Uses Google Gemini AI to convert natural language reports into structured JSON data
- **Accessibility Focus**: Designed for reporting issues related to wheelchair access, tactile paths, and audio guidance
- **Backend Integration**: Seamlessly connects to Django REST API for data storage
- **Session Management**: Persistent user sessions with automatic token refresh

## 📋 Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Gemini API Key
- Django backend API endpoint (default: `https://saarthi-backend-xv47.onrender.com`)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AyushButola/Saarthi-bot.git
   cd Saarthi-bot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

## 🏃‍♂️ Running the Bot

Start the bot with:
```bash
python main.py
```

The bot will start running and respond to Telegram messages.

## 📖 Bot Commands

### User Management

- `/start` - Welcome message and basic instructions
- `/register` - Start the interactive registration process
- `/login <username> <password>` - Log in to your account
- `/logout` - Log out from your current session

### Reporting

- `/sendlocation` - Share your current GPS location
- `/submitreport <description>` - Submit an accessibility report at your current location

### Example Usage

1. **Register a new account:**
   ```
   /register
   ```
   Follow the interactive prompts to provide:
   - First name
   - Last name
   - Email
   - Password
   - User type (user/volunteer)
   - Accessibility needs (wheelchair, tactile paths, audio guidance)

2. **Log in:**
   ```
   /login your_username your_password
   ```

3. **Submit a report:**
   ```
   /sendlocation
   [Share your location via Telegram]
   /submitreport There's a broken wheelchair ramp near the main entrance
   ```

## 🔧 Configuration

### Backend API

The bot connects to a Django backend API. Update the following in `auth_manage.py` if needed:

```python
BASE_URL = "https://saarthi-backend-xv47.onrender.com/api/users"
```

### Gemini AI Configuration

The bot uses Google Gemini AI for natural language processing. The model configuration is in `main.py`:

```python
gemini_model = genai.GenerativeModel("gemini-2.5-flash")
```

## 📁 Project Structure

```
Saarthi-bot/
├── main.py              # Main bot logic and command handlers
├── auth_manage.py       # Authentication and session management
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (not tracked in git)
├── sessions.json       # User session storage (auto-generated)
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## 🔑 Key Components

### main.py
- **Bot Initialization**: Sets up the Telegram bot with proper handlers
- **Command Handlers**: Implements all bot commands and conversations
- **Gemini Integration**: Converts natural language to structured JSON reports
- **Location Handling**: Manages GPS location sharing and storage

### auth_manage.py
- **User Authentication**: Registration, login, and logout functionality
- **Session Management**: Persistent user sessions with JWT tokens
- **Token Refresh**: Automatic token refresh for expired sessions
- **Backend Communication**: API calls to Django backend

## 🤝 API Integration

The bot sends structured accessibility reports to the backend in this format:

```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "problem_type": "Accessibility Issue",
  "disability_types": ["wheelchair"],
  "severity": "Medium",
  "description": "Broken wheelchair ramp at entrance",
  "photo_url": null,
  "status": "Active"
}
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Session Encryption**: Encrypted session storage
- **Token Refresh**: Automatic token refresh to maintain sessions
- **Environment Variables**: Sensitive data stored in `.env` file

## 🐛 Troubleshooting

### Common Issues

1. **Bot doesn't respond**
   - Check if the bot token is correct in `.env`
   - Ensure the bot is running without errors
   - Verify internet connection

2. **Authentication fails**
   - Check backend API availability
   - Verify user credentials
   - Check `sessions.json` file permissions

3. **Gemini API errors**
   - Verify API key in `.env`
   - Check API quota and usage limits
   - Ensure network connectivity to Google services

### Debug Mode

Enable detailed logging by modifying the logging configuration in `main.py`:

```python
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG  # Change from INFO to DEBUG
)
```

## 📝 Dependencies

Key dependencies include:
- `python-telegram-bot` - Telegram Bot API wrapper
- `google-generativeai` - Google Gemini AI integration
- `requests` - HTTP client for API calls
- `python-dotenv` - Environment variable management
- `jwt` - JSON Web Token handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Python Telegram Bot](https://python-telegram-bot.org/) - Excellent Telegram bot framework
- [Google Gemini AI](https://ai.google.dev/) - Powerful AI for natural language processing
- [Saarthi Backend](https://github.com/AyushButola/Saarthi-backend) - Django backend for data persistence

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the maintainers

---

**Made with ❤️ for accessibility awareness**
