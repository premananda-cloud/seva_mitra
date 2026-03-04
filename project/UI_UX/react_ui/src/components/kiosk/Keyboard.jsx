import React from 'react';

const LAYOUT = [
  ['1','2','3','4','5','6','7','8','9','0'],
  ['q','w','e','r','t','y','u','i','o','p'],
  ['a','s','d','f','g','h','j','k','l'],
  ['z','x','c','v','b','n','m'],
  [' ', 'Backspace', 'Clear', 'Close']
];

const keyDisplay = {
  ' ': '␣ Space',
  'Backspace': '⌫',
  'Clear': '✕',
  'Close': '▼'
};

export default function Keyboard({ onKeyPress, onClose }) {
  const handleClick = (key) => {
    if (key === 'Close') {
      onClose?.();
      return;
    }
    onKeyPress?.(key);
  };

  const handleMouseDown = (e) => {
    // Prevent button from stealing focus from input
    e.preventDefault();
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 animate-slide-up">
      <div className="bg-koisk-navy/70 backdrop-blur-lg border-t border-white/20 shadow-2xl px-2 py-4 sm:px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col items-center gap-2">
            {LAYOUT.map((row, i) => (
              <div key={i} className="flex justify-center gap-1.5 sm:gap-2 w-full flex-wrap">
                {row.map((key) => {
                  const isSpace = key === ' ';
                  const isSpecial = ['Backspace', 'Clear', 'Close'].includes(key);
                  return (
                    <button
                      key={key}
                      onClick={() => handleClick(key)}
                      onMouseDown={handleMouseDown}
                      className={`
                        flex items-center justify-center
                        font-medium text-white/90
                        rounded-xl shadow-md
                        transition-all duration-100
                        focus:outline-none focus:ring-2 focus:ring-koisk-teal/50
                        active:scale-95 active:bg-white/20
                        ${isSpace
                          ? 'w-40 sm:w-48 bg-white/10 hover:bg-white/20 text-base'
                          : isSpecial
                          ? 'w-16 sm:w-20 bg-koisk-teal/20 hover:bg-koisk-teal/30 text-sm sm:text-base'
                          : 'w-10 sm:w-12 bg-white/5 hover:bg-white/15 text-base sm:text-lg'
                        }
                        py-3 sm:py-4
                      `}
                    >
                      {keyDisplay[key] || key}
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