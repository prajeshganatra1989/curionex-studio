import {
  CirclePlay,
  Factory,
  FolderKanban,
  LayoutDashboard,
  Library,
  Settings,
  BookOpen,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

/** Primary daily workflow first; Projects kept as an implementation detail. */
export const MAIN_NAV: NavItem[] = [
  { href: "/production/session", label: "Session", icon: CirclePlay },
  { href: "/production", label: "Production", icon: Factory },
  { href: "/topics", label: "Topics", icon: Library },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/knowledge-packs", label: "Knowledge Packs", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];
