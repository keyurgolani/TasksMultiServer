import type { ViewOption } from "./ViewSelector";

/**
 * Default view options for the ViewSelector component
 */
export const defaultViews: ViewOption[] = [
  { id: "dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { id: "projects", label: "Projects", icon: "Folder" },
  { id: "taskLists", label: "Task Lists", icon: "List" },
  { id: "tasks", label: "Tasks", icon: "CheckSquare" },
];
