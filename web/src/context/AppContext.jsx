import { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.config';

// Create the context
export const AppContext = createContext(null);

// Create the hook
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

// Create the provider component
export const AppProvider = ({ children }) => {
  const [sessions, setSessions] = useState({});
  const [currentSession, setCurrentSession] = useState(null);
  const [preferences, setPreferences] = useState({
    theme: 'light',
    fontSize: 'medium',
    autoSave: true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const storedSessions = localStorage.getItem('sessions');
    const storedPreferences = localStorage.getItem('preferences');

    if (storedSessions) setSessions(JSON.parse(storedSessions));
    if (storedPreferences) setPreferences(JSON.parse(storedPreferences));
  }, []);

  const createNewSession = () => {
    const sessionId = `session_${Date.now()}`;
    const newSession = {
      id: sessionId,
      title: 'New Chat',
      createdAt: new Date().toISOString(),
      messages: [],
      settings: {
        model: 'gpt-4',
        temperature: 0.7,
        systemPrompt: 'You are a helpful AI assistant.'
      }
    };

    setSessions(prev => ({
      [sessionId]: newSession,
      ...prev,
    }));

    return sessionId;
  };

  const fetchChatHistory = async (userId) => {
    setIsLoading(true);
    setError(null);

    try {
      // Clear localStorage first
      localStorage.removeItem('sessions');
      
      // Use default_user if no userId is provided
      const effectiveUserId = userId || "default_user";
      
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHAT_HISTORY}?user_id=${effectiveUserId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch chat history: ${response.status}`);
      }

      const data = await response.json();
      
      // Transform the API response to match our session format
      const transformedSessions = {};
      
      Object.entries(data).forEach(([sessionId, sessionData]) => {
        // Create an array of interleaved messages (user query followed by assistant response)
        const messages = [];
        
        // Process each query-response pair and add them as sequential messages
        sessionData.queries.forEach(query => {
          // Add user message
          messages.push({
            id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'user',
            content: query.query,
            timestamp: query.timestamp,
            status: 'complete'
          });
          
          // Add assistant message with document data
          messages.push({
            id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: query.response,
            timestamp: query.timestamp,
            status: 'complete',
            documents: query.documents || {}, // Include document highlighting data
            userId: effectiveUserId // Include user ID for document access
          });
        });
        
        // Sort messages by timestamp if needed
        messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        transformedSessions[sessionId] = {
          id: sessionId,
          title: sessionData.name || 'New Chat',
          createdAt: sessionData.timestamp,
          timestamp: sessionData.timestamp,
          messages: messages,
          settings: {
            model: sessionData.model || 'gpt-4o-mini',
            temperature: 0.7,
            systemPrompt: 'You are a helpful AI assistant.'
          }
        };
      });
      
      // Sort sessions by createdAt date (newest first)
      const sortedSessions = Object.fromEntries(
        Object.entries(transformedSessions)
          .sort(([, a], [, b]) => new Date(b.createdAt) - new Date(a.createdAt))
      );
      
      setSessions(sortedSessions);
      
      // Save to localStorage
      localStorage.setItem('sessions', JSON.stringify(sortedSessions));
      
      // Set the most recent session as current if no current session
      if (!currentSession && Object.keys(sortedSessions).length > 0) {
        setCurrentSession(Object.keys(sortedSessions)[0]);
      }
      
    } catch (err) {
      setError(err.message);
      console.error('Error fetching chat history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSessionName = async (sessionId, newName) => {
    if (!sessionId) {
      setError('Session ID is required to update chat name');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Check if session exists and has no messages
      if (sessions[sessionId]?.messages?.length === 0 || sessions[sessionId]?.messages?.length === undefined) {
        // Update only frontend state for empty sessions
        setSessions(prev => {
          const updatedSessions = { ...prev };
          if (updatedSessions[sessionId]) {
            updatedSessions[sessionId] = {
              ...updatedSessions[sessionId],
              title: newName
            };
          }
          return updatedSessions;
        });

        // Update localStorage
        const updatedSessions = { ...sessions };
        if (updatedSessions[sessionId]) {
          updatedSessions[sessionId] = {
            ...updatedSessions[sessionId],
            title: newName
          };
        }
        localStorage.setItem('sessions', JSON.stringify(updatedSessions));
        setIsLoading(false);
        return;
      }

      const user = localStorage.getItem('user');
      let userId = "default_user"; // Default user ID for unregistered users

      if (user) {
        try {
          const userData = JSON.parse(user);
          if (userData && userData.user_id) {
            userId = userData.user_id;
          }
        } catch (error) {
          console.warn("Invalid user data in localStorage, using default user ID");
        }
      }

      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHAT_NAME}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          name: newName
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to update chat name: ${response.status}`);
      }

      // Update frontend state
      setSessions(prev => {
        const updatedSessions = { ...prev };
        if (updatedSessions[sessionId]) {
          updatedSessions[sessionId] = {
            ...updatedSessions[sessionId],
            title: newName
          };
        }
        return updatedSessions;
      });

      // Update localStorage
      const updatedSessions = { ...sessions };
      if (updatedSessions[sessionId]) {
        updatedSessions[sessionId] = {
          ...updatedSessions[sessionId],
          title: newName
        };
      }
      localStorage.setItem('sessions', JSON.stringify(updatedSessions));

    } catch (err) {
      setError(err.message);
      console.error('Error updating chat name:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId) => {
    if (!sessionId) {
      setError('Session ID is required to delete chat');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const user = localStorage.getItem('user');
      let userId = "default_user"; // Default user ID for unregistered users

      if (user) {
        try {
          const userData = JSON.parse(user);
          if (userData && userData.user_id) {
            userId = userData.user_id;
          }
        } catch (error) {
          console.warn("Invalid user data in localStorage, using default user ID");
        }
      }

      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.DELETE_CHAT_HISTORY}?user_id=${userId}&session_id=${sessionId}`, {
          method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`Failed to delete chat: ${response.status}`);
      }

      // Update frontend state
      setSessions(prev => {
        const updatedSessions = { ...prev };
        delete updatedSessions[sessionId];
        return updatedSessions;
      });

      // Update localStorage
      const updatedSessions = { ...sessions };
      delete updatedSessions[sessionId];
      localStorage.setItem('sessions', JSON.stringify(updatedSessions));

      // If the deleted session was the current session, set current session to null
      if (currentSession === sessionId) {
          setCurrentSession(null);
      }

    } catch (err) {
      setError(err.message);
      console.error('Error deleting chat:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    sessions,
    setSessions,
    currentSession,
    setCurrentSession,
    preferences,
    setPreferences,
    isLoading,
    error,
    createNewSession,
    fetchChatHistory,
    updateSessionName,
    deleteSession
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}; 