import {
  LayoutDashboard,
  Film,
  Tv,
  Bookmark,
  History,
  FolderKanban,
  Settings,
  Library,
  Sparkles,
  Bot,
  UploadCloud,
  type LucideIcon,
} from "lucide-react";

export interface NavigationItem {
  name: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

export const navigationItems: NavigationItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "AI Oracle", href: "/oracle", icon: Bot, badge: "Oracle" },
  { name: "Movies", href: "/movies", icon: Film },
  { name: "Series", href: "/series", icon: Tv },
  { name: "Social & Match", href: "/social", icon: Sparkles, badge: "AI" },
  { name: "Library", href: "/library", icon: Library },
  { name: "Watchlist", href: "/watchlist", icon: Bookmark },
  { name: "History", href: "/history", icon: History },
  { name: "Collections", href: "/collections", icon: FolderKanban },
  { name: "Import", href: "/import", icon: UploadCloud },
  { name: "Settings", href: "/settings", icon: Settings },
];
