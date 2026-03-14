/**
 * src/context/KeyboardContext.jsx
 *
 * Global virtual keyboard — auto-wires to EVERY input/textarea in the app
 * via document-level focusin/focusout listeners. No per-input ref needed.
 *
 * Excluded: type="date", type="time", type="number", type="file",
 *           inputs inside #keyboard itself (prevent infinite loop).
 */

import { createContext, useContext, useRef, useState, useEffect } from 'react';

const KeyboardContext = createContext(null);

const EXCLUDED_TYPES = new Set(['date', 'time', 'number', 'file', 'range', 'color', 'checkbox', 'radio', 'submit', 'button', 'reset', 'hidden']);

function shouldShowKeyboard(el) {
  if (!el) return false;
  const tag = el.tagName;
  if (tag !== 'INPUT' && tag !== 'TEXTAREA') return false;
  if (EXCLUDED_TYPES.has(el.type?.toLowerCase())) return false;
  // Don't trigger if the input is inside the keyboard itself
  if (el.closest('#keyboard-container')) return false;
  return true;
}

// Trigger React's synthetic onChange via native value setter
function setNativeValue(el, value, cursor) {
  const proto = el.tagName === 'TEXTAREA'
    ? window.HTMLTextAreaElement.prototype
    : window.HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
  setter?.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  requestAnimationFrame(() => {
    try { el.focus(); el.setSelectionRange(cursor, cursor); } catch {}
  });
}

export function KeyboardProvider({ children }) {
  const [activeInput, setActiveInput] = useState(null);
  const activeRef = useRef(null);

  useEffect(() => {
    function onFocusIn(e) {
      if (shouldShowKeyboard(e.target)) {
        activeRef.current = e.target;
        setActiveInput(e.target);
      }
    }
    function onFocusOut(e) {
      // Delay slightly — if focus moves to keyboard button, we keep the input active
      setTimeout(() => {
        const focused = document.activeElement;
        if (!shouldShowKeyboard(focused) && !focused?.closest('#keyboard-container')) {
          activeRef.current = null;
          setActiveInput(null);
        }
      }, 120);
    }
    document.addEventListener('focusin',  onFocusIn);
    document.addEventListener('focusout', onFocusOut);
    return () => {
      document.removeEventListener('focusin',  onFocusIn);
      document.removeEventListener('focusout', onFocusOut);
    };
  }, []);

  const handleKeyPress = (key) => {
    const el = activeRef.current;
    if (!el) return;

    const value = el.value;
    let start, end;
    try {
      start = el.selectionStart ?? value.length;
      end   = el.selectionEnd   ?? value.length;
    } catch {
      start = end = value.length;
    }

    if (key === 'Backspace') {
      if (start === end && start > 0) {
        setNativeValue(el, value.slice(0, start - 1) + value.slice(end), start - 1);
      } else if (start !== end) {
        setNativeValue(el, value.slice(0, start) + value.slice(end), start);
      }
    } else if (key === 'Clear') {
      setNativeValue(el, '', 0);
    } else {
      const next = value.slice(0, start) + key + value.slice(end);
      setNativeValue(el, next, start + key.length);
    }
  };

  const blurInput = () => {
    activeRef.current = null;
    setActiveInput(null);
  };

  // kept for backward compatibility with useKeyboardInput hook callers
  const focusInput = (el) => {
    activeRef.current = el;
    setActiveInput(el);
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
