import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Feed } from './components/Feed';
import { InsightsPanel } from './components/InsightsPanel';
import type { PostReaction, DirectMessage, DriftSummary, StreamEvent } from './types';

function App() {
  const [originalText, setOriginalText] = useState('');
  const [feed, setFeed] = useState<PostReaction[]>([]);
  const [dms, setDms] = useState<DirectMessage[]>([]);
  const [driftSummary, setDriftSummary] = useState<DriftSummary | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const startSimulation = async (text: string) => {
    setOriginalText(text);
    setFeed([]);
    setDms([]);
    setDriftSummary(null);
    setIsStreaming(true);

    try {
      const response = await fetch('http://localhost:8000/post/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, max_hops: 6 })
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        
        buffer = lines.pop() || ''; 

        for (const block of lines) {
          if (!block.trim()) continue;
          
          const eventLine = block.split('\n').find(l => l.startsWith('event:'));
          const dataLine = block.split('\n').find(l => l.startsWith('data:'));
          
          if (!eventLine || !dataLine) continue;

          const eventType = eventLine.replace('event:', '').trim();
          const dataPayload = JSON.parse(dataLine.replace('data:', '').trim());

          if (eventType === 'hop') {
            setFeed(prev => [...prev, dataPayload]);
          } else if (eventType === 'dm') {
            setDms(prev => [...prev, dataPayload]);
          } else if (eventType === 'done') {
            setDriftSummary(dataPayload.drift_summary);
          }
        }
      }
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="app-container">
      <Navbar />
      <div className="main-content">
        <Sidebar />
        
        <Feed 
          onStartSimulation={startSimulation}
          feed={feed}
          isStreaming={isStreaming}
          originalText={originalText}
        />
        
        <InsightsPanel 
          dms={dms}
          driftSummary={driftSummary}
        />
      </div>
    </div>
  );
}

export default App;
