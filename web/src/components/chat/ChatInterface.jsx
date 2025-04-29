import { useState, useEffect, useRef } from "react";
import { useApp } from "../../hooks/useApp";
import { LoadingSpinner } from "../common/LoadingStates";
import { uploadDocument } from "../../services/document.service";
import { getChatResponse } from "../../services/chat.service";
import ReactMarkdown from 'react-markdown';

// Function to remove markdown formatting
const removeMarkdown = (text) => {
  return text.replace(/\*\*/g, '').replace(/\*/g, '');
};

export default function ChatInterface({ sessionId, isDocumentOpen, isSidebarOpen }) {
  const { sessions, setSessions } = useApp();
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [showUploadPopover, setShowUploadPopover] = useState(false);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessions[sessionId]?.messages]);

  useEffect(() => {
    if (sessionId && sessions[sessionId]?.messages?.length > 0) {
      scrollToBottom();
    }
  }, [sessionId, sessions]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const newMessage = {
      role: "user",
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setIsLoading(true);
    setInputMessage("");
    setStreamingText(""); // Reset streaming text

    try {
      // Add user message to the session
      setSessions((prev) => ({
        ...prev,
        [sessionId]: {
          ...prev[sessionId],
          messages: [...(prev[sessionId]?.messages || []), newMessage],
        },
      }));

      // Get response from the chat service
      const user = localStorage.getItem("user");
      const userp = JSON.parse(user);
      const userId = userp.user_id;
      const model = sessions[sessionId]?.settings?.model || 'gpt-4o-mini';
      const response = await getChatResponse(
        inputMessage,
        sessionId,
        model,
        userId
      );

      // Add assistant's response to the session immediately
      setSessions((prev) => ({
        ...prev,
        [sessionId]: {
          ...prev[sessionId],
          messages: [
            ...(prev[sessionId]?.messages || []),
            {
              role: "assistant",
              content: response.answer,
              timestamp: new Date().toISOString(),
              userId: response.user_id
            },
          ],
        },
      }));
      setIsLoading(false);

      /* Commenting out streaming code
      // Start streaming the response
      let streamText = "";
      const chars = response.answer.split("");
      setIsStreaming(true);

      const streamInterval = setInterval(() => {
        if (chars.length > 0) {
          const nextChar = chars.shift();
          streamText += nextChar;
          setStreamingText(streamText);
        } else {
          clearInterval(streamInterval);
          setIsStreaming(false);
        }
      }, 50);
      */
    } catch (error) {
      console.error("Error sending message:", error);
      // Add error message to the chat
      setSessions((prev) => ({
        ...prev,
        [sessionId]: {
          ...prev[sessionId],
          messages: [
            ...(prev[sessionId]?.messages || []),
            {
              role: "assistant",
              content:
                "Sorry, there was an error processing your request. Please try again.",
              timestamp: new Date().toISOString(),
              error: true,
            },
          ],
        },
      }));
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleFiles = async (files) => {
    setIsUploading(true);
    try {
      for (const file of files) {
        const user = localStorage.getItem("user");
        const userp = JSON.parse(user);
        const userId = userp.user_id;
        await uploadDocument(file, userId);
      }
    } catch (error) {
      console.error("Error uploading files:", error);
      alert("Failed to upload file: " + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = async (e, type) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    if (type === "image") {
      const imageFiles = files.filter((file) => file.type.startsWith("image/"));
      if (imageFiles.length !== files.length) {
        alert("Please select only image files");
        e.target.value = "";
        return;
      }
      await handleFiles(imageFiles);
    } else {
      const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
      ];
      const validFiles = files.filter((file) =>
        allowedTypes.includes(file.type)
      );
      if (validFiles.length !== files.length) {
        alert("Please select only PDF, DOC, DOCX, or TXT files");
        e.target.value = "";
        return;
      }
      await handleFiles(validFiles);
    }
    e.target.value = "";
  };

  const handleFileUpload = (type) => {
    if (type === "image") {
      imageInputRef.current?.click();
    } else {
      fileInputRef.current?.click();
    }
    setShowUploadPopover(false);
  };

  return (
    <div className="flex flex-col h-full bg-[#0D1117]">
        <div 
          className="flex-1 overflow-y-auto p-4 space-y-4 pb-24"
          style={{
            marginLeft: isSidebarOpen ? '256px' : '0',
            marginRight: isDocumentOpen ? '300px' : '0',
            transition: 'all 300ms'
          }}
        >
          {sessions[sessionId]?.messages?.length > 0 ? (
            sessions[sessionId]?.messages?.map((message, index) => (
              <div
                key={`message-${index}`}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-700 text-gray-200"
                  }`}
                >
                  <div className="whitespace-pre-wrap">
                    <ReactMarkdown>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))
          ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            No messages yet. Start a conversation!
            </div>
          )}
          {/* Commenting out streaming display
          {isStreaming && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-4 bg-gray-700 text-gray-200">
              <p className="whitespace-pre-wrap">{streamingText}</p>
            </div>
            </div>
          )}
          */}
          <div ref={messagesEndRef} />
        </div>

      <div
        className="fixed bottom-0 p-4 bg-[#0D1117]"
        style={{
          left: isSidebarOpen ? '256px' : '0',
          right: isDocumentOpen ? '300px' : '0',
          transition: 'all 300ms'
        }}
      >
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSendMessage} className="flex space-x-4">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              disabled={isLoading || !inputMessage.trim()}
            >
              {isLoading ? <LoadingSpinner /> : "Send"}
            </button>
          </form>
        </div>
      </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileChange(e, "file")}
            className="hidden"
        multiple
          />
          <input
            type="file"
            ref={imageInputRef}
            onChange={(e) => handleFileChange(e, "image")}
        className="hidden"
        multiple
            accept="image/*"
      />
    </div>
  );
}
