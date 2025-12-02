import './index.css';
import { Dashboard } from './pages/Dashboard';

import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import { ThemeSwitcher } from './components/ThemeSwitcher';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <Dashboard />
        <ThemeSwitcher />
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
