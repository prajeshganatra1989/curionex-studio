import {
  Activity,
  CheckSquare,
  FileText,
  FolderKanban,
  Layers3,
  LayoutDashboard,
  Settings,
  BookOpen,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

export const MAIN_NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/knowledge-packs", label: "Knowledge Packs", icon: BookOpen },
  { href: "/scripts", label: "Scripts", icon: FileText },
  { href: "/versions", label: "Versions", icon: Layers3 },
  { href: "/reviews", label: "Reviews", icon: CheckSquare },
  { href: "/activity", label: "Activity", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
];
