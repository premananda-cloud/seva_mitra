import React, { createContext, useContext, useState, useRef, useCallback } from 'react';

const KeyboardContext = createContext();

export function KeyboardProvider({ children }) {
  const [activeInput, setActiveInput] = useState(null);
  const inputRef = useRef(null);
  const [valueSetter, setValueSetter] = useState(null); // new

  const focusInput = useCallback((ref, setter) => {
    inputRef.current = ref;
    setValueSetter(() => setter); // store the setter
    setActiveInput(ref);
  }, []);

  const blurInput = useCallback(() => {
    setActiveInput(null);
    inputRef.current = null;
    setValueSetter(null);
  }, []);

  const insertChar = useCallback((char) => {
    if (!inputRef.current || !valueSetter) return;
    const input = inputRef.current;
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const currentValue = input.value;
    const newValue = currentValue.substring(0, start) + char + currentValue.substring(end);
    valueSetter(newValue); // update React state
    // After state update, cursor will be reset; we need to restore it after render
    setTimeout(() => {
      input.focus();
      input.setSelectionRange(start + char.length, start + char.length);
    }, 0);
  }, [valueSetter]);

  const handleBackspace = useCallback(() => {
    if (!inputRef.current || !valueSetter) return;
    const input = inputRef.current;
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const currentValue = input.value;
    let newValue;
    let newCursor = start;
    if (start === end && start > 0) {
      newValue = currentValue.substring(0, start - 1) + currentValue.substring(end);
      newCursor = start - 1;
    } else if (start !== end) {
      newValue = currentValue.substring(0, start) + currentValue.substring(end);
      newCursor = start;
    } else return;
    valueSetter(newValue);
    setTimeout(() => {
      input.focus();
      input.setSelectionRange(newCursor, newCursor);
    }, 0);
  }, [valueSetter]);

  const handleClear = useCallback(() => {
    if (!valueSetter) return;
    valueSetter('');
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [valueSetter]);

  const handleKeyPress = useCallback((key) => {
    if (key === 'Backspace') handleBackspace();
    else if (key === 'Clear') handleClear();
    else if (key === 'Close') blurInput();
    else if (key === ' ') insertChar(' ');
    else insertChar(key);
  }, [handleBackspace, handleClear, insertChar, blurInput]);

  return (
    <KeyboardContext.Provider value={{ activeInput, focusInput, blurInput, handleKeyPress }}>
      {children}
    </KeyboardContext.Provider>
  );
}

export function useKeyboard() {
  return useContext(KeyboardContext);
}