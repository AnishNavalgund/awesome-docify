'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ChevronLeft, FileText, Search, BookOpen } from 'lucide-react';
import Link from 'next/link';

interface DocumentFile {
  files: string[];
}

interface DocumentContent {
  markdown: string;
  metadata: {
    title?: string;
    url?: string;
    sourceURL?: string;
    language?: string;
    contentType?: string;
    scrapeId?: string;
    statusCode?: number;
  };
}

export default function DocsPage() {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [documentContent, setDocumentContent] = useState<DocumentContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch available document files
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/v1/debug/json-files');
        if (!response.ok) {
          throw new Error('Failed to fetch document files');
        }
        const data: DocumentFile = await response.json();
        setFiles(data.files);
        
        // Auto-select first file if available
        if (data.files.length > 0 && !selectedFile) {
          setSelectedFile(data.files[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load documents');
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, []);

  // Fetch document content when file is selected
  useEffect(() => {
    const fetchDocumentContent = async () => {
      if (!selectedFile) return;

      try {
        setLoading(true);
        const response = await fetch(`/api/v1/debug/json-files/${encodeURIComponent(selectedFile)}`);
        if (!response.ok) {
          throw new Error('Failed to fetch document content');
        }
        const data: DocumentContent = await response.json();
        setDocumentContent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document content');
      } finally {
        setLoading(false);
      }
    };

    fetchDocumentContent();
  }, [selectedFile]);

  // Filter files based on search term
  const filteredFiles = files.filter(file => 
    file.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatFileName = (filename: string) => {
    // Remove file extension and replace underscores with spaces
    return filename
      .replace(/\.json$/, '')
      .replace(/_/g, ' ')
      .replace(/\./g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const renderMarkdown = (markdown: string) => {
    // Enhanced markdown rendering with better formatting
    const lines = markdown.split('\n');
    const elements: JSX.Element[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];

    lines.forEach((line, index) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          elements.push(
            <pre key={`code-${index}`} className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg my-4 font-mono text-sm overflow-x-auto">
              <code>{codeBlockContent.join('\n')}</code>
            </pre>
          );
          codeBlockContent = [];
          inCodeBlock = false;
        } else {
          // Start code block
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        return;
      }

      // Handle headers
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={index} className="text-3xl font-bold mb-4 mt-6 text-gray-900 dark:text-white">
            {line.substring(2)}
          </h1>
        );
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={index} className="text-2xl font-bold mb-3 mt-5 text-gray-900 dark:text-white">
            {line.substring(3)}
          </h2>
        );
        return;
      }
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={index} className="text-xl font-bold mb-2 mt-4 text-gray-900 dark:text-white">
            {line.substring(4)}
          </h3>
        );
        return;
      }
      if (line.startsWith('#### ')) {
        elements.push(
          <h4 key={index} className="text-lg font-bold mb-2 mt-3 text-gray-900 dark:text-white">
            {line.substring(5)}
          </h4>
        );
        return;
      }

      // Handle lists
      if (line.startsWith('- ') || line.startsWith('* ')) {
        elements.push(
          <li key={index} className="ml-4 mb-1 text-gray-700 dark:text-gray-300">
            {line.substring(2)}
          </li>
        );
        return;
      }

      // Handle numbered lists
      if (/^\d+\.\s/.test(line)) {
        elements.push(
          <li key={index} className="ml-4 mb-1 text-gray-700 dark:text-gray-300">
            {line.replace(/^\d+\.\s/, '')}
          </li>
        );
        return;
      }

      // Handle bold text
      if (line.includes('**')) {
        const parts = line.split('**');
        const formattedParts = parts.map((part, partIndex) => {
          if (partIndex % 2 === 1) {
            return <strong key={partIndex}>{part}</strong>;
          }
          return part;
        });
        elements.push(
          <p key={index} className="mb-2 leading-relaxed text-gray-700 dark:text-gray-300">
            {formattedParts}
          </p>
        );
        return;
      }

      // Handle links
      if (line.includes('[') && line.includes('](') && line.includes(')')) {
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        let lastIndex = 0;
        const parts: (string | JSX.Element)[] = [];
        let match;

        while ((match = linkRegex.exec(line)) !== null) {
          parts.push(line.slice(lastIndex, match.index));
          parts.push(
            <a
              key={`link-${match.index}`}
              href={match[2]}
              className="text-blue-600 dark:text-blue-400 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {match[1]}
            </a>
          );
          lastIndex = match.index + match[0].length;
        }
        parts.push(line.slice(lastIndex));

        elements.push(
          <p key={index} className="mb-2 leading-relaxed text-gray-700 dark:text-gray-300">
            {parts}
          </p>
        );
        return;
      }

      // Handle empty lines
      if (line.trim() === '') {
        elements.push(<br key={index} />);
        return;
      }

      // Default paragraph
      elements.push(
        <p key={index} className="mb-2 leading-relaxed text-gray-700 dark:text-gray-300">
          {line}
        </p>
      );
    });

    return elements;
  };

  if (loading && files.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading documents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <FileText className="h-12 w-12 mx-auto" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Error Loading Documents</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="ghost" size="sm" className="flex items-center space-x-2">
                  <ChevronLeft className="h-4 w-4" />
                  <span>Back</span>
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <BookOpen className="h-5 w-5 text-blue-500" />
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Documentation Viewer
                </h1>
              </div>
            </div>
            <Badge variant="secondary" className="text-sm">
              {files.length} documents
            </Badge>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Document List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileText className="h-5 w-5" />
                  <span>Documents</span>
                </CardTitle>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredFiles.map((file) => (
                    <button
                      key={file}
                      onClick={() => setSelectedFile(file)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        selectedFile === file
                          ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="font-medium text-sm text-gray-900 dark:text-white">
                        {formatFileName(file)}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {file}
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content - Document Viewer */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>
                    {selectedFile ? formatFileName(selectedFile) : 'Select a document'}
                  </span>
                  {documentContent?.metadata?.url && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(documentContent.metadata.url, '_blank')}
                    >
                      View Original
                    </Button>
                  )}
                </CardTitle>
                {documentContent?.metadata && (
                  <div className="flex flex-wrap gap-2">
                    {documentContent.metadata.language && (
                      <Badge variant="secondary">{documentContent.metadata.language}</Badge>
                    )}
                    {documentContent.metadata.contentType && (
                      <Badge variant="outline">{documentContent.metadata.contentType}</Badge>
                    )}
                    {documentContent.metadata.statusCode && (
                      <Badge variant={documentContent.metadata.statusCode === 200 ? "default" : "destructive"}>
                        Status: {documentContent.metadata.statusCode}
                      </Badge>
                    )}
                  </div>
                )}
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                      <p className="text-gray-600 dark:text-gray-300">Loading document...</p>
                    </div>
                  </div>
                                 ) : documentContent ? (
                   <div className="max-w-none">
                     <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 overflow-auto max-h-[70vh]">
                       <div className="markdown-content">
                         {renderMarkdown(documentContent.markdown)}
                       </div>
                     </div>
                   </div>
                ) : (
                  <div className="text-center py-12">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-300">
                      Select a document from the sidebar to view its content
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
} 