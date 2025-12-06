import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export function ThemeSlider() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center justify-between p-2 bg-surface-tertiary rounded-lg">
      <button
        onClick={() => setTheme('light')}
        className={`flex-1 flex items-center justify-center p-1.5 rounded-md transition-all ${
          theme === 'light'
            ? 'bg-white text-electric-blue shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        title="Light Mode"
      >
        <Sun size={16} />
      </button>
      <button
        onClick={() => setTheme('system')}
        className={`flex-1 flex items-center justify-center p-1.5 rounded-md transition-all ${
          theme === 'system'
            ? 'bg-white text-electric-blue shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        title="System Preference"
      >
        <Monitor size={16} />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={`flex-1 flex items-center justify-center p-1.5 rounded-md transition-all ${
          theme === 'dark'
            ? 'bg-white text-electric-blue shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        title="Dark Mode"
      >
        <Moon size={16} />
      </button>
    </div>
  );
}
