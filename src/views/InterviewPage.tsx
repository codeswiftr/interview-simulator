import { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../components/ui/drawer";
import { useInterviewStateMachine } from "../hooks/useInterviewStateMachine";
import { Lightbulb, Mic, Square } from "lucide-react";
import { cn } from "../lib/cn";

export function InterviewPage() {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [isMentorHintsOpen, setIsMentorHintsOpen] = useState(false);
  const {
    state,
    error,
    canRecord,
    canStop,
    canReset,
    requestPermission,
    grantPermission,
    denyPermission,
    startRecording,
    stopRecording,
    reset,
  } = useInterviewStateMachine();

  // Request microphone permission on mount
  useEffect(() => {
    if (state === "idle") {
      requestPermission();
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(() => grantPermission())
        .catch(() => denyPermission());
    }
  }, [state, requestPermission, grantPermission, denyPermission]);

  // Enter full-screen focus mode when recording
  useEffect(() => {
    if (state === "recording") {
      setIsFullScreen(true);
    } else if (state === "complete" || state === "error") {
      setIsFullScreen(false);
    }
  }, [state]);

  const handleRecord = () => {
    if (canRecord) {
      startRecording();
    } else if (canStop) {
      stopRecording();
    }
  };

  return (
    <div
      className={cn(
        "flex w-full flex-col gap-4 transition-all",
        isFullScreen && "fixed inset-0 z-50 bg-background"
      )}
    >
      {/* Timer + Progress bar (top-fixed when recording) */}
      {(state === "recording" || state === "processing") && (
        <div className="sticky top-0 z-40 border-b border-border bg-background/95 px-4 py-2 backdrop-blur">
          <div className="mx-auto flex max-w-md items-center justify-between">
            <span className="text-sm font-mono">
              {state === "recording" ? "00:45" : "Processing..."}
            </span>
            {state === "recording" && (
              <div className="h-1 w-24 rounded-full bg-muted">
                <div className="h-full w-3/4 animate-pulse rounded-full bg-primary" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Question text - Top, large readable font */}
      <Card className={cn(isFullScreen && "border-0 shadow-none")}>
        <CardHeader>
          <CardTitle className="text-lg">
            {state === "idle" || state === "requesting_permission"
              ? "Interview Practice"
              : "Current Question"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-dashed border-border p-4">
            <p className="text-base leading-relaxed">
              &ldquo;Tell me about a time you had to debug a production
              incident under pressure.&rdquo;
            </p>
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-500">
              {error}
            </div>
          )}

          {/* Recording controls - Bottom-center (thumb zone) */}
          <div className="fixed inset-x-0 bottom-16 z-30 mx-auto flex max-w-md items-center justify-center gap-3">
            {canRecord && (
              <Button
                size="fab"
                onClick={handleRecord}
                className="h-16 w-16 shadow-lg"
                aria-label="Start recording"
              >
                <Mic className="h-6 w-6" />
              </Button>
            )}
            {canStop && (
              <Button
                size="fab"
                onClick={handleRecord}
                variant="outline"
                className="h-16 w-16 border-2 border-red-500 shadow-lg"
                aria-label="Stop recording"
              >
                <Square className="h-6 w-6 fill-red-500 text-red-500" />
              </Button>
            )}
            {canReset && state !== "idle" && (
              <Button
                variant="ghost"
                onClick={reset}
                className="text-xs"
                aria-label="Reset interview"
              >
                Reset
              </Button>
            )}
          </div>

          {/* Mentor hints - Collapsible bottom sheet */}
          <Drawer open={isMentorHintsOpen} onOpenChange={setIsMentorHintsOpen}>
            <DrawerTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start gap-2"
                disabled={state === "idle" || state === "requesting_permission"}
              >
                <Lightbulb className="h-4 w-4" />
                <span>Get a hint</span>
              </Button>
            </DrawerTrigger>
            <DrawerContent>
              <DrawerHeader>
                <DrawerTitle>Mentor Hints</DrawerTitle>
                <DrawerDescription>
                  Helpful guidance for answering this question
                </DrawerDescription>
              </DrawerHeader>
              <div className="max-h-[60vh] space-y-3 overflow-y-auto px-4 pb-4">
                <div className="rounded-lg border border-border bg-muted/40 p-3 text-sm">
                  <p className="font-medium">Structure your answer:</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                    <li>Describe the situation and context</li>
                    <li>Explain the task and your responsibility</li>
                    <li>Detail the actions you took</li>
                    <li>Highlight the result and impact</li>
                  </ul>
                </div>
                <div className="rounded-lg border border-border bg-muted/40 p-3 text-sm">
                  <p className="font-medium">Key points to cover:</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                    <li>How you prioritized the issue</li>
                    <li>Your debugging process</li>
                    <li>How you communicated under pressure</li>
                    <li>The outcome and lessons learned</li>
                  </ul>
                </div>
              </div>
            </DrawerContent>
          </Drawer>
        </CardContent>
      </Card>
    </div>
  );
}
