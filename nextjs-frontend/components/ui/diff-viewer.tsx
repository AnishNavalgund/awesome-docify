import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, Minus, Plus } from 'lucide-react';

interface DiffViewerProps {
  originalContent?: string;
  newContent: string;
  fileTitle: string;
  section: string;
  changeType: 'add' | 'delete' | 'modify' | 'replace';
  confidence?: number;
}

export function DiffViewer({
  originalContent,
  newContent,
  changeType
}: DiffViewerProps) {
  // Improved diff algorithm that handles non-aligned content better
  const generateDiff = (original: string, newText: string) => {
    // If there's no original content, treat everything as added
    if (!original || original.trim() === '') {
      return newText.split('\n').map(line => ({
        type: 'added' as const,
        newLine: line
      }));
    }

    // If there's no new content, treat everything as removed
    if (!newText || newText.trim() === '') {
      return original.split('\n').map(line => ({
        type: 'removed' as const,
        originalLine: line
      }));
    }

    const originalLines = original.split('\n');
    const newLines = newText.split('\n');

    // If the content is completely different, show as replacement
    if (originalLines.length === 1 && newLines.length === 1 && originalLines[0] !== newLines[0]) {
      return [
        {
          type: 'removed' as const,
          originalLine: originalLines[0]
        },
        {
          type: 'added' as const,
          newLine: newLines[0]
        }
      ];
    }

    // For multi-line content, try to find common patterns
    const diff: Array<{
      type: 'unchanged' | 'added' | 'removed' | 'modified';
      originalLine?: string;
      newLine?: string;
      highlightedOriginal?: string;
      highlightedNew?: string;
    }> = [];

    // Simple line-by-line comparison with better handling
    const maxLines = Math.max(originalLines.length, newLines.length);

    for (let i = 0; i < maxLines; i++) {
      const originalLine = originalLines[i] || '';
      const newLine = newLines[i] || '';

      if (originalLine === newLine) {
        diff.push({
          type: 'unchanged',
          originalLine,
          newLine
        });
      } else if (!originalLine && newLine) {
        diff.push({
          type: 'added',
          newLine
        });
      } else if (originalLine && !newLine) {
        diff.push({
          type: 'removed',
          originalLine
        });
      } else {
        // For modified lines, show both versions
        diff.push({
          type: 'modified',
          originalLine,
          newLine,
          highlightedOriginal: highlightDifferences(originalLine, newLine, 'removed'),
          highlightedNew: highlightDifferences(newLine, originalLine, 'added')
        });
      }
    }

    return diff;
  };

  // Function to highlight word-level differences
  const highlightDifferences = (text: string, compareText: string, type: 'added' | 'removed') => {
    const words = text.split(/(\s+)/);
    const compareWords = compareText.split(/(\s+)/);

    return words.map((word, index) => {
      const compareWord = compareWords[index];
      if (word !== compareWord) {
        const bgColor = type === 'added' ? 'bg-green-200 dark:bg-green-800' : 'bg-red-200 dark:bg-red-800';
        const textColor = type === 'added' ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100';
        return `<span class="${bgColor} ${textColor} px-1 rounded">${word}</span>`;
      }
      return word;
    }).join('');
  };

  const diff = generateDiff(originalContent || '', newContent || '');

  const getDiffLineColor = (type: string) => {
    switch (type) {
      case 'added': return 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500';
      case 'removed': return 'bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500';
      case 'modified': return 'bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500';
      default: return 'bg-gray-50 dark:bg-gray-800';
    }
  };

  const getDiffIcon = (type: string) => {
    switch (type) {
      case 'added': return <Plus className="h-3 w-3 text-green-600" />;
      case 'removed': return <Minus className="h-3 w-3 text-red-600" />;
      case 'modified': return <FileText className="h-3 w-3 text-yellow-600" />;
      default: return null;
    }
  };

  return (
    <Card className="border border-gray-200 dark:border-gray-600">
      <CardContent className="pt-4">
        {/* Diff View */}
        <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
          <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-600">
            <div className="grid grid-cols-2 gap-4 text-sm font-medium text-gray-700 dark:text-gray-300">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Current Content</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>{changeType === 'delete' ? 'After Deletion' : 'New Content'}</span>
              </div>
            </div>
          </div>

          {/* Single scrollable container for synchronized scrolling */}
          <div className="max-h-[400px] overflow-y-auto">
            <div className="grid grid-cols-2 gap-0">
              {/* Current Content (Red) */}
              <div className="bg-red-50 dark:bg-red-900/10 p-4">
                <div className="text-sm font-medium text-red-700 dark:text-red-300 mb-2">
                  Current Content
                </div>
                {originalContent ? (
                  <div className="space-y-1">
                    {diff.map((line, index) => (
                      <div
                        key={`original-${index}`}
                        className={`p-1 rounded text-xs font-mono ${getDiffLineColor(line.type)} min-h-[1.5rem] flex items-center`}
                      >
                        <div className="flex items-center space-x-2 w-full">
                          {getDiffIcon(line.type)}
                          <span
                            className="break-words whitespace-pre-wrap flex-1"
                            dangerouslySetInnerHTML={{
                              __html: line.type === 'added' ? '' : ('originalLine' in line ? (line.originalLine || '') : '')
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                    No existing content
                  </div>
                )}
              </div>

              {/* New Content (Green) */}
              <div className="bg-green-50 dark:bg-green-900/10 p-4">
                <div className="text-sm font-medium text-green-700 dark:text-green-300 mb-2">
                  {changeType === 'delete' ? 'After Deletion' : 'New Content'}
                </div>
                {changeType === 'delete' && (!newContent || newContent.trim() === '') ? (
                  <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                    Content will be completely removed
                  </div>
                ) : (
                  <div className="space-y-1">
                    {diff.map((line, index) => (
                      <div
                        key={`new-${index}`}
                        className={`p-1 rounded text-xs font-mono ${getDiffLineColor(line.type)} min-h-[1.5rem] flex items-center`}
                      >
                        <div className="flex items-center space-x-2 w-full">
                          {getDiffIcon(line.type)}
                          <span
                            className="break-words whitespace-pre-wrap flex-1"
                            dangerouslySetInnerHTML={{
                              __html: line.type === 'removed' ? '' : ('newLine' in line ? (line.newLine || '') : '')
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
