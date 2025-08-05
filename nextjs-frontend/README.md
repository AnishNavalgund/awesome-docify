# Awesome Docify Frontend

Next.js-based frontend application for the Awesome Docify.

## File Structure

```bash
app/
├── page.tsx                 # Main application page
├── layout.tsx              # Root layout with fonts and metadata
├── globals.css             # Global styles and CSS variables
├── api/                    # API route handlers (proxies to backend)
│   └── v1/
│       ├── query/          # Query processing endpoint
│       ├── save-change/    # Document change saving
│       ├── debug/          # Debug endpoints
│       └── docs/           # Documentation endpoints
├── utils/                  # Utility functions
├── fonts/                  # Custom font files (Geist)
└── openapi-client/         # Generated API clientL
components/
├── ui/                     # Reusable UI components
│   ├── button.tsx         # Button component
│   ├── card.tsx           # Card layout component
│   ├── textarea.tsx       # Text input component
│   ├── badge.tsx          # Status badge component
│   └── diff-viewer.tsx    # Document diff visualization
└── actions/               # Action handlers (currently empty)
lib/
├── utils.ts               # Utility functions (cn, error handling)
├── clientConfig.ts        # API client configuration
└── definitions.ts         # Type definitions
```

## Tech Stack

- **Next.js 15.1.0**: React framework with App Router
- **React 19.0.0**: Latest React with concurrent features
- **TypeScript 5**: Type-safe development

## Component Architecture

### Main Page (`page.tsx`)
The primary application interface with:
- Query input form
- Response display
- Document change cards
- Action buttons (approve/reject/modify)
- Save functionality

### UI Components
- **Button**: Variant-based button component
- **Card**: Content container with header/body
- **Textarea**: Multi-line text input
- **Badge**: Status indicator
- **DiffViewer**: Side-by-side diff visualization
- **SaveButton**: Save button component
-**SaveConfirmationModal**: Save confirmation modal component
