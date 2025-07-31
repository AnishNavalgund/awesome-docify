# Awesome Docify Frontend

A modern Next.js frontend for the Awesome Docify documentation management system.

## Features

- **Document Viewer**: Browse and view documentation files with enhanced markdown rendering
- **Search Functionality**: Search through available documents
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Automatic dark/light mode based on system preferences
- **Real-time Updates**: Live reload during development

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or pnpm
- Backend server running on `http://localhost:8000`

### Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

### Document Viewer

1. Click "Get Started" on the homepage
2. Browse available documents in the sidebar
3. Use the search bar to filter documents
4. Click on any document to view its content
5. Use the "View Original" button to open the source URL

### Features

- **Enhanced Markdown Rendering**: Supports headers, lists, code blocks, links, and more
- **Document Metadata**: View document information like language, content type, and status
- **Responsive Layout**: Sidebar collapses on mobile devices
- **Loading States**: Smooth loading indicators for better UX

## API Integration

The frontend communicates with the backend through Next.js API routes:

- `/api/v1/debug/json-files` - List available documents
- `/api/v1/debug/json-files/[filename]` - Get document content

## Development

### Project Structure

```
app/
├── docs/           # Document viewer page
├── api/            # API routes for backend communication
├── components/     # Reusable UI components
└── globals.css     # Global styles and markdown styling
```

### Key Components

- **Document Viewer** (`app/docs/page.tsx`): Main document browsing interface
- **API Routes**: Proxy requests to the backend
- **Markdown Renderer**: Custom markdown parsing and rendering

### Styling

The project uses Tailwind CSS with custom markdown styling defined in `globals.css`.

## Environment Variables

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Building for Production

```bash
npm run build
npm start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request 