import { useReducer, useCallback } from "react";

export type InterviewState =
  | "idle"
  | "requesting_permission"
  | "ready"
  | "recording"
  | "processing"
  | "complete"
  | "error";

type InterviewAction =
  | { type: "REQUEST_PERMISSION" }
  | { type: "PERMISSION_GRANTED" }
  | { type: "PERMISSION_DENIED" }
  | { type: "START_RECORDING" }
  | { type: "STOP_RECORDING" }
  | { type: "PROCESSING_START" }
  | { type: "PROCESSING_COMPLETE" }
  | { type: "RESET" }
  | { type: "ERROR"; error: string };

interface InterviewStateMachine {
  state: InterviewState;
  error: string | null;
  canRecord: boolean;
  canStop: boolean;
  canReset: boolean;
}

const initialState: InterviewStateMachine = {
  state: "idle",
  error: null,
  canRecord: false,
  canStop: false,
  canReset: false,
};

function interviewReducer(
  state: InterviewStateMachine,
  action: InterviewAction
): InterviewStateMachine {
  switch (action.type) {
    case "REQUEST_PERMISSION":
      return {
        ...state,
        state: "requesting_permission",
        canRecord: false,
        canStop: false,
        canReset: true,
      };
    case "PERMISSION_GRANTED":
      return {
        ...state,
        state: "ready",
        canRecord: true,
        canStop: false,
        canReset: true,
        error: null,
      };
    case "PERMISSION_DENIED":
      return {
        ...state,
        state: "error",
        error: "Microphone permission denied",
        canRecord: false,
        canStop: false,
        canReset: true,
      };
    case "START_RECORDING":
      if (state.state === "ready") {
        return {
          ...state,
          state: "recording",
          canRecord: false,
          canStop: true,
          canReset: true,
          error: null,
        };
      }
      return state;
    case "STOP_RECORDING":
      if (state.state === "recording") {
        return {
          ...state,
          state: "processing",
          canRecord: false,
          canStop: false,
          canReset: true,
        };
      }
      return state;
    case "PROCESSING_COMPLETE":
      return {
        ...state,
        state: "complete",
        canRecord: false,
        canStop: false,
        canReset: true,
      };
    case "RESET":
      return {
        ...initialState,
        canReset: false,
      };
    case "ERROR":
      return {
        ...state,
        state: "error",
        error: action.error,
        canRecord: false,
        canStop: false,
        canReset: true,
      };
    default:
      return state;
  }
}

export function useInterviewStateMachine() {
  const [machine, dispatch] = useReducer(interviewReducer, initialState);

  const requestPermission = useCallback(() => {
    dispatch({ type: "REQUEST_PERMISSION" });
  }, []);

  const grantPermission = useCallback(() => {
    dispatch({ type: "PERMISSION_GRANTED" });
  }, []);

  const denyPermission = useCallback(() => {
    dispatch({ type: "PERMISSION_DENIED" });
  }, []);

  const startRecording = useCallback(() => {
    dispatch({ type: "START_RECORDING" });
  }, []);

  const stopRecording = useCallback(() => {
    dispatch({ type: "STOP_RECORDING" });
  }, []);

  const completeProcessing = useCallback(() => {
    dispatch({ type: "PROCESSING_COMPLETE" });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const setError = useCallback((error: string) => {
    dispatch({ type: "ERROR", error });
  }, []);

  return {
    state: machine.state,
    error: machine.error,
    canRecord: machine.canRecord,
    canStop: machine.canStop,
    canReset: machine.canReset,
    requestPermission,
    grantPermission,
    denyPermission,
    startRecording,
    stopRecording,
    completeProcessing,
    reset,
    setError,
  };
}
