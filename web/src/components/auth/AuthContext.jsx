import { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [authenticated, setAuthenticated] = useState(true);
  const [sessions, setSessions] = useState({});
  const [currentSession, setCurrentSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser && storedUser !== 'undefined') {
          const userData = JSON.parse(storedUser);
          if (userData && userData.access_token && userData.user_id) {
            setUser(userData);
            setAuthenticated(true);
          } else {
            // Clear invalid user data
            localStorage.removeItem('user');
            setUser(null);
            setAuthenticated(false);
          }
        } else {
          setUser(null);
          setAuthenticated(false);
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
        // Clear invalid user data
        localStorage.removeItem('user');
        setUser(null);
        setAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = (userData) => {
    if (userData && userData.access_token) {
      setUser(userData);
      setAuthenticated(true);
      localStorage.setItem('user', JSON.stringify(userData));
    }
  };
  
  const logout = () => {
    setUser(null);
    setAuthenticated(true);
    setSessions({});
    setCurrentSession(null);
    localStorage.removeItem('user');
  };

  const isSessionEmpty = (sessionId) => {
    const session = sessions[sessionId];
    if (!session) return true;
    
    const hasMessages = session.messages && 
                       session.messages.length > 0 && 
                       session.messages.some(msg => msg.content && msg.content.trim() !== '');
    
    return !hasMessages;
  };

  const handleSessionChange = (sessionId) => {
    console.log('handleSessionChange', sessionId);
    setSessions(prev => {
      const newSessions = { ...prev };
      Object.keys(newSessions).forEach(sid => {
        console.log('Checking session:', sid, newSessions[sid]);
        if (sid !== sessionId && isSessionEmpty(sid)) {
          delete newSessions[sid];
        }
      });
      return newSessions;
    });
    
    setCurrentSession(sessionId);
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen bg-[#1C1E21]">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }

  return (
    <AuthContext.Provider value={{
      user,
      authenticated,
      sessions,
      setSessions,
      currentSession,
      setCurrentSession: handleSessionChange,
      login,
      logout,
      isSessionEmpty
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext); 