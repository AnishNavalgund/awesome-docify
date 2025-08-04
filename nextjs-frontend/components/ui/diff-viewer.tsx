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
  // Enhanced diff algorithm to highlight word-level changes
  const generateDiff = (original: string, newText: string) => {
    const originalLines = original.split('\n');
    const newLines = newText.split('\n');

    const diff: Array<{
      type: 'unchanged' | 'added' | 'removed' | 'modified';
      originalLine?: string;
      newLine?: string;
      highlightedOriginal?: string;
      highlightedNew?: string;
    }> = [];

    const maxLines = Math.max(originalLines.length, newLines.length);

    for (let i = 0; i < maxLines; i++) {
      const originalLine = originalLines[i];
      const newLine = newLines[i];

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
        // For modified lines, highlight the differences
        const highlightedOriginal = highlightDifferences(originalLine, newLine, 'removed');
        const highlightedNew = highlightDifferences(newLine, originalLine, 'added');

        diff.push({
          type: 'modified',
          originalLine,
          newLine,
          highlightedOriginal,
          highlightedNew
        });
      }
    }

    return diff;
  };

  // Function to highlight word-level differences
  const highlightDifferences = (text: string | undefined, compareText: string | undefined, type: 'added' | 'removed') => {
    const words = text ? text.split(/(\s+)/) : [];
    const compareWords = compareText ? compareText.split(/(\s+)/) : [];

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

  const diff = originalContent ? generateDiff(originalContent, newContent || '') : [];

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
                      key={index}
                      className={`p-1 rounded text-xs font-mono ${getDiffLineColor(line.type)}`}
                    >
                      <div className="flex items-center space-x-2">
                        {getDiffIcon(line.type)}
                        <span
                          className="break-all"
                          dangerouslySetInnerHTML={{
                            __html: line.highlightedOriginal || line.originalLine || ''
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
                      key={index}
                      className={`p-1 rounded text-xs font-mono ${getDiffLineColor(line.type)}`}
                    >
                      <div className="flex items-center space-x-2">
                        {getDiffIcon(line.type)}
                        <span
                          className="break-all"
                          dangerouslySetInnerHTML={{
                            __html: line.highlightedNew || line.newLine || ''
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
      </CardContent>
    </Card>
  );
}
