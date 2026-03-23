import { Home, Mic, BarChart2, Settings } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "../../lib/cn";

const items = [
  { to: "/dashboard", icon: Home, label: "Home" },
  { to: "/practice", icon: Mic, label: "Practice" },
  { to: "/progress", icon: BarChart2, label: "Progress" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function BottomNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-md items-center justify-between px-4 py-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex flex-1 flex-col items-center gap-1 text-xs text-muted-foreground",
                  isActive && "text-primary"
                )
              }
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
