import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { ScoreRing } from "../components/ui/score-ring";

export function FeedbackPage() {
  return (
    <div className="flex w-full flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Session feedback</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Score summary - Swipeable cards (Overall → Content → Delivery) */}
          <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
            <div className="min-w-[140px] flex-shrink-0 rounded-lg border border-border bg-muted/40 p-4 flex flex-col items-center gap-2">
              <ScoreRing value={85} size="md" label="Overall" />
            </div>
            <div className="min-w-[140px] flex-shrink-0 rounded-lg border border-border bg-muted/40 p-4 flex flex-col items-center gap-2">
              <ScoreRing value={88} size="md" label="Content" />
            </div>
            <div className="min-w-[140px] flex-shrink-0 rounded-lg border border-border bg-muted/40 p-4 flex flex-col items-center gap-2">
              <ScoreRing value={82} size="md" label="Delivery" />
            </div>
          </div>

          {/* Detailed feedback - Tap to expand (progressive disclosure) */}
          <details className="rounded-lg border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
            <summary className="cursor-pointer text-foreground font-medium">
              Strengths
            </summary>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Structured answers using STAR method effectively.</li>
              <li>Clear description of impact and outcomes.</li>
              <li>Good use of technical terminology.</li>
            </ul>
          </details>
          <details className="rounded-lg border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
            <summary className="cursor-pointer text-foreground font-medium">
              Improvement areas
            </summary>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Slow down when explaining tradeoffs for clarity.</li>
              <li>Bring in more concrete metrics to quantify impact.</li>
              <li>Practice transitions between topics.</li>
            </ul>
          </details>

          {/* Next steps - Fixed bottom CTA */}
          <div className="fixed inset-x-0 bottom-16 z-30 mx-auto max-w-md px-4">
            <Button className="w-full shadow-lg">Practice Again</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
