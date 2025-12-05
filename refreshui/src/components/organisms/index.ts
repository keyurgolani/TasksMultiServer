/**
 * Organisms - Complex functional blocks composed of molecules and atoms
 *
 * Organisms are relatively complex UI components composed of groups of
 * molecules and/or atoms. They form distinct sections of an interface.
 */

// Export TaskCard
export {
  TaskCard,
  TaskCardSkeleton,
  type TaskCardProps,
  type TaskCardSkeletonProps,
} from "./TaskCard";

export * from "./ProjectCard";
export * from "./TaskListCard";
// @deprecated - Use CustomizationPopup instead (Requirement 53.2)
// CustomizationDrawer is kept for backwards compatibility but should not be used
export * from "./CustomizationDrawer";

// Export TaskDetailModal
export { TaskDetailModal, type TaskDetailModalProps } from "./TaskDetailModal";

// Export AppHeader
export { AppHeader, type AppHeaderProps, type LogoVariant, type LogoSize } from "./AppHeader";

// Export ViewSelector
export {
  ViewSelector,
  defaultViews,
  type ViewSelectorProps,
  type ViewOption,
  type DashboardView,
} from "./ViewSelector";

// Export FAB
export { FAB, type FABProps } from "./FAB";

// Export CreateProjectModal
export { CreateProjectModal, type CreateProjectModalProps } from "./CreateProjectModal";

// Export CreateTaskListModal
export { CreateTaskListModal, type CreateTaskListModalProps } from "./CreateTaskListModal";

// Export CreateTaskModal
export { CreateTaskModal, type CreateTaskModalProps } from "./CreateTaskModal";

// Export EditProjectModal
export { EditProjectModal, type EditProjectModalProps } from "./EditProjectModal";

// Export EditTaskListModal
export { EditTaskListModal, type EditTaskListModalProps } from "./EditTaskListModal";

// Export DeleteConfirmationDialog
export {
  DeleteConfirmationDialog,
  type DeleteConfirmationDialogProps,
  type CascadingDeletionInfo,
} from "./DeleteConfirmationDialog";

// Export ProjectGroup
export { ProjectGroup, type ProjectGroupProps } from "./ProjectGroup";

// Export SortFilterPopup
export {
  SortFilterPopup,
  type SortFilterPopupProps,
  type SortOption,
  type FilterOption,
} from "./SortFilterPopup";

// Export LivePreviewPanel
export { LivePreviewPanel, type LivePreviewPanelProps } from "./LivePreviewPanel";

// Export EffectsControlPanel
export { EffectsControlPanel, type EffectsControlPanelProps } from "./EffectsControlPanel";

// Export CustomizationPopup
export { CustomizationPopup, type CustomizationPopupProps } from "./CustomizationPopup";

// Export TaskStatusSummary
export { TaskStatusSummary, type TaskStatusSummaryProps } from "./TaskStatusSummary";

// Export ProjectProgressSummary
export { ProjectProgressSummary, type ProjectProgressSummaryProps } from "./ProjectProgressSummary";

// Export TaskListProgressSummary
export { TaskListProgressSummary, type TaskListProgressSummaryProps } from "./TaskListProgressSummary";

// Export OverallProgress
export {
  OverallProgress,
  type OverallProgressProps,
  type StatusCounts as OverallProgressStatusCounts,
} from "./OverallProgress";
