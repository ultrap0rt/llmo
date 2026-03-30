import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSession, sendMessage } from '../api';
import type { ChatSession, Message } from '../api';
import { Send, Bot, User, Share2, CornerUpLeft } from 'lucide-react';

export function Chat() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId) {
      getSession(sessionId)
        .then(data => {
          setSession(data);
          setMessages(data.messages);
        })
        .catch(() => {
          alert('Сессия не найдена. Создайте новую.');
          navigate('/');
        });
    }
  }, [sessionId, navigate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId || loading) return;

    const userText = input;
    setInput('');
    setLoading(true);

    // Optimistic user message
    const tempId = Date.now().toString();
    const tempUserMsg: Message = {
      id: tempId,
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await sendMessage(sessionId, userText);
      const assistantMsg: Message = {
        id: response.message_id,
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      alert('Ошибка при отправке сообщения');
    } finally {
      setLoading(false);
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('Скрытая ссылка скопирована в буфер обмена!');
  };

  if (!session) {
    return <div className="flex h-full items-center justify-center">Загрузка сессии...</div>;
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto w-full bg-gray-900 border-x border-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/95 sticky top-0 z-10 backdrop-blur">
        <div className="flex items-center space-x-3">
          <button onClick={() => navigate('/')} className="p-2 hover:bg-gray-800 rounded-lg text-gray-400">
            <CornerUpLeft size={20} />
          </button>
          <div>
            <h2 className="font-semibold truncate">{session.title}</h2>
            <p className="text-xs text-gray-500 font-mono hidden sm:block">ID: {sessionId}</p>
          </div>
        </div>
        <button 
          onClick={copyLink}
          className="flex items-center space-x-2 text-sm text-blue-400 hover:text-blue-300 hover:bg-gray-800 p-2 rounded-lg transition-colors"
        >
          <Share2 size={16} />
          <span className="hidden sm:inline">Копировать ссылку</span>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            <Bot size={48} className="mx-auto mb-4 opacity-50" />
            <p>Нет сообщений. Начните диалог!</p>
            <p className="text-sm mt-2">Система будет запоминать каждое слово и строить граф знаний.</p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-blue-600 ml-3' : 'bg-green-600 mr-3'}`}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-3 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-gray-800 text-gray-100 rounded-tl-sm'}`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                <span className="text-[10px] text-gray-500 mt-1 select-none">
                  {new Date(msg.timestamp).toLocaleString()}
                </span>
                {msg.graph_context && msg.role === 'assistant' && (
                  <details className="mt-2 text-xs text-gray-500 cursor-pointer max-w-sm">
                    <summary>Knowledge Graph Context</summary>
                    <pre className="mt-2 p-2 bg-gray-950 rounded border border-gray-800 whitespace-pre-wrap font-mono overflow-x-auto text-[10px]">
                      {msg.graph_context}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex flex-row max-w-[80%] items-center">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-green-600 mr-3">
                <Bot size={16} />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-gray-800 text-gray-100 rounded-tl-sm flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-gray-800 bg-gray-900">
        <form onSubmit={handleSend} className="flex space-x-2 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Введите сообщение..."
            className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-xl pl-4 pr-12 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-500 text-white w-10 flex items-center justify-center rounded-lg transition-colors disabled:opacity-50 disabled:hover:bg-blue-600"
          >
            <Send size={18} />
          </button>
        </form>
        <div className="text-center mt-2 text-[10px] text-gray-600">
          Все ваши данные сохраняются с точной временной меткой в граф знаний. Ссылка уникальна и скрыта.
        </div>
      </div>
    </div>
  );
}
