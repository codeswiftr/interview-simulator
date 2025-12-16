import { useState } from "react";
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
import { Textarea } from "../components/ui/textarea";
import { MessageSquare, Mic, Volume2 } from "lucide-react";

export function PreparationPage() {
  const [isQASheetOpen, setIsQASheetOpen] = useState(false);

  return (
    <div className="flex w-full flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Preparation mentor</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Q&A conversation - Bottom sheet (expandable) */}
          <Drawer open={isQASheetOpen} onOpenChange={setIsQASheetOpen}>
            <DrawerTrigger asChild>
              <Button variant="outline" className="w-full justify-start gap-2">
                <MessageSquare className="h-4 w-4" />
                <span>Ask your mentor</span>
              </Button>
            </DrawerTrigger>
            <DrawerContent>
              <DrawerHeader>
                <DrawerTitle>Mentor Q&A</DrawerTitle>
                <DrawerDescription>
                  Ask questions about the question you&apos;re preparing for
                </DrawerDescription>
              </DrawerHeader>
              <div className="max-h-[60vh] space-y-4 overflow-y-auto px-4 pb-4">
                <div className="space-y-2">
                  <div className="rounded-lg bg-muted/40 p-3 text-sm">
                    <p className="font-medium">Mentor:</p>
                    <p className="mt-1 text-muted-foreground">
                      &ldquo;What specific tradeoffs did you consider when
                      designing this system?&rdquo;
                    </p>
                  </div>
                  <div className="ml-auto max-w-[80%] rounded-lg bg-primary/10 p-3 text-sm">
                    <p className="font-medium">You:</p>
                    <p className="mt-1">
                      I considered latency vs. consistency. I chose eventual
                      consistency to prioritize response time.
                    </p>
                  </div>
                </div>
              </div>
            </DrawerContent>
          </Drawer>

          {/* Draft editor - Main content area */}
          <div className="rounded-lg border border-dashed border-border p-4">
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Mentor question
            </p>
            <p className="text-sm">
              &ldquo;Walk me through a recent system you designed and a tradeoff
              you had to make.&rdquo;
            </p>
          </div>
          <Textarea
            className="mt-2 h-32 resize-none"
            placeholder="Draft your answer here..."
          />

          {/* Voice controls - Fixed bottom bar (thumb zone) */}
          <div className="fixed inset-x-0 bottom-16 z-30 mx-auto flex max-w-md items-center justify-between gap-3 rounded-full border border-border bg-background/95 px-4 py-2 shadow-lg backdrop-blur">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle mentor voice"
            >
              <Volume2 className="h-4 w-4" />
            </Button>
            <Button className="flex-1 gap-2">
              <Mic className="h-4 w-4" />
              <span>Start speaking</span>
            </Button>
            <Button variant="ghost" size="icon" aria-label="More options">
              ⋯
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
