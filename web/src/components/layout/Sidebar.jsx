import { useState, useEffect } from 'react';
import { useApp } from '../../hooks/useApp';
import ModelSelector from '../chat/ModelSelector';

export default function Sidebar() {
  const { 
    sessions, 
    setSessions, 
    createNewSession, 
    setCurrentSession, 
    currentSession,
    fetchChatHistory,
    updateSessionName,
    deleteSession,
    isLoading,
    error
  } = useApp();
  const [isCreating, setIsCreating] = useState(false);
  const [editingTitle, setEditingTitle] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [userId, setUserId] = useState(''); // State to store user ID

  // Fetch chat history when component mounts
  useEffect(() => {
    const user = localStorage.getItem("user");
    if (user) {
      const userp = JSON.parse(user);
      const currentUserId = userp.user_id;
      setUserId(currentUserId);
      fetchChatHistory(currentUserId);
    }
  }, []);

  const handleNewChat = async () => {
    setIsCreating(true);
    try {
      const newSessionId = await createNewSession();
      setCurrentSession(newSessionId);
    } finally {
      setIsCreating(false);
    }
  };

  const handleRename = (id, currentTitle) => {
    setEditingTitle(id);
    setNewTitle(currentTitle || '');
  };

  const handleSaveTitle = async (id) => {
    if (!newTitle.trim()) {
      setEditingTitle(null);
      setNewTitle('');
      return;
    }

    try {
      await updateSessionName(id, newTitle.trim());
      setEditingTitle(null);
      setNewTitle('');
    } catch (error) {
      console.error('Failed to update session name:', error);
      alert('Failed to update chat name. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteSession(id);
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert('Failed to delete chat. Please try again.');
    }
  };

  const isSessionEmpty = (sessionId) => {
    const session = sessions[sessionId];
    if (!session) return true;
    
    const hasMessages = session.messages && 
                       session.messages.length > 0 && 
                       session.messages.some(msg => msg.content && msg.content.trim() !== '');
    
    return !hasMessages;
  };

  const handleSessionChange = (id) => {
    setSessions(prev => {
      const newSessions = { ...prev };
      Object.keys(newSessions).forEach(sid => {
        if (sid !== id && isSessionEmpty(sid)) {
          delete newSessions[sid];
        }
      });
      return newSessions;
    });
    
    setCurrentSession(id);
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      return date.toLocaleDateString();
    } catch (error) {
      return 'Invalid Date';
    }
  };

  return (
    <aside className="w-64 h-full bg-[#1C1E21] flex flex-col">
      {/* New Chat Button - Commented out
      <div className="p-4">
        <button
          onClick={handleNewChat}
          disabled={isCreating}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center"
        >
          {isCreating ? (
            <span>Creating...</span>
          ) : (
            <>
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Chat
            </>
          )}
        </button>
      </div>
      */}

      {currentSession && (
        <div className="px-4 py-2">
          <ModelSelector sessionId={currentSession} />
        </div>
      )}

      {/* Commenting out the chat sessions list
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="p-4 text-center text-gray-400">
            <div className="animate-spin inline-block w-6 h-6 border-2 border-current border-t-transparent rounded-full mb-2"></div>
            <p>Loading chat history...</p>
          </div>
        )}
        
        {!isLoading && !error && (
          <div className="space-y-1 p-2">
            {Object.entries(sessions || {}).length === 0 ? (
              <div className="p-4 text-center text-gray-400">
                <p>No chat history found</p>
              </div>
            ) : (
              Object.entries(sessions || {}).map(([id, session]) => (
                <div
                  key={id}
                  className={`group relative rounded-md hover:bg-gray-800 ${
                    currentSession === id ? 'bg-gray-800' : ''
                  }`}
                >
                  {editingTitle === id ? (
                    <div className="p-2 flex items-center">
                      <input
                        type="text"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        onBlur={() => handleSaveTitle(id)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSaveTitle(id)}
                        className="flex-1 px-2 py-1 bg-gray-900 text-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-red-500"
                        autoFocus
                      />
                    </div>
                  ) : (
                    <button
                      onClick={() => handleSessionChange(id)}
                      className="w-full px-3 py-2 text-left"
                    >
                      <div className="text-sm font-medium truncate text-gray-200">
                        {session.title || 'New Chat'}
                      </div>
                    </button>
                  )}
                  
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100">
                    <button
                      onClick={() => handleRename(id, session.title)}
                      className="p-1 text-gray-400 hover:text-gray-200"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDelete(id)}
                      className="p-1 text-gray-400 hover:text-red-400"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
      */}
    </aside>
  );
} 