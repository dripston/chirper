import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Feed } from './components/Feed';
import { InsightsPanel } from './components/InsightsPanel';
import type { PostReaction, DirectMessage, DriftSummary } from './types';

function App() {
  const [originalText, setOriginalText] = useState('');
  const [feed, setFeed] = useState<PostReaction[]>([]);
  const [dms, setDms] = useState<DirectMessage[]>([]);
  const [driftSummary, setDriftSummary] = useState<DriftSummary | null>(null);
  const [liveDrift, setLiveDrift] = useState<{ score: number; label: string } | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activePersonaId, setActivePersonaId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [finalText, setFinalText] = useState<string | null>(null);

  const startSimulation = async (text: string, driftTarget: number | null, maxHops: number, timeLimit: number) => {
    setOriginalText(text);
    setFeed([]);
    setDms([]);
    setDriftSummary(null);
    setLiveDrift(null);
    setActivePersonaId(null);
    setErrorMsg(null);
    setFinalText(null);
    setIsStreaming(true);

    try {
      const response = await fetch('http://localhost:8000/post/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text, 
          drift_target: driftTarget || undefined,
          max_hops: maxHops,
          time_limit_seconds: timeLimit
        })
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
            setActivePersonaId(dataPayload.persona_id);
          } else if (eventType === 'dm') {
            setDms(prev => [...prev, dataPayload]);
          } else if (eventType === 'entropy_update') {
            setLiveDrift({ score: dataPayload.drift_score, label: dataPayload.drift_label });
          } else if (eventType === 'done') {
            setDriftSummary(dataPayload.drift_summary);
            setFinalText(dataPayload.drift_summary.final_text);
            setActivePersonaId(null);
          } else if (eventType === 'error') {
            setErrorMsg(dataPayload.message);
            setIsStreaming(false);
            setActivePersonaId(null);
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
        <Sidebar activePersonaId={activePersonaId} />
        
        <Feed 
          onStartSimulation={startSimulation}
          feed={feed}
          isStreaming={isStreaming}
          originalText={originalText}
          errorMsg={errorMsg}
          finalText={finalText}
        />
        
        <InsightsPanel 
          dms={dms}
          driftSummary={driftSummary}
          liveDrift={liveDrift}
        />
      </div>
    </div>
  );
}

export default App;
