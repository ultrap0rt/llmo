import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Home } from './components/Home';
import { Chat } from './components/Chat';
import { SwaggerPage } from './components/SwaggerPage';

function App() {
  return (
    <Router>
      <div className="bg-black text-white h-screen w-screen overflow-hidden">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat/:sessionId" element={<Chat />} />
          <Route path="/swagger" element={<SwaggerPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
