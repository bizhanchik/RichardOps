import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, Clock, Container, AlertCircle, CheckCircle, Code, Terminal } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  container: string;
  message: string;
  level?: string;
}

interface QueryResult {
  success: boolean;
  result?: {
    intent: string;
    results: any[];
    count: number;
    data_source?: string;
    query_info?: {
      query_type: string;
      method_called?: string;
      parameters?: Record<string, any>;
    };
  };
  processing_time_ms?: number;
  error?: string;
}

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  queryResult?: QueryResult;
}

interface AskAIProps {
  sidebarOpen?: boolean;
}

const AskAI: React.FC<AskAIProps> = ({ sidebarOpen = true }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: "Hello! I'm your AI Security Assistant. I can help you understand health of your system. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userQuery = inputValue.trim();
    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: userQuery,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Call the backend NLP API
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/api/nlp/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userQuery }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Create AI response with query result
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: generateResponseContent(result),
        timestamp: new Date(),
        queryResult: result
      };

      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error calling NLP API:', error);
      
      // Create error response
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `I encountered an error while processing your query: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the backend server is running on localhost:8000.`,
        timestamp: new Date(),
        queryResult: {
          query_type: 'error',
          method_called: 'N/A',
          parameters: {},
          execution_time: 0,
          total_results: 0,
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      };

      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateResponseContent = (result: QueryResult): string => {
    if (!result.success || result.error) {
      return `I encountered an error: ${result.error || 'Unknown error occurred'}`;
    }

    const processingTime = result.processing_time_ms || 0;
    const queryType = result.result?.intent || 'unknown';
    const totalResults = result.result?.count || 0;
    
    if (totalResults === 0) {
      return `I processed your query but didn't find any matching results. The query was interpreted as "${queryType}" and executed in ${processingTime.toFixed(2)}ms.`;
    }

    return `Found ${totalResults} result${totalResults !== 1 ? 's' : ''} for your "${queryType}" query. Execution completed in ${processingTime.toFixed(2)}ms.`;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatLogLevel = (level?: string) => {
    if (!level) return null;
    
    const levelColors = {
      'ERROR': 'bg-red-100 text-red-800 border-red-200',
      'WARN': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'INFO': 'bg-blue-100 text-blue-800 border-blue-200',
      'DEBUG': 'bg-gray-100 text-gray-800 border-gray-200',
    };
    
    const colorClass = levelColors[level.toUpperCase() as keyof typeof levelColors] || 'bg-gray-100 text-gray-800 border-gray-200';
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${colorClass}`}>
        {level.toUpperCase()}
      </span>
    );
  };

  const LogEntryComponent: React.FC<{ log: LogEntry; index: number }> = ({ log, index }) => (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-2 font-mono text-xs">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-gray-500">#{index + 1}</span>
          <Container className="w-3 h-3 text-blue-500" />
          <span className="font-semibold text-blue-700">{log.container}</span>
          {log.level && formatLogLevel(log.level)}
        </div>
        <div className="flex items-center space-x-1 text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{new Date(log.timestamp).toLocaleString()}</span>
        </div>
      </div>
      <div className="bg-white border border-gray-100 rounded p-2 text-gray-800 leading-relaxed">
        {log.message}
      </div>
    </div>
  );

  const MethodCallComponent: React.FC<{ queryResult: QueryResult }> = ({ queryResult }) => {
    const methodCalled = queryResult.result?.query_info?.method_called || 'process_query';
    const queryType = queryResult.result?.intent || 'unknown';
    const executionTime = queryResult.processing_time_ms || 0;
    const totalResults = queryResult.result?.count || 0;
    const parameters = queryResult.result?.query_info?.parameters || {};
    const dataSource = queryResult.result?.data_source || 'unknown';

    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center space-x-2 mb-3">
          <Code className="w-4 h-4 text-blue-600" />
          <h4 className="font-semibold text-blue-900">Query Execution Details</h4>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              <Terminal className="w-3 h-3 text-green-600" />
              <span className="text-xs font-medium text-gray-600">METHOD CALLED</span>
            </div>
            <code className="text-sm font-mono text-green-700 bg-green-50 px-2 py-1 rounded">
              {methodCalled}
            </code>
          </div>
          
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              <Database className="w-3 h-3 text-purple-600" />
              <span className="text-xs font-medium text-gray-600">QUERY INTENT</span>
            </div>
            <span className="text-sm font-semibold text-purple-700 bg-purple-50 px-2 py-1 rounded">
              {queryType}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              <Clock className="w-3 h-3 text-orange-600" />
              <span className="text-xs font-medium text-gray-600">EXECUTION TIME</span>
            </div>
            <span className="text-sm font-mono text-orange-700">
              {executionTime.toFixed(2)}ms
            </span>
          </div>
          
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              {totalResults > 0 ? (
                <CheckCircle className="w-3 h-3 text-green-600" />
              ) : (
                <AlertCircle className="w-3 h-3 text-yellow-600" />
              )}
              <span className="text-xs font-medium text-gray-600">RESULTS FOUND</span>
            </div>
            <span className="text-sm font-semibold text-gray-700">
              {totalResults.toLocaleString()}
            </span>
          </div>
        </div>

        {dataSource && (
          <div className="bg-white rounded-lg p-3 border border-blue-100 mb-3">
            <div className="flex items-center space-x-2 mb-1">
              <Database className="w-3 h-3 text-blue-600" />
              <span className="text-xs font-medium text-gray-600">DATA SOURCE</span>
            </div>
            <span className="text-sm font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded">
              {dataSource}
            </span>
          </div>
        )}

        {Object.keys(parameters).length > 0 && (
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-2">
              <Code className="w-3 h-3 text-indigo-600" />
              <span className="text-xs font-medium text-gray-600">PARAMETERS</span>
            </div>
            <pre className="text-xs font-mono text-indigo-700 bg-indigo-50 p-2 rounded overflow-x-auto">
              {JSON.stringify(parameters, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  const suggestedQuestions = [
    "show me recent logs",
    "backend container logs",
    "logs from last hour",
    "error logs today",
    "container logs with high severity",
    "show me all containers"
  ];

  return (
    <div className="h-full flex flex-col relative">
      {/* Messages Area - Centered with responsive padding */}
      <div className="flex-1 overflow-y-auto pt-24 pb-32 space-y-6">
        <div className="max-w-3xl mx-auto px-4 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'user' 
                    ? 'bg-emerald-600 text-white ml-3' 
                    : 'bg-blue-100 text-blue-600 mr-3'
                }`}>
                  {message.type === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>
                
                {/* Message Bubble */}
                <div className={`rounded-2xl px-4 py-3 ${
                  message.type === 'user'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className={`text-xs mt-2 ${
                    message.type === 'user' ? 'text-emerald-100' : 'text-gray-500'
                  }`}>
                    {formatTime(message.timestamp)}
                  </p>
                </div>
                
                {/* Query Result Display */}
                {message.type === 'ai' && message.queryResult && (
                  <div className="mt-4 max-w-4xl">
                    <MethodCallComponent queryResult={message.queryResult} />
                    
                    {message.queryResult.result?.results && message.queryResult.result.results.length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-4">
                          <Terminal className="w-4 h-4 text-gray-600" />
                          <h4 className="font-semibold text-gray-900">
                            Query Results ({message.queryResult.result.results.length})
                          </h4>
                        </div>
                        
                        <div className="max-h-96 overflow-y-auto space-y-2">
                          {message.queryResult.result.results.slice(0, 10).map((result, index) => (
                            <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                              <pre className="text-xs font-mono text-gray-700 overflow-x-auto whitespace-pre-wrap">
                                {JSON.stringify(result, null, 2)}
                              </pre>
                            </div>
                          ))}
                          
                          {message.queryResult.result.results.length > 10 && (
                            <div className="text-center py-2">
                              <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                                ... and {message.queryResult.result.results.length - 10} more entries
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 mr-3">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggested Questions - Positioned above input */}
      {messages.length === 1 && !isLoading && (
        <div className="fixed bottom-20 z-40" style={{ 
          left: sidebarOpen ? '256px' : '0px',
          right: '0px',
          transition: 'left 300ms ease-in-out'
        }}>
          <div className="max-w-3xl mx-auto px-4">
            <div className="text-center mb-4">
              <div className="flex flex-wrap justify-center gap-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(question)}
                    className="text-xs px-3 py-2 bg-white hover:bg-gray-50 border border-gray-200 rounded-full text-gray-700 transition-colors shadow-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Input Area - Fixed at bottom with responsive positioning */}
      <div className="fixed bottom-6 z-50" style={{ 
        left: sidebarOpen ? '256px' : '0px',
        right: '0px',
        transition: 'left 300ms ease-in-out'
      }}>
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-white rounded-full border border-gray-300 shadow-lg flex items-center px-5 py-3 min-h-[50px] max-h-32 overflow-hidden">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your system health, security metrics, or performance..."
              className="flex-1 bg-transparent border-none outline-none resize-none text-sm placeholder-gray-500 leading-relaxed pr-3"
              rows={1}
              style={{ minHeight: '24px', maxHeight: '96px' }}
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 flex-shrink-0 ${
                inputValue.trim() && !isLoading
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AskAI;