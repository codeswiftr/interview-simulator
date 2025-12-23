/**
 * Custom SVG illustrations for onboarding flow
 * Design: Recording studio aesthetic with electric-blue accent
 */

interface IllustrationProps {
  className?: string;
  animate?: boolean;
}

/**
 * Welcome illustration - Confident person with radiating aura
 * Represents confidence building and growth
 */
export function WelcomeIllustration({ className = '', animate = true }: IllustrationProps) {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Radiating circles - confidence aura */}
      <circle
        cx="100"
        cy="100"
        r="90"
        stroke="url(#welcome-gradient)"
        strokeWidth="1"
        opacity="0.15"
        className={animate ? 'animate-[ping_3s_ease-out_infinite]' : ''}
      />
      <circle
        cx="100"
        cy="100"
        r="70"
        stroke="url(#welcome-gradient)"
        strokeWidth="1.5"
        opacity="0.25"
        className={animate ? 'animate-[ping_3s_ease-out_infinite_0.5s]' : ''}
      />
      <circle
        cx="100"
        cy="100"
        r="50"
        stroke="url(#welcome-gradient)"
        strokeWidth="2"
        opacity="0.4"
        className={animate ? 'animate-[ping_3s_ease-out_infinite_1s]' : ''}
      />

      {/* Person silhouette - abstract */}
      <g className={animate ? 'animate-[pulse_4s_ease-in-out_infinite]' : ''}>
        {/* Head */}
        <circle cx="100" cy="70" r="20" fill="url(#welcome-gradient)" opacity="0.9" />
        {/* Body */}
        <path
          d="M75 95 L100 90 L125 95 L120 140 L80 140 Z"
          fill="url(#welcome-gradient)"
          opacity="0.8"
        />
        {/* Arms raised - victory pose */}
        <path
          d="M75 100 L55 70 M125 100 L145 70"
          stroke="url(#welcome-gradient)"
          strokeWidth="8"
          strokeLinecap="round"
          opacity="0.8"
        />
      </g>

      {/* Sparkles */}
      <circle cx="50" cy="50" r="3" fill="#38bdf8" opacity="0.8" className={animate ? 'animate-[pulse_2s_ease-in-out_infinite]' : ''} />
      <circle cx="150" cy="60" r="2" fill="#6366f1" opacity="0.6" className={animate ? 'animate-[pulse_2s_ease-in-out_infinite_0.3s]' : ''} />
      <circle cx="45" cy="120" r="2" fill="#38bdf8" opacity="0.5" className={animate ? 'animate-[pulse_2s_ease-in-out_infinite_0.6s]' : ''} />
      <circle cx="160" cy="130" r="3" fill="#6366f1" opacity="0.7" className={animate ? 'animate-[pulse_2s_ease-in-out_infinite_0.9s]' : ''} />

      <defs>
        <linearGradient id="welcome-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
    </svg>
  );
}

/**
 * Recording illustration - Microphone with soundwaves
 * Represents the recording experience
 */
export function RecordingIllustration({ className = '', animate = true }: IllustrationProps) {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Sound waves */}
      <g opacity="0.6">
        <path
          d="M40 100 Q40 60, 40 100 Q40 140, 40 100"
          stroke="#38bdf8"
          strokeWidth="3"
          strokeLinecap="round"
          className={animate ? 'animate-[soundwave_1s_ease-in-out_infinite]' : ''}
          style={{ transformOrigin: '40px 100px' }}
        />
        <path
          d="M55 100 Q55 50, 55 100 Q55 150, 55 100"
          stroke="#38bdf8"
          strokeWidth="3"
          strokeLinecap="round"
          opacity="0.8"
          className={animate ? 'animate-[soundwave_1s_ease-in-out_infinite_0.1s]' : ''}
          style={{ transformOrigin: '55px 100px' }}
        />
        <path
          d="M70 100 Q70 40, 70 100 Q70 160, 70 100"
          stroke="#38bdf8"
          strokeWidth="3"
          strokeLinecap="round"
          opacity="0.6"
          className={animate ? 'animate-[soundwave_1s_ease-in-out_infinite_0.2s]' : ''}
          style={{ transformOrigin: '70px 100px' }}
        />
      </g>

      {/* Microphone body */}
      <g className={animate ? 'animate-[float_3s_ease-in-out_infinite]' : ''}>
        {/* Mic head */}
        <rect x="90" y="50" width="40" height="60" rx="20" fill="url(#recording-gradient)" />
        {/* Grille lines */}
        <line x1="95" y1="65" x2="125" y2="65" stroke="#0f172a" strokeWidth="2" opacity="0.3" />
        <line x1="95" y1="75" x2="125" y2="75" stroke="#0f172a" strokeWidth="2" opacity="0.3" />
        <line x1="95" y1="85" x2="125" y2="85" stroke="#0f172a" strokeWidth="2" opacity="0.3" />
        <line x1="95" y1="95" x2="125" y2="95" stroke="#0f172a" strokeWidth="2" opacity="0.3" />
        {/* Mic stand */}
        <rect x="105" y="110" width="10" height="30" fill="url(#recording-gradient)" opacity="0.8" />
        <rect x="85" y="140" width="50" height="8" rx="4" fill="url(#recording-gradient)" opacity="0.6" />
      </g>

      {/* Right side waves */}
      <g opacity="0.6">
        <path
          d="M160 100 Q160 60, 160 100 Q160 140, 160 100"
          stroke="#6366f1"
          strokeWidth="3"
          strokeLinecap="round"
          className={animate ? 'animate-[soundwave_1s_ease-in-out_infinite]' : ''}
          style={{ transformOrigin: '160px 100px' }}
        />
        <path
          d="M145 100 Q145 50, 145 100 Q145 150, 145 100"
          stroke="#6366f1"
          strokeWidth="3"
          strokeLinecap="round"
          opacity="0.8"
          className={animate ? 'animate-[soundwave_1s_ease-in-out_infinite_0.1s]' : ''}
          style={{ transformOrigin: '145px 100px' }}
        />
        <path
          d="M130 100 Q130 40, 130 100 Q130 160, 130 100"
          stroke="#6366f1"
          strokeWidth="3"
          strokeLinecap="round"
          opacity="0.6"
          className={animate ? 'animate-[soundwave_1s_ease-in-out_infinite_0.2s]' : ''}
          style={{ transformOrigin: '130px 100px' }}
        />
      </g>

      <defs>
        <linearGradient id="recording-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
    </svg>
  );
}

/**
 * Growth illustration - Ascending chart with rocket
 * Represents progress and improvement
 */
export function GrowthIllustration({ className = '', animate = true }: IllustrationProps) {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Grid background */}
      <g opacity="0.1">
        {[40, 70, 100, 130, 160].map((y) => (
          <line key={`h-${y}`} x1="30" y1={y} x2="170" y2={y} stroke="#38bdf8" strokeWidth="1" />
        ))}
        {[40, 70, 100, 130, 160].map((x) => (
          <line key={`v-${x}`} x1={x} y1="30" x2={x} y2="170" stroke="#38bdf8" strokeWidth="1" />
        ))}
      </g>

      {/* Ascending bars */}
      <g>
        <rect x="45" y="130" width="20" height="40" rx="4" fill="url(#growth-gradient)" opacity="0.4" />
        <rect x="75" y="110" width="20" height="60" rx="4" fill="url(#growth-gradient)" opacity="0.6" />
        <rect x="105" y="85" width="20" height="85" rx="4" fill="url(#growth-gradient)" opacity="0.8" />
        <rect x="135" y="55" width="20" height="115" rx="4" fill="url(#growth-gradient)" />
      </g>

      {/* Trend line */}
      <path
        d="M55 125 L85 105 L115 75 L145 45"
        stroke="#38bdf8"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="200"
        strokeDashoffset={animate ? "0" : "200"}
        className={animate ? 'animate-[dash_2s_ease-out_forwards]' : ''}
      />

      {/* Star/goal at top */}
      <g className={animate ? 'animate-[pulse_2s_ease-in-out_infinite]' : ''}>
        <circle cx="145" cy="35" r="12" fill="url(#growth-gradient)" opacity="0.3" />
        <path
          d="M145 25 L147 32 L155 32 L149 37 L151 45 L145 40 L139 45 L141 37 L135 32 L143 32 Z"
          fill="#38bdf8"
        />
      </g>

      <defs>
        <linearGradient id="growth-gradient" x1="0%" y1="100%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#38bdf8" />
        </linearGradient>
      </defs>
    </svg>
  );
}

// Add CSS keyframes to globals.css:
// @keyframes soundwave {
//   0%, 100% { transform: scaleY(0.5); }
//   50% { transform: scaleY(1); }
// }
// @keyframes float {
//   0%, 100% { transform: translateY(0); }
//   50% { transform: translateY(-8px); }
// }
// @keyframes dash {
//   to { stroke-dashoffset: 0; }
// }
