import { useState } from 'react';
import axios from 'axios';

function App() {
  const [question, setQuestion] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [files, setFiles] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleUpload = async () => {
    if (!files) return;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    setUploadStatus('Uploading and training AI...');
    try {
      await axios.post('http://localhost:8000/upload', formData);
      setUploadStatus('Training complete! You can now ask questions.');
    } catch (error) {
      setUploadStatus('Error uploading documents.');
    }
  };

  const handleAsk = async () => {
    if (!question) return;
    const newChatLog = [...chatLog, { role: 'user', content: question }];
    setChatLog(newChatLog);
    setQuestion('');

    try {
      const response = await axios.post('http://localhost:8000/ask', { question });
      setChatLog([...newChatLog, { role: 'ai', content: response.data.answer }]);
    } catch (error) {
      setChatLog([...newChatLog, { role: 'ai', content: 'Error: Please ensure documents are uploaded.' }]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold mb-6 text-blue-800">Enterprise AI Knowledge Base</h1>
        
        {/* Admin Upload Section */}
        <div className="mb-8 p-4 bg-gray-50 rounded border border-gray-200">
          <h2 className="text-lg font-semibold mb-2">Admin: Upload Knowledge Documents</h2>
          <input type="file" multiple onChange={(e) => setFiles(e.target.files)} className="mb-2" />
          <button onClick={handleUpload} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Process Documents
          </button>
          <p className="mt-2 text-sm text-gray-600">{uploadStatus}</p>
        </div>

        {/* Chat Interface */}
        <div className="border border-gray-300 rounded h-96 overflow-y-auto p-4 mb-4 bg-gray-50">
          {chatLog.map((message, index) => (
            <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
              <span className={`inline-block p-3 rounded-lg ${message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'}`}>
                {message.content}
              </span>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' ? handleAsk() : null}
            placeholder="E.g., What is our remote work policy?"
            className="flex-1 border border-gray-300 p-3 rounded focus:outline-none focus:border-blue-500"
          />
          <button onClick={handleAsk} className="bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700 font-semibold">
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;