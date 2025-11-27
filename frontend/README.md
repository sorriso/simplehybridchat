# path: ./README.md
# version: 1

# AI Chatbot Frontend

Modern, full-featured chatbot interface built with Next.js, NLUX, and TypeScript.

## Features

- ✅ **Conversations Management**
  - Create, rename, and delete conversations
  - Organize conversations into groups
  - Drag & drop conversations between groups
  
- ✅ **File Upload**
  - Drag & drop file upload
  - Multiple file support
  - Progress tracking
  - Supported formats: PDF, TXT, CSV, JSON, MD
  
- ✅ **Settings & Customization**
  - Custom prompt instructions
  - User preferences
  - Theme settings (coming soon)
  
- ✅ **Real-time Chat**
  - Streaming responses via SSE
  - ChatGPT-like interface with NLUX
  - Markdown support
  - Context-aware conversations

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: React 18
- **Chat Interface**: NLUX
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **File Upload**: react-dropzone

## Project Structure

```
src/
├── app/                      # Next.js app router
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Main page
│   └── globals.css          # Global styles
├── components/
│   ├── chat/                # Chat components
│   ├── sidebar/             # Sidebar & navigation
│   ├── upload/              # File upload components
│   ├── settings/            # Settings components
│   └── ui/                  # Reusable UI components
├── lib/
│   ├── api/                 # API client functions
│   ├── hooks/               # React hooks
│   └── utils/               # Utility functions
└── types/                   # TypeScript type definitions
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (FastAPI)

### Installation

1. **Install dependencies**
```bash
npm install
```

2. **Configure environment variables**

Create a `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MOCK_TOKEN=dev-token-12345
NEXT_PUBLIC_MINIO_ENDPOINT=http://localhost:9000
```

3. **Run development server**
```bash
npm run dev
```

4. **Open browser**
Navigate to [http://localhost:3000](http://localhost:3000)

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

- Use TypeScript for all new code
- Follow React hooks best practices
- Keep components small and focused
- Add comments for complex logic
- Use meaningful variable names

## Backend API Integration

The frontend expects the following API endpoints:

### Conversations
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `PUT /api/conversations/:id` - Update conversation
- `DELETE /api/conversations/:id` - Delete conversation

### Groups
- `GET /api/groups` - List groups
- `POST /api/groups` - Create group
- `DELETE /api/groups/:id` - Delete group
- `POST /api/groups/:id/conversations` - Add conversation to group
- `DELETE /api/groups/:id/conversations/:conversationId` - Remove from group

### Chat
- `POST /api/chat/stream` - Stream chat responses (SSE)

### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files` - List files
- `DELETE /api/files/:id` - Delete file

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update user settings

## Authentication

Currently uses mock authentication with a hardcoded token. In production:

1. Implement proper SSO integration
2. Handle token refresh
3. Add session management
4. Implement logout functionality

## Deployment

### Docker (Recommended)

**Quick Start:**
```bash
make build
make run
```

The application will be available at http://localhost

**All available commands:**
```bash
make build       # Build Docker image
make run         # Run container on port 80
make stop        # Stop container
make restart     # Restart container
make logs        # View logs
make clean       # Remove container and image
```

See [DOCKER.md](./DOCKER.md) for detailed Docker documentation.

### Manual Build for Production

```bash
npm run build
npm run start
```

### Environment Variables (Production)

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_MINIO_ENDPOINT=https://minio.yourdomain.com
```

## Troubleshooting

### NLUX Not Rendering

Ensure NLUX theme CSS is imported:
```typescript
import '@nlux/themes/nova.css';
```

### API Connection Issues

Check CORS configuration on backend:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### File Upload Fails

Verify:
- File size is under 10MB
- File type is in allowed list
- Backend endpoint is configured correctly

## Future Enhancements

- [ ] Dark mode theme
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Export conversations
- [ ] Advanced search
- [ ] Keyboard shortcuts
- [ ] Mobile responsive design

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Submit a pull request

## License

MIT License - see LICENSE file for details