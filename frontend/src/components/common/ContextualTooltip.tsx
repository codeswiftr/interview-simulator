import { useState, useRef, useEffect } from 'react';
import { Info, X } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ContextualTooltipProps {
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'always';
  className?: string;
  children?: React.ReactNode;
  title?: string;
}

export default function ContextualTooltip({
  content,
  position = 'top',
  trigger = 'hover',
  className,
  children,
  title,
}: ContextualTooltipProps) {
  const [isVisible, setIsVisible] = useState(trigger === 'always');
  const [isMobile, setIsMobile] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleMouseEnter = () => {
    if (trigger === 'hover' && !isMobile) {
      setIsVisible(true);
    }
  };

  const handleMouseLeave = () => {
    if (trigger === 'hover' && !isMobile) {
      setIsVisible(false);
    }
  };

  const handleClick = () => {
    if (trigger === 'click' || isMobile) {
      setIsVisible((prev) => !prev);
    }
  };

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-surface-secondary border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-surface-secondary border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-surface-secondary border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-surface-secondary border-t-transparent border-b-transparent border-l-transparent',
  };

  return (
    <div
      className={cn('relative inline-block', className)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    >
      {children || (
        <button
          type="button"
          className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-electric-blue/10 text-electric-blue hover:bg-electric-blue/20 transition-colors"
          aria-label={title || 'Show information'}
        >
          <Info size={14} />
        </button>
      )}

      {isVisible && (
        <div
          ref={tooltipRef}
          className={cn(
            'absolute z-50 px-3 py-2 text-sm text-text-primary bg-surface-secondary border border-border-light rounded-lg shadow-lg max-w-xs',
            'animate-fade-in',
            positionClasses[position]
          )}
          role="tooltip"
        >
          {/* Arrow */}
          <div
            className={cn(
              'absolute w-0 h-0 border-4',
              arrowClasses[position]
            )}
          />

          {/* Close button for mobile/click mode */}
          {(trigger === 'click' || isMobile) && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsVisible(false);
              }}
              className="absolute top-1 right-1 text-text-tertiary hover:text-text-primary transition-colors"
              aria-label="Close tooltip"
            >
              <X size={12} />
            </button>
          )}

          {/* Content */}
          <div className="pr-4">
            {title && (
              <div className="font-semibold mb-1 text-electric-blue">{title}</div>
            )}
            <div className="text-text-secondary">{content}</div>
          </div>
        </div>
      )}
    </div>
  );
}
