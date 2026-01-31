import { useState, useEffect, useCallback, useRef } from 'react';

export interface TimerPhase {
  type: 'focus' | 'break';
  minutes: number;
}

interface UseTimerOptions {
  onPhaseComplete?: (phase: TimerPhase) => void;
  onSessionComplete?: () => void;
  onTick?: (remainingSeconds: number) => void;
}

interface UseTimerReturn {
  minutes: number;
  seconds: number;
  isRunning: boolean;
  isPaused: boolean;
  currentPhase: TimerPhase | null;
  currentRound: number;
  totalRounds: number;
  start: (phases: TimerPhase[]) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  skip: () => void;
}

export const useTimer = (options: UseTimerOptions = {}): UseTimerReturn => {
  const [phases, setPhases] = useState<TimerPhase[]>([]);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const optionsRef = useRef(options);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const currentPhase = phases[currentPhaseIndex] || null;

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;

  const clearTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const moveToNextPhase = useCallback(() => {
    const { onPhaseComplete, onSessionComplete } = optionsRef.current;

    if (currentPhase && onPhaseComplete) {
      onPhaseComplete(currentPhase);
    }

    if (currentPhaseIndex >= phases.length - 1) {
      // Session complete
      clearTimer();
      setIsRunning(false);
      setIsPaused(false);
      if (onSessionComplete) {
        onSessionComplete();
      }
    } else {
      // Move to next phase
      const nextIndex = currentPhaseIndex + 1;
      setCurrentPhaseIndex(nextIndex);
      setRemainingSeconds(phases[nextIndex].minutes * 60);
    }
  }, [currentPhase, currentPhaseIndex, phases, clearTimer]);

  useEffect(() => {
    if (isRunning && !isPaused && remainingSeconds > 0) {
      intervalRef.current = setInterval(() => {
        setRemainingSeconds((prev) => {
          const newValue = prev - 1;
          if (optionsRef.current.onTick) {
            optionsRef.current.onTick(newValue);
          }
          return newValue;
        });
      }, 1000);
    } else {
      clearTimer();
    }

    return clearTimer;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRunning, isPaused, clearTimer]);

  useEffect(() => {
    if (isRunning && !isPaused && remainingSeconds === 0 && phases.length > 0) {
      moveToNextPhase();
    }
  }, [remainingSeconds, isRunning, isPaused, phases.length, moveToNextPhase]);

  const start = useCallback((newPhases: TimerPhase[]) => {
    if (newPhases.length === 0) return;

    setPhases(newPhases);
    setCurrentPhaseIndex(0);
    setRemainingSeconds(newPhases[0].minutes * 60);
    setIsRunning(true);
    setIsPaused(false);
  }, []);

  const pause = useCallback(() => {
    setIsPaused(true);
  }, []);

  const resume = useCallback(() => {
    setIsPaused(false);
  }, []);

  const stop = useCallback(() => {
    clearTimer();
    setIsRunning(false);
    setIsPaused(false);
    setPhases([]);
    setCurrentPhaseIndex(0);
    setRemainingSeconds(0);
  }, [clearTimer]);

  const skip = useCallback(() => {
    if (isRunning) {
      moveToNextPhase();
    }
  }, [isRunning, moveToNextPhase]);

  // Calculate rounds (focus phases count)
  const focusPhases = phases.filter(p => p.type === 'focus');
  const completedFocusPhases = phases
    .slice(0, currentPhaseIndex)
    .filter(p => p.type === 'focus').length;
  const currentRound = currentPhase?.type === 'focus'
    ? completedFocusPhases + 1
    : completedFocusPhases;
  const totalRounds = focusPhases.length;

  return {
    minutes,
    seconds,
    isRunning,
    isPaused,
    currentPhase,
    currentRound,
    totalRounds,
    start,
    pause,
    resume,
    stop,
    skip,
  };
};
