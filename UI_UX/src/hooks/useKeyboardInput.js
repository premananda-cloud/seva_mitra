/**
 * src/hooks/useKeyboardInput.js
 * Attach to any <input ref={useKeyboardInput()}> to wire it into the
 * virtual keyboard. Focuses/blurs the global KeyboardContext automatically.
 */

import { useCallback, useEffect, useRef } from 'react';
import { useKeyboard } from '../context/KeyboardContext';

export function useKeyboardInput() {
  const { focusInput, blurInput } = useKeyboard();
  const inputRef = useRef(null);

  const refCallback = useCallback((el) => {
    inputRef.current = el;
  }, []);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;

    const onFocus = () => focusInput(el);
    const onBlur  = () => blurInput();

    el.addEventListener('focus', onFocus);
    el.addEventListener('blur',  onBlur);
    return () => {
      el.removeEventListener('focus', onFocus);
      el.removeEventListener('blur',  onBlur);
    };
  }, [focusInput, blurInput]);

  return refCallback;
}
