import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Web Speech API Hook für Spracheingabe (deutsch).
 * Gibt den erkannten Text und den Status zurück.
 */

interface UseSpeechRecognitionReturn {
  /** Ob gerade zugehört wird */
  isListening: boolean;
  /** Der erkannte Text */
  transcript: string;
  /** Ob die Web Speech API verfügbar ist */
  isSupported: boolean;
  /** Fehler-Nachricht */
  error: string | null;
  /** Aufnahme starten */
  startListening: () => void;
  /** Aufnahme stoppen */
  stopListening: () => void;
  /** Transcript zurücksetzen */
  resetTranscript: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Browser-Compat: SpeechRecognition nicht überall getypt
type SpeechRecognitionInstance = any;

function getSpeechRecognitionClass(): (new () => SpeechRecognitionInstance) | null {
  if (typeof window === 'undefined') return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Browser-Compat
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const SpeechRecognitionClass = getSpeechRecognitionClass();
  const isSupported = SpeechRecognitionClass !== null;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  // Aufräumen bei Unmount
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognitionClass) {
      setError('Spracheingabe wird von diesem Browser nicht unterstützt.');
      return;
    }

    setError(null);
    const recognition = new SpeechRecognitionClass();
    recognition.lang = 'de-DE';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Browser SpeechRecognition Event
    recognition.onresult = (event: any) => {
      let finalText = '';
      let interimText = '';
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
        } else {
          interimText += result[0].transcript;
        }
      }
      setTranscript(finalText || interimText);
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Browser SpeechRecognition Error
    recognition.onerror = (event: any) => {
      if (event.error === 'aborted') return;
      const errorMessages: Record<string, string> = {
        'not-allowed': 'Mikrofon-Zugriff wurde verweigert.',
        'no-speech': 'Keine Sprache erkannt.',
        'audio-capture': 'Kein Mikrofon gefunden.',
        network: 'Netzwerkfehler bei der Spracherkennung.',
      };
      setError(errorMessages[event.error] ?? `Spracherkennungsfehler: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [SpeechRecognitionClass]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return {
    isListening,
    transcript,
    isSupported,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
}
