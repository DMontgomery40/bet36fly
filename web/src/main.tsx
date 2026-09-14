import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './style.css';
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: boolean }> {
  state = { error: false };
  static getDerivedStateFromError() { return { error: true }; }
  render() { return this.state.error ? <main className="fatal"><h1>The research application couldn’t render.</h1><p>Reload to reconnect to the frozen confirmation evidence.</p><button onClick={() => window.location.reload()}>Reload</button></main> : this.props.children; }
}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><ErrorBoundary><App /></ErrorBoundary></React.StrictMode>);
