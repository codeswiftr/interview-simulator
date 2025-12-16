import { Plus } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export function DashboardPage() {
  return (
    <div className="flex w-full flex-col gap-4">
      <section className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Welcome back</h1>
          <p className="text-sm text-muted-foreground">
            Track your practice and jump into your next session.
          </p>
        </div>
        <Button className="inline-flex items-center gap-2 rounded-full px-4 py-2">
          <Plus className="h-4 w-4" />
          <span>New practice</span>
        </Button>
      </section>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Readiness score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">—</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Complete a few sessions to see your score.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>This week</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">0 practice sessions</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Your recent sessions will appear here.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">
          Recent sessions
        </h2>
        <Card>
          <CardContent className="py-6 text-sm text-muted-foreground">
            You don&apos;t have any sessions yet. Start a new practice to see
            your history here.
          </CardContent>
        </Card>
      </section>

      {/* FAB - Fixed Action Button in thumb zone */}
      <Button
        size="fab"
        className="fixed bottom-20 right-4 z-30 shadow-lg md:bottom-24 md:right-8"
        aria-label="Start new practice session"
        title="Start new practice session"
      >
        <Plus className="h-6 w-6" />
      </Button>
    </div>
  );
}
