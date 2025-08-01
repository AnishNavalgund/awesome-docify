'use client';

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DiffViewer } from '@/components/ui/diff-viewer';
import { 
  Search, 
  BookOpen, 
  CheckCircle, 
  XCircle, 
  Edit3,
  AlertTriangle,
  Clock,
  Target,
  Zap
} from 'lucide-react';

interface DocumentUpdate {
  file: string;
  action: 'add' | 'remove' | 'modify';
  reason: string;
  section?: string;
  original_content?: string;
  new_content?: string;
  confidence?: number;
  line_numbers?: number[];
}

interface QueryResponse {
  query: string;
  keyword?: string;
  analysis: string;
  documents_to_update: DocumentUpdate[];
  total_documents: number;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, 'approve' | 'reject' | 'modify'>>({});

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      console.log('Sending query to backend:', query);
      const res = await fetch('/api/v1/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      console.log('Response status:', res.status);
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('Backend error response:', errorText);
        throw new Error(`Failed to get suggestions: ${res.status} ${errorText}`);
      }

      const data: QueryResponse = await res.json();
      console.log('Received response:', data);
      setResponse(data);
    } catch (err) {
      console.error('Error in handleSubmit:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReviewDecision = (suggestionId: string, decision: 'approve' | 'reject' | 'modify') => {
    setReviewDecisions(prev => ({
      ...prev,
      [suggestionId]: decision
    }));
  };

  const getPriorityColor = (action: string) => {
    switch (action) {
      case 'modify': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'add': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'remove': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-16">
            <div className="flex items-center space-x-4">
              <BookOpen className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Awesome Docify</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Query Input */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="h-5 w-5" />
              <span>What would you like to update?</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g., the function set_default_openai_key will be changed to set_default_openai_keyValue"
                  className="min-h-[100px]"
                  disabled={isLoading}
                />
              </div>
              <Button 
                type="submit" 
                disabled={isLoading || !query.trim()}
                className="w-full sm:w-auto"
              >
                {isLoading ? (
                  <>
                    <Clock className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Update Docs
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="mb-8 border-red-200 dark:border-red-800">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {response && (
          <div className="space-y-8">
            {/* Documents to Update */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Documents to Update ({response.total_documents || 0})
              </h2>
              
              {response.documents_to_update?.map((doc, index) => (
                <Card key={index} className="border-2 border-gray-200 dark:border-gray-700">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{doc.file}</CardTitle>
                        <div className="flex items-center space-x-4 mt-2">
                          <Badge className={getPriorityColor(doc.action)}>
                            {doc.action}
                          </Badge>
                          {doc.section && (
                            <Badge variant="outline">
                              Section: {doc.section}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant={reviewDecisions[`doc-${index}`] === 'approve' ? 'default' : 'outline'}
                          onClick={() => handleReviewDecision(`doc-${index}`, 'approve')}
                          className="text-green-600 hover:text-green-700"
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant={reviewDecisions[`doc-${index}`] === 'reject' ? 'destructive' : 'outline'}
                          onClick={() => handleReviewDecision(`doc-${index}`, 'reject')}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          variant={reviewDecisions[`doc-${index}`] === 'modify' ? 'default' : 'outline'}
                          onClick={() => handleReviewDecision(`doc-${index}`, 'modify')}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <Edit3 className="h-4 w-4 mr-1" />
                          Modify
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="space-y-4">
                      {/* Actual Diff View */}
                      {doc.original_content && doc.new_content && (
                        <div>
                          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Proposed Changes</h4>
                          <DiffViewer
                            originalContent={doc.original_content}
                            newContent={doc.new_content}
                            fileTitle={doc.file}
                            section={doc.section || "Content"}
                            changeType="modify"
                            confidence={doc.confidence || 0.8}
                          />
                        </div>
                      )}
                      
                      {/* Fallback if no content available */}
                      {(!doc.original_content || !doc.new_content) && (
                        <div>
                          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Document Update Required</h4>
                          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                            <p className="text-yellow-800 dark:text-yellow-200">
                              Content extraction is in progress. The document "{doc.file}" needs to be updated based on the query.
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4">
              <Button variant="outline" onClick={() => setResponse(null)}>
                Start Over
              </Button>
              <Button 
                disabled={Object.keys(reviewDecisions).length === 0}
                onClick={() => {
                  // TODO: Implement save functionality
                  console.log('Saving decisions:', reviewDecisions);
                }}
              >
                Save Changes
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
