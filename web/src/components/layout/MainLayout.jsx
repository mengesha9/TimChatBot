import { useEffect, useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { LuArrowLeftFromLine, LuArrowRightFromLine } from "react-icons/lu";
import ChatInterface from '../chat/ChatInterface';
import Sidebar from './Sidebar';
import Header from './Header';

export default function MainLayout() {
  const { currentSession, setCurrentSession, createNewSession } = useApp();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);

  useEffect(() => {
    if (!currentSession) {
      // Create a new session without requiring user_id
      const sessionId = createNewSession();
      setCurrentSession(sessionId);
    }
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#1C1E21] text-gray-200">
      <Header 
        setIsSidebarOpen={setIsSidebarOpen} 
        isSidebarOpen={isSidebarOpen}
        isRightSidebarOpen={isRightSidebarOpen}
        setIsRightSidebarOpen={setIsRightSidebarOpen}
      />
      
      <div className="flex flex-1 overflow-hidden">
        {isSidebarOpen && (
          <div className="w-64 bg-gray-800 border-r border-gray-700">
            <Sidebar />
          </div>
        )}
        
        <div className="flex-1 flex flex-col">
          <ChatInterface />
        </div>
        
        {isRightSidebarOpen && (
          <div className="w-64 bg-gray-800 border-l border-gray-700">
            {/* Right sidebar content */}
          </div>
        )}
      </div>
    </div>
  );
} 