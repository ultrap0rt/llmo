import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession } from '../api';
import { Bot, ArrowRight } from 'lucide-react';

export function Home() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStartChat = async () => {
    try {
      setLoading(true);
      const session = await createSession('Новый диалог');
      navigate(`/chat/${session.session_id}`);
    } catch (err) {
      console.error(err);
      alert('Ошибка при создании сессии');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full w-full max-w-2xl mx-auto p-6 space-y-8 text-center">
      <div className="bg-gray-800 p-6 rounded-full">
        <Bot size={64} className="text-blue-500" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight">AI Knowledge Graph System</h1>
      <p className="text-xl text-gray-400">
        Система с бесконечным контекстом и эпизодической памятью.
        Начните чат, и мы сгенерируем для вас скрытую ссылку для возвращения в любой момент.
      </p>
      
      <button
        onClick={handleStartChat}
        disabled={loading}
        className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl text-lg font-medium transition-all disabled:opacity-50"
      >
        <span>{loading ? 'Создание...' : 'Начать новый диалог'}</span>
        {!loading && <ArrowRight size={20} />}
      </button>
    </div>
  );
}
