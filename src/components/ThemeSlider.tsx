import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

type ThemeOption = 'light' | 'system' | 'dark';

export function ThemeSlider() {
  const { theme, setTheme } = useTheme();

  const handleKeyDown = (e: React.KeyboardEvent, currentTheme: ThemeOption) => {
    const themes: ThemeOption[] = ['light', 'system', 'dark'];
    const currentIndex = themes.indexOf(currentTheme);

    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % themes.length;
      setTheme(themes[nextIndex]);
      // Focus will stay on the radiogroup, which is appropriate
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + themes.length) % themes.length;
      setTheme(themes[prevIndex]);
    }
  };

  return (
    <div
      role="radiogroup"
      aria-label="Theme selection"
      className="flex items-center justify-between p-2 bg-surface-tertiary rounded-lg"
    >
      <button
        role="radio"
        aria-checked={theme === 'light'}
        onClick={() => setTheme('light')}
        onKeyDown={(e) => handleKeyDown(e, 'light')}
        className={`flex-1 flex items-center justify-center p-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2 ${
          theme === 'light'
            ? 'bg-white text-electric-blue shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        aria-label="Light mode"
        tabIndex={theme === 'light' ? 0 : -1}
      >
        <Sun size={16} aria-hidden="true" />
      </button>
      <button
        role="radio"
        aria-checked={theme === 'system'}
        onClick={() => setTheme('system')}
        onKeyDown={(e) => handleKeyDown(e, 'system')}
        className={`flex-1 flex items-center justify-center p-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2 ${
          theme === 'system'
            ? 'bg-white text-electric-blue shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        aria-label="System preference"
        tabIndex={theme === 'system' ? 0 : -1}
      >
        <Monitor size={16} aria-hidden="true" />
      </button>
      <button
        role="radio"
        aria-checked={theme === 'dark'}
        onClick={() => setTheme('dark')}
        onKeyDown={(e) => handleKeyDown(e, 'dark')}
        className={`flex-1 flex items-center justify-center p-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2 ${
          theme === 'dark'
            ? 'bg-white text-electric-blue shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        aria-label="Dark mode"
        tabIndex={theme === 'dark' ? 0 : -1}
      >
        <Moon size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
