# ORION OS Navigator

## 📸 Screenshots

### 🔐 Preview 1
![Command Pallete](Screenshot/1.png)

---




### 💽 Preview 2  
![Extension](Screenshot/2.png)

Advanced AI Command Center with modern UI and system control capabilities.

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **pnpm** package manager
- **Python** (3.8 or higher) - for the Python backend script
- **Git** (optional)

### Installation & Running

#### 1. Install Dependencies

First, install all Node.js dependencies:

```bash
pnpm install
```

#### 2. Run the Next.js Frontend

Start the development server:

```bash
pnpm dev
```

The application will be available at: **http://localhost:3000**

#### 3. Run the Python Backend API Server

**⚠️ IMPORTANT:** The backend API server is **required** for all command functionality!

**Windows:**
```bash
scripts\start_backend.bat
```

**Or manually:**
```bash
python scripts/api_server.py
```

The API server will run on **http://localhost:5000** and must stay running while using the application.

**Note:** The server will automatically install required dependencies on first run. For volume control on Windows, you may need to install:

```bash
pip install pycaw comtypes
```

## 📋 Available Commands

### Frontend (Next.js)

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

### Python Backend API Server

The Python API server (`api_server.py`) provides:
- **Command processing** - All system commands
- **Voice recognition** - Speech-to-text
- **Text-to-speech** - Voice responses
- **System control** - Volume, screenshots, processes, files
- **AI integration** - Gemini AI chat and vision
- **Cross-platform support** - Windows, Mac, Linux

**Standalone Application:** You can also run `orion_os_navigator.py` as a standalone GUI application with full UI.

## 🎨 Features

- **Modern UI** with glass morphism effects
- **Real-time system metrics** (CPU, RAM, Storage)
- **Volume control** with slider
- **Command console** for system commands
- **AI Assistant** integration
- **Task management**
- **File explorer**
- **Weather widget**
- **Notes widget**

## 🔧 Troubleshooting

### TypeScript Errors

If you see "Cannot find module" errors, make sure dependencies are installed:

```bash
pnpm install
```

### Volume Control Not Working

On Windows, install the required packages:

```bash
pip install pycaw comtypes
```

### Port Already in Use

If port 3000 is already in use, Next.js will automatically use the next available port (3001, 3002, etc.).

## 📁 Project Structure

```
.
├── app/                 # Next.js app directory
│   ├── globals.css     # Global styles
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Home page
├── components/         # React components
│   ├── ui/            # UI components
│   └── *.tsx          # Feature components
├── scripts/           # Python scripts
│   └── orion_os_navigator.py
├── lib/               # Utilities
└── public/            # Static assets
```

## 🎯 Keyboard Shortcuts

- `Ctrl+K` - Open Command Console
- `Ctrl+T` - Open Tasks Panel
- `Ctrl+R` - Open Reminders Panel
- `Ctrl+F` - Open File Explorer

## 🌟 Tech Stack

- **Frontend:** Next.js 16, React 19, TypeScript
- **Styling:** Tailwind CSS 4
- **UI Components:** Radix UI
- **Icons:** Lucide React
- **Backend:** Python 3.8+

## 📝 License

Private project





