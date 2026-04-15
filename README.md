# AI Multi-Code Converter

A modern, AI-powered code converter that translates code between 30+ programming languages using Groq AI.

## ✨ Features

- 🚀 **30+ Programming Languages**: Convert between Python, JavaScript, Java, C++, Go, Rust, and many more
- ✨ **AI-Powered Conversion**: Uses Groq API with Llama 3.3 70B for intelligent code translation
- 🎯 **Smart Language Detection**: Validates source language to prevent conversion errors
- 📊 **Conversion History**: Track all your code conversions with detailed history
- 🎨 **Modern UI**: Beautiful, responsive React interface with dark mode
- 🔐 **Secure Authentication**: User registration and login with JWT tokens
- 📈 **Statistics Dashboard**: View your conversion stats and most-used languages
- 🎓 **Video Tutorials**: Integrated learning resources for each language
- ⚡ **Fast & Reliable**: Optimized for speed with intelligent token management

## 🛠️ Tech Stack

### Backend
- **FastAPI** for high-performance REST API
- **SQLite** for data persistence
- **Groq API** for AI code conversion
- **JWT Authentication** for secure user sessions

### Frontend
- **React 18** with modern hooks
- **Vite** for lightning-fast development
- **Lucide Icons** for beautiful UI elements
- **CSS3** with custom properties for theming

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Groq API key ([Get one here](https://console.groq.com/))

## 🚀 Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd AI-MULTI-CODE-CONVERTOR
```

### Environment Configuration

Create a `.env` file in the root directory:

```bash
GROQ_API_KEY=your_api_key_here
```

3. Run the backend server:
```bash
python backend.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will start on `http://localhost:3000`

## Usage

1. **Register/Login**: Create an account or log in with existing credentials
2. **Select Languages**: Choose source and target programming languages
3. **Paste Code**: Enter your source code in the left panel
4. **Convert**: Click the "Convert Code" button
5. **Review**: See the AI-converted code in the right panel
6. **Copy**: Copy the converted code to your clipboard

## Supported Languages

Python, Java, JavaScript, TypeScript, C++, C#, C, Go, Rust, Swift, Kotlin, Ruby, PHP, Dart, Scala, R, MATLAB, Julia, Perl, Haskell, Lua, Objective-C, Visual Basic, F#, Elixir, Clojure, Groovy, Assembly, Shell, PowerShell, SQL

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Verify token

### Conversion
- `POST /api/convert` - Convert code
- `GET /api/history` - Get conversion history
- `GET /api/history/{id}` - Get specific conversion

### Stats
- `GET /api/stats` - Get user statistics
- `GET /api/videos` - Get video tutorials
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update preferences

## Environment Variables

### Backend (.env)
```
OPENROUTER_API_KEY=your_api_key_here
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000/api
```

## Development

### Backend Development
```bash
# Run with auto-reload
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Build for Production
```bash
cd frontend
npm run build
```

## Database

The application uses SQLite with the following tables:
- `users` - User accounts
- `sessions` - Authentication sessions
- `conversion_history` - Code conversion records
- `user_preferences` - User settings
- `video_tutorials` - Programming tutorials

## Screenshots

### Login Page
Premium glassmorphism design with animated background and smooth transitions.

### Dashboard
Modern code editor interface with real-time conversion and statistics.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues or questions, please open an issue on GitHub.

## 🙏 Credits

- Groq for providing AI API access
- React team for the amazing framework
- FastAPI for the excellent Python web framework

## License

MIT License - feel free to use this project for personal or commercial purposes.
