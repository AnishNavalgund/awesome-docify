'use client';

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DiffViewer } from '@/components/ui/diff-viewer';
import { 
  Search, 
  BookOpen, 
  CheckCircle, 
  XCircle, 
  Edit3,
  AlertTriangle,
  Clock,
  Zap,
  Save,
  X
} from 'lucide-react';

interface DocumentUpdate {
  file: string;
  action: 'add' | 'delete' | 'modify';
  reason: string;
  section?: string;
  original_content?: string;
  new_content?: string;
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
  const [editableContent, setEditableContent] = useState<Record<string, string | undefined>>({});
  const [isEditing, setIsEditing] = useState<Record<string, boolean>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [showSaveConfirmation, setShowSaveConfirmation] = useState(false);

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

    // If modify is selected, initialize editable content
    if (decision === 'modify') {
      const doc = response?.documents_to_update.find((_, index) => `doc-${index}` === suggestionId);
      if (doc?.new_content) {
        setEditableContent(prev => ({
          ...prev,
          [suggestionId]: doc.new_content
        }));
        setIsEditing(prev => ({
          ...prev,
          [suggestionId]: true
        }));
      }
    } else {
      // Exit edit mode for other decisions
      setIsEditing(prev => ({
        ...prev,
        [suggestionId]: false
      }));
    }
  };

  const handleContentEdit = (docId: string, newContent: string) => {
    setEditableContent(prev => ({
      ...prev,
      [docId]: newContent
    }));
  };

  const handleSaveEdit = (docId: string) => {
    setIsEditing(prev => ({
      ...prev,
      [docId]: false
    }));
    // The edited content is already saved in editableContent state
  };

  const handleCancelEdit = (docId: string) => {
    setIsEditing(prev => ({
      ...prev,
      [docId]: false
    }));
    // Reset to original content
    const doc = response?.documents_to_update.find((_, index) => `doc-${index}` === docId);
    if (doc?.new_content) {
      setEditableContent(prev => ({
        ...prev,
        [docId]: doc.new_content
      }));
    } else {
      // Remove the entry if no original content exists
      setEditableContent(prev => {
        const newState = { ...prev };
        delete newState[docId];
        return newState;
      });
    }
  };

  const handleApproveAll = () => {
    const newDecisions: Record<string, 'approve' | 'reject' | 'modify'> = {};
    visibleDocuments.forEach((doc, visibleIndex) => {
      const originalIndex = response?.documents_to_update.findIndex(d => 
        d.file === doc.file && 
        d.action === doc.action && 
        d.reason === doc.reason &&
        d.original_content === doc.original_content &&
        d.new_content === doc.new_content
      );
      if (originalIndex !== undefined && originalIndex !== -1) {
        newDecisions[`doc-${originalIndex}`] = 'approve';
      }
    });
    setReviewDecisions(prev => ({
      ...prev,
      ...newDecisions
    }));
  };

  const handleRejectAll = () => {
    const newDecisions: Record<string, 'approve' | 'reject' | 'modify'> = {};
    visibleDocuments.forEach((doc, visibleIndex) => {
      const originalIndex = response?.documents_to_update.findIndex(d => 
        d.file === doc.file && 
        d.action === doc.action && 
        d.reason === doc.reason &&
        d.original_content === doc.original_content &&
        d.new_content === doc.new_content
      );
      if (originalIndex !== undefined && originalIndex !== -1) {
        newDecisions[`doc-${originalIndex}`] = 'reject';
      }
    });
    setReviewDecisions(prev => ({
      ...prev,
      ...newDecisions
    }));
  };

  const saveChanges = async () => {
    if (!response) return;

    setIsSaving(true);
    setSaveStatus(null);

    try {
      // Get approved documents
      const approvedDocuments = response.documents_to_update.filter((doc, index) => {
        const decision = reviewDecisions[`doc-${index}`];
        return decision === 'approve' || decision === 'modify';
      });

      if (approvedDocuments.length === 0) {
        setSaveStatus('No changes to save');
        return;
      }

      // Update documents with edited content if any
      const documentsToSave = approvedDocuments.map((doc, index) => {
        const docId = `doc-${response.documents_to_update.indexOf(doc)}`;
        const editedContent = editableContent[docId];
        
        return {
          ...doc,
          new_content: editedContent || doc.new_content
        };
      });

      const saveRequest = {
        document_updates: documentsToSave,
        approved_by: 'user@example.com' // You can make this dynamic later
      };

      const res = await fetch('/api/v1/save-change', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveRequest),
      });

      if (!res.ok) {
        throw new Error(`Failed to save changes: ${res.status}`);
      }

      const saveResponse = await res.json();
      setSaveStatus(`Successfully saved ${saveResponse.saved_count} changes!`);
      
      // Show confirmation popup instead of auto-clearing
      setShowSaveConfirmation(true);
      
      // Clear the form after successful save
      setTimeout(() => {
        setResponse(null);
        setReviewDecisions({});
        setEditableContent({});
        setIsEditing({});
        setSaveStatus(null);
      }, 2000);

    } catch (err) {
      console.error('Error saving changes:', err);
      setSaveStatus(err instanceof Error ? err.message : 'Failed to save changes');
    } finally {
      setIsSaving(false);
    }
  };

  const goToMainPage = () => {
    // Reset all states to go back to main page
    setResponse(null);
    setReviewDecisions({});
    setEditableContent({});
    setIsEditing({});
    setSaveStatus(null);
    setShowSaveConfirmation(false);
    setQuery('');
    setError(null);
  };

  // Filter out rejected documents
  const visibleDocuments = response?.documents_to_update?.filter((doc, index) => {
    const decision = reviewDecisions[`doc-${index}`];
    return decision !== 'reject';
  }) || [];

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
            <Card className="border-2 border-gray-200 dark:border-gray-700">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">Documents to Update ({visibleDocuments.length})</CardTitle>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-green-600 hover:text-green-700"
                      onClick={handleApproveAll}
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Approve All
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700"
                      onClick={handleRejectAll}
                    >
                      <XCircle className="h-4 w-4 mr-1" />
                      Reject All
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                    {visibleDocuments.map((doc, visibleIndex) => {
                      const originalIndex = response.documents_to_update.findIndex(d => 
                        d.file === doc.file && 
                        d.action === doc.action && 
                        d.reason === doc.reason &&
                        d.original_content === doc.original_content &&
                        d.new_content === doc.new_content
                      );
                      const docId = `doc-${originalIndex}`;
                      const isEditingThisDoc = isEditing[docId] || false;
                      
                      return (
                        <div key={`${doc.file}-${visibleIndex}-${doc.action}`} className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">{doc.file}</h3>
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{doc.action} - {doc.reason}</p>
                            </div>
                          </div>
                          <div className="flex space-x-1">
                            <Button
                              size="sm"
                              variant={reviewDecisions[docId] === 'approve' ? 'default' : 'outline'}
                              onClick={() => handleReviewDecision(docId, 'approve')}
                              className="text-green-600 hover:text-green-700 text-xs px-2 py-1"
                              disabled={isEditingThisDoc}
                            >
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant={reviewDecisions[docId] === 'reject' ? 'default' : 'outline'}
                              onClick={() => handleReviewDecision(docId, 'reject')}
                              className="text-red-600 hover:text-red-700 text-xs px-2 py-1"
                              disabled={isEditingThisDoc}
                            >
                              <XCircle className="h-3 w-3 mr-1" />
                              Reject
                            </Button>
                            <Button
                              size="sm"
                              variant={reviewDecisions[docId] === 'modify' ? 'default' : 'outline'}
                              onClick={() => handleReviewDecision(docId, 'modify')}
                              className="text-blue-600 hover:text-blue-700 text-xs px-2 py-1"
                              disabled={isEditingThisDoc}
                            >
                              <Edit3 className="h-3 w-3 mr-1" />
                              Modify
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Show diff for the first document with content */}
                  {(() => {
                    const firstDocWithContent = visibleDocuments.find(doc => doc.original_content && doc.new_content);
                    if (firstDocWithContent) {
                      const originalIndex = response.documents_to_update.findIndex(d => 
                        d.file === firstDocWithContent.file && 
                        d.action === firstDocWithContent.action && 
                        d.reason === firstDocWithContent.reason &&
                        d.original_content === firstDocWithContent.original_content &&
                        d.new_content === firstDocWithContent.new_content
                      );
                      const docId = `doc-${originalIndex}`;
                      const isEditingThisDoc = isEditing[docId] || false;
                      const currentContent = editableContent[docId] || firstDocWithContent.new_content || '';
                      
                      return (
                        <div>
                          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Proposed Changes</h4>
                          {isEditingThisDoc ? (
                            <div className="space-y-4">
                              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Current Content
                                </div>
                                <div className="bg-red-50 dark:bg-red-900/10 p-3 rounded text-sm font-mono">
                                  {firstDocWithContent.original_content}
                                </div>
                              </div>
                              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Edit New Content
                                </div>
                                <Textarea
                                  value={currentContent}
                                  onChange={(e) => handleContentEdit(docId, e.target.value)}
                                  className="min-h-[200px] font-mono text-sm"
                                  placeholder="Edit the content here..."
                                />
                                <div className="flex justify-end space-x-2 mt-3">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleCancelEdit(docId)}
                                  >
                                    <X className="h-4 w-4 mr-1" />
                                    Cancel
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => handleSaveEdit(docId)}
                                  >
                                    <Save className="h-4 w-4 mr-1" />
                                    Save
                                  </Button>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <DiffViewer
                              originalContent={firstDocWithContent.original_content}
                              newContent={currentContent}
                              fileTitle={firstDocWithContent.file}
                              section={firstDocWithContent.section || "Content"}
                              changeType={firstDocWithContent.action}
                            />
                          )}
                        </div>
                      );
                    }
                    return null;
                  })()}
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4">
              <Button 
                disabled={Object.keys(reviewDecisions).length === 0 || isSaving}
                onClick={saveChanges}
              >
                {isSaving ? (
                  <>
                    <Clock className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>

            {/* Save Status */}
            {saveStatus && (
              <Card className={`mt-4 ${saveStatus.includes('Successfully') ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800'}`}>
                <CardContent className="pt-6">
                  <div className={`flex items-center space-x-2 ${saveStatus.includes('Successfully') ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {saveStatus.includes('Successfully') ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <AlertTriangle className="h-5 w-5" />
                    )}
                    <span>{saveStatus}</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Save Confirmation Popup */}
        {showSaveConfirmation && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center space-x-3 mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Changes Saved Successfully!
                </h3>
              </div>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Your approved changes have been saved to the system. You can now return to the main page to make more updates.
              </p>
              <div className="flex justify-end space-x-3">
                <Button
                  onClick={goToMainPage}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Go to Main Page
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
