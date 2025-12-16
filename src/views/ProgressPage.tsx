import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export function ProgressPage() {
  return (
    <div className="flex w-full flex-col gap-4">
      <section>
        <h1 className="text-xl font-semibold">Your Progress</h1>
        <p className="text-sm text-muted-foreground">
          Track your improvement over time
        </p>
      </section>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Average Score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">—</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Complete sessions to see your average
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">0</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Practice sessions completed
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">
          Session History
        </h2>
        <Card>
          <CardContent className="py-6 text-sm text-muted-foreground">
            Your practice sessions will appear here. Complete your first
            interview to see your progress over time.
          </CardContent>
        </Card>
      </section>
    </div>
  );
}