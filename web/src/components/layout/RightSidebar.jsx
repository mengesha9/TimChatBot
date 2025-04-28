import { useState } from 'react';
import { ShareIcon, UserCircleIcon, EllipsisHorizontalIcon } from '@heroicons/react/24/outline';

export default function RightSidebar({ isOpen, onClose }) {
  const [showMenu, setShowMenu] = useState(false);

  const handleShare = () => {
    // Implement share functionality
    console.log('Share clicked');
  };

  const handleProfile = () => {
    // Implement profile functionality
    console.log('Profile clicked');
  };

  const handleArchive = () => {
    // Implement archive functionality
    console.log('Archive clicked');
    setShowMenu(false);
  };

  const handleDelete = () => {
    // Implement delete functionality
    console.log('Delete clicked');
    setShowMenu(false);
  };

  return (
    <div 
      className={`fixed top-[60px] right-0 h-full w-64 bg-[#1C1E21] border-l border-gray-700 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      <div className="p-4 flex flex-row items-center justify-between">
        <button
          onClick={handleShare}
          className="flex items-center justify-center space-x-2 p-2 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ShareIcon className="h-5 w-5" />
        </button>

        <button
          onClick={handleProfile}
          className="flex items-center justify-center space-x-2 p-2 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <UserCircleIcon className="h-5 w-5" />
        </button>

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center justify-center space-x-2 p-2 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <EllipsisHorizontalIcon className="h-5 w-5" />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg py-1 z-10">
              <button
                onClick={handleArchive}
                className="w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-700"
              >
                Archive
              </button>
              <button
                onClick={handleDelete}
                className="w-full text-left px-4 py-2 text-red-500 hover:bg-gray-700"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 