/**
 * src/context/KeyboardContext.jsx
 * Global virtual keyboard state — tracks which input is active.
 * App.jsx renders <Keyboard> when activeInput is set.
 */

import { createContext, useContext, useRef, useState } from 'react';

const KeyboardContext = createContext(null);

export function KeyboardProvider({ children }) {
  const [activeInput, setActiveInput] = useState(null); // ref to focused input
  const activeRef = useRef(null);

  const focusInput = (inputRef) => {
    activeRef.current = inputRef;
    setActiveInput(inputRef);
  };

  const blurInput = () => {
    activeRef.current = null;
    setActiveInput(null);
  };

  const handleKeyPress = (key) => {
    const el = activeRef.current;
    if (!el) return;

    const { value, selectionStart: start, selectionEnd: end } = el;

    if (key === 'Backspace') {
      if (start === end && start > 0) {
        const next = value.slice(0, start - 1) + value.slice(end);
        setNativeValue(el, next, start - 1);
      } else if (start !== end) {
        const next = value.slice(0, start) + value.slice(end);
        setNativeValue(el, next, start);
      }
    } else if (key === 'Clear') {
      setNativeValue(el, '', 0);
    } else {
      const next = value.slice(0, start) + key + value.slice(end);
      setNativeValue(el, next, start + key.length);
    }
  };

  return (
    <KeyboardContext.Provider value={{ activeInput, focusInput, blurInput, handleKeyPress }}>
      {children}
    </KeyboardContext.Provider>
  );
}

export function useKeyboard() {
  const ctx = useContext(KeyboardContext);
  if (!ctx) throw new Error('useKeyboard must be used inside <KeyboardProvider>');
  return ctx;
}

// Trigger React's synthetic onChange by using the native input value setter
function setNativeValue(el, value, cursor) {
  const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set
    || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
  nativeSetter?.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  requestAnimationFrame(() => {
    el.focus();
    el.setSelectionRange(cursor, cursor);
  });
}
