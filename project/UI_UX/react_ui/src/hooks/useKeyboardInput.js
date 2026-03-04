import { useRef, useEffect } from 'react';
import { useKeyboard } from '../context/KeyboardContext';

export function useKeyboardInput(setter) {
  const inputRef = useRef(null);
  const { focusInput } = useKeyboard();

  useEffect(() => {
    const handleFocus = () => focusInput(inputRef.current, setter);
    const inputEl = inputRef.current;
    if (inputEl) {
      inputEl.addEventListener('focus', handleFocus);
    }
    return () => {
      if (inputEl) inputEl.removeEventListener('focus', handleFocus);
    };
  }, [focusInput, setter]);

  return inputRef;
}