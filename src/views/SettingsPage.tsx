import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../components/ui/drawer";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Settings, Volume2 } from "lucide-react";

export function SettingsPage() {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [ttsRate, setTtsRate] = useState("normal");

  return (
    <div className="flex w-full flex-col gap-4">
      {/* Account Section */}
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Email</Label>
            <p className="text-sm text-muted-foreground">
              user@example.com
            </p>
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="email-notifications">
                Email notifications
              </Label>
              <p className="text-xs text-muted-foreground">
                Receive updates about your practice sessions
              </p>
            </div>
            <Switch
              id="email-notifications"
              checked={emailNotifications}
              onCheckedChange={setEmailNotifications}
            />
          </div>
        </CardContent>
      </Card>

      {/* Voice Preferences Section */}
      <Card>
        <CardHeader>
          <CardTitle>Voice preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="voice-enabled">
                Voice mentor
              </Label>
              <p className="text-xs text-muted-foreground">
                Enable AI voice responses
              </p>
            </div>
            <Switch
              id="voice-enabled"
              checked={voiceEnabled}
              onCheckedChange={setVoiceEnabled}
            />
          </div>

          {/* Voice Settings Drawer */}
          <Drawer>
            <DrawerTrigger asChild>
              <Button variant="outline" className="w-full justify-start gap-2">
                <Volume2 className="h-4 w-4" />
                <span>Voice settings</span>
              </Button>
            </DrawerTrigger>
            <DrawerContent>
              <DrawerHeader>
                <DrawerTitle>Voice Settings</DrawerTitle>
                <DrawerDescription>
                  Configure mentor voice, TTS rate, and audio options
                </DrawerDescription>
              </DrawerHeader>
              <div className="space-y-4 px-4 pb-4">
                <div className="space-y-2">
                  <Label>Voice</Label>
                  <Select defaultValue="female">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="female">Female</SelectItem>
                      <SelectItem value="male">Male</SelectItem>
                      <SelectItem value="neutral">Neutral</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Speech rate</Label>
                  <Select value={ttsRate} onValueChange={setTtsRate}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="slow">Slow</SelectItem>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="fast">Fast</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Audio preview</Label>
                    <p className="text-xs text-muted-foreground">
                      Test voice settings
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Play sample
                  </Button>
                </div>
              </div>
            </DrawerContent>
          </Drawer>
        </CardContent>
      </Card>

      {/* Appearance Section */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Dark mode will be available in a future update.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
