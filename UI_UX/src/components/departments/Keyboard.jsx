import React, { useState } from 'react';

const LOWER = [
  ['1','2','3','4','5','6','7','8','9','0'],
  ['q','w','e','r','t','y','u','i','o','p'],
  ['a','s','d','f','g','h','j','k','l'],
  ['z','x','c','v','b','n','m'],
  ['Shift', ' ', '@', '.', 'Backspace', 'Clear', 'Close'],
];

const UPPER = [
  ['1','2','3','4','5','6','7','8','9','0'],
  ['Q','W','E','R','T','Y','U','I','O','P'],
  ['A','S','D','F','G','H','J','K','L'],
  ['Z','X','C','V','B','N','M'],
  ['Shift', ' ', '@', '.', 'Backspace', 'Clear', 'Close'],
];

const SPECIAL_DISPLAY = {
  ' ':         '␣ Space',
  'Backspace':  '⌫',
  'Clear':      '✕ Clear',
  'Close':      '▼ Done',
  'Shift':      '⇧ Shift',
  '@':          '@',
  '.':          '.',
};

const SPECIAL_KEYS = ['Backspace', 'Clear', 'Close', 'Shift', ' ', '@', '.'];

export default function Keyboard({ onKeyPress, onClose }) {
  const [shifted, setShifted] = useState(false);
  const layout = shifted ? UPPER : LOWER;

  const handleClick = (key) => {
    if (key === 'Close')  { onClose?.(); return; }
    if (key === 'Shift')  { setShifted(s => !s); return; }
    onKeyPress?.(key);
    // Auto-unshift after a letter key
    if (shifted && key.length === 1 && key !== '@' && key !== '.') {
      setShifted(false);
    }
  };

  const handleMouseDown = (e) => e.preventDefault();

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50"
      role="dialog"
      aria-label="On-screen keyboard"
      aria-modal="false"
    >
      <div className="bg-koisk-navy/85 backdrop-blur-lg border-t border-white/20 shadow-2xl px-2 py-3 sm:px-4 sm:py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col items-center gap-1.5 sm:gap-2">
            {layout.map((row, i) => (
              <div key={i} className="flex justify-center gap-1 sm:gap-1.5 w-full flex-wrap">
                {row.map((key) => {
                  const isSpace   = key === ' ';
                  const isSpecial = SPECIAL_KEYS.includes(key);
                  const isShift   = key === 'Shift';
                  const isClose   = key === 'Close';
                  const isActive  = isShift && shifted;
                  return (
                    <button
                      key={key}
                      onClick={() => handleClick(key)}
                      onMouseDown={handleMouseDown}
                      aria-label={SPECIAL_DISPLAY[key] ?? key}
                      aria-pressed={isShift ? shifted : undefined}
                      className={[
                        'flex items-center justify-center font-medium rounded-xl shadow-md',
                        'transition-all duration-100 active:scale-95',
                        'focus:outline-none focus:ring-2 focus:ring-koisk-teal/50',
                        'py-3 sm:py-3.5 text-sm sm:text-base',
                        isSpace  ? 'w-28 sm:w-36 bg-white/10 hover:bg-white/20 text-white/90'
                        : isClose  ? 'w-20 sm:w-24 bg-koisk-teal/30 hover:bg-koisk-teal/50 text-white font-semibold'
                        : isActive ? 'w-16 sm:w-20 bg-koisk-accent text-koisk-navy font-bold'
                        : isSpecial? 'w-16 sm:w-20 bg-white/15 hover:bg-white/25 text-white/80'
                        :            'w-9 sm:w-11 bg-white/8 hover:bg-white/18 text-white/90',
                      ].join(' ')}
                    >
                      {SPECIAL_DISPLAY[key] ?? key}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
