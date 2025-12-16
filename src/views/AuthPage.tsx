import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

export function AuthPage() {
  return (
    <div className="flex w-full flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Email" type="email" />
          <Input placeholder="Password" type="password" />
          <Button className="mt-2 w-full">Continue</Button>
        </CardContent>
      </Card>
    </div>
  );
}
