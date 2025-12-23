import { useEffect, useState } from 'react';

interface TimerProps {
  startTime?: number;
  className?: string;
  variant?: 'elapsed' | 'countdown';
  maxSeconds?: number;
}

export default function Timer({
  startTime,
  className = '',
  variant = 'elapsed',
  maxSeconds
}: TimerProps) {
  const getSeconds = (): number => {
    if (!startTime) return 0;

    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    if (variant === 'countdown' && maxSeconds) {
      return Math.max(0, maxSeconds - elapsed);
    }
    return elapsed;
  };

  const [seconds, setSeconds] = useState(getSeconds);

  useEffect(() => {
    if (!startTime) {
      return;
    }

    const interval = setInterval(() => {
      setSeconds(getSeconds());
    }, 1000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startTime, variant, maxSeconds]);

  const formatTime = (totalSeconds: number): string => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className={`timer-display ${className}`}>
      {formatTime(seconds)}
    </div>
  );
}
