import React, { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { Palette, Plus, Search, AlertCircle, Check, Info, ArrowLeft } from "lucide-react";

// Hooks
import { useParallax } from "../core/hooks/useParallax";

// Atoms
import { Button, type ButtonVariant, type ButtonSize } from "../components/atoms/Button";
import { Badge, type BadgeVariant, type BadgeSize } from "../components/atoms/Badge";
import { Input, type InputState } from "../components/atoms/Input";
import { Card, type CardVariant, type CardPadding } from "../components/atoms/Card";
import { Typography, type TypographyVariant, type TypographyColor } from "../components/atoms/Typography";
import { Icon } from "../components/atoms/Icon";
import { Skeleton, type SkeletonVariant } from "../components/atoms/Skeleton";
import { ProgressBar } from "../components/atoms/ProgressBar";

// Molecules
import { SearchBar } from "../components/molecules/SearchBar";
import { Toggle } from "../components/molecules/Toggle";
import { Slider } from "../components/molecules/Slider";
import { FilterChips } from "../components/molecules/FilterChips";
import { StatusIndicator, type StatusType } from "../components/molecules/StatusIndicator";
import { SortFilterButton } from "../components/molecules/SortFilterButton";
import { SearchFilterBar } from "../components/molecules/SearchFilterBar";
import { ThemePreviewSkeleton } from "../components/molecules/ThemePreviewSkeleton";
import { ColorSchemeMiniPreview } from "../components/molecules/ColorSchemeMiniPreview";
import { ColorSchemeRow } from "../components/molecules/ColorSchemeRow";
import { TypographyRow } from "../components/molecules/TypographyRow";
import { TaskCompletionProgress } from "../components/molecules/TaskCompletionProgress";
import { PercentageProgress } from "../components/molecules/PercentageProgress";
import { ReadyTasksProgress } from "../components/molecules/ReadyTasksProgress";

// Organisms
import { TaskCard } from "../components/organisms/TaskCard";
import { ProjectCard } from "../components/organisms/ProjectCard";
import { TaskListCard } from "../components/organisms/TaskListCard";
// CustomizationDrawer is deprecated - use CustomizationPopup instead (Requirement 53.2)
import { TaskDetailModal } from "../components/organisms/TaskDetailModal";
import { AppHeader } from "../components/organisms/AppHeader";
import { ViewSelector, type DashboardView } from "../components/organisms/ViewSelector";
import { FAB } from "../components/organisms/FAB";
import { CreateProjectModal } from "../components/organisms/CreateProjectModal";
import { CreateTaskListModal } from "../components/organisms/CreateTaskListModal";
import { CreateTaskModal } from "../components/organisms/CreateTaskModal";
import { EditProjectModal } from "../components/organisms/EditProjectModal";
import { EditTaskListModal } from "../components/organisms/EditTaskListModal";
import { DeleteConfirmationDialog } from "../components/organisms/DeleteConfirmationDialog";
import { ProjectGroup } from "../components/organisms/ProjectGroup";
import { SortFilterPopup } from "../components/organisms/SortFilterPopup";
import { LivePreviewPanel } from "../components/organisms/LivePreviewPanel";
import { EffectsControlPanel } from "../components/organisms/EffectsControlPanel";
import { CustomizationPopup } from "../components/organisms/CustomizationPopup";
import { TaskStatusSummary } from "../components/organisms/TaskStatusSummary";
import { ProjectProgressSummary } from "../components/organisms/ProjectProgressSummary";
import { TaskListProgressSummary } from "../components/organisms/TaskListProgressSummary";
import { OverallProgress } from "../components/organisms/OverallProgress";

// Atoms - CustomizationButton
import { CustomizationButton } from "../components/atoms/CustomizationButton";

// Effects
import { GlassBlurDemo } from "../components/effects/GlassBlurDemo";
import { AnimationSpeedDemo } from "../components/effects/AnimationSpeedDemo";

// Types
import type { Task, Project, TaskList } from "../core/types/entities";
import type { ProjectStats, TaskListStats } from "../services/types";

// Theme types and defaults
import {
  colorThemes,
  fontThemes,
  defaultEffectSettings,
  type ColorTheme,
  type FontTheme,
  type EffectSettings,
} from "../styles/themes";

// Theme context for applying customizations (Requirement 53.1, 53.3)
import { useTheme } from "../context/ThemeContext";

/**
 * ShowcasePage Component
 *
 * A comprehensive design system showcase page that displays all design tokens,
 * atoms, molecules, and organisms in one place. Allows developers to view
 * all component variants and states.
 *
 * Requirements: 9.1
 * - Display sections for tokens, atoms, molecules, and organisms
 */

// Sample data for organisms
const sampleTask: Task = {
  id: "task-1",
  taskListId: "list-1",
  title: "Implement user authentication",
  description: "Add OAuth2 authentication flow with Google and GitHub providers",
  status: "IN_PROGRESS",
  priority: "HIGH",
  dependencies: [{ taskId: "task-0", taskListId: "list-1" }],
  exitCriteria: [
    { criteria: "OAuth flow works", status: "COMPLETE" },
    { criteria: "Session management", status: "INCOMPLETE" },
    { criteria: "Error handling", status: "INCOMPLETE" },
  ],
  notes: [{ content: "Consider using Passport.js", timestamp: "2024-01-15T10:00:00Z" }],
  researchNotes: [],
  executionNotes: [],
  tags: ["auth", "security", "backend"],
  createdAt: "2024-01-10T08:00:00Z",
  updatedAt: "2024-01-15T10:00:00Z",
};

const sampleProject: Project = {
  id: "project-1",
  name: "Task Manager App",
  description: "A comprehensive task management application with real-time collaboration",
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-15T00:00:00Z",
};

const sampleProjectStats: ProjectStats = {
  taskListCount: 5,
  totalTasks: 24,
  completedTasks: 12,
  inProgressTasks: 8,
  blockedTasks: 2,
  readyTasks: 2,
};

const sampleTaskList: TaskList = {
  id: "list-1",
  projectId: "project-1",
  name: "Sprint 1 - Core Features",
  description: "Initial sprint focusing on core functionality",
  createdAt: "2024-01-05T00:00:00Z",
  updatedAt: "2024-01-15T00:00:00Z",
};

const sampleTaskListStats: TaskListStats = {
  taskCount: 8,
  completedTasks: 3,
  inProgressTasks: 3,
  blockedTasks: 1,
  readyTasks: 1,
  completionPercentage: 38,
};

// Section component for consistent styling
const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section className="mb-12">
    <Typography variant="h3" className="mb-6 pb-2 border-b border-[var(--border)]">
      {title}
    </Typography>
    {children}
  </section>
);

// Subsection component
const Subsection: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="mb-8">
    <Typography variant="h5" color="secondary" className="mb-4">
      {title}
    </Typography>
    {children}
  </div>
);

export const ShowcasePage: React.FC = () => {
  // Theme context for applying customizations (Requirement 53.1, 53.3)
  const { 
    activeColorTheme, 
    activeFontTheme, 
    activeEffectSettings,
    setColorTheme, 
    setFontTheme, 
    setEffectSettings 
  } = useTheme();

  // State for interactive components
  const [toggleState, setToggleState] = useState(false);
  const [sliderValue, setSliderValue] = useState(50);
  const [searchValue, setSearchValue] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<string[]>(["react"]);

  // State for organism modals
  // Note: CustomizationDrawer state removed - using CustomizationPopup instead (Requirement 53.1, 53.2)
  const [isTaskDetailModalOpen, setIsTaskDetailModalOpen] = useState(false);
  
  // State for new modals (Task 34)
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [isCreateTaskListModalOpen, setIsCreateTaskListModalOpen] = useState(false);
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [isEditProjectModalOpen, setIsEditProjectModalOpen] = useState(false);
  const [isEditTaskListModalOpen, setIsEditTaskListModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isSortFilterPopupOpen, setIsSortFilterPopupOpen] = useState(false);
  
  // State for ViewSelector demo
  const [currentView, setCurrentView] = useState<DashboardView>("dashboard");
  
  // State for SortFilterPopup demo
  const [activeSortId, setActiveSortId] = useState("name");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  
  // State for SearchFilterBar demo
  const [searchFilterValue, setSearchFilterValue] = useState("");
  
  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null!);
  
  // State for CustomizationPopup (Task 43.7)
  const [isCustomizationPopupOpen, setIsCustomizationPopupOpen] = useState(false);
  
  // State for theme customization demos (Task 43)
  const [demoColorScheme, setDemoColorScheme] = useState<ColorTheme>(colorThemes.dark);
  const [demoTypography, setDemoTypography] = useState<FontTheme>(fontThemes.inter);
  const [demoEffects, setDemoEffects] = useState<EffectSettings>(defaultEffectSettings);

  // Open customization popup to change theme (Requirement 53.1)
  const handleCustomizeClick = () => {
    setIsCustomizationPopupOpen(true);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-12">
          <div>
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-4 transition-colors"
            >
              <ArrowLeft size={16} />
              <span className="text-sm font-medium">Back to Dashboard</span>
            </Link>
            <Typography variant="h1" className="mb-2">
              Design System Showcase
            </Typography>
            <Typography variant="body" color="secondary">
              A comprehensive view of all design tokens and components
            </Typography>
          </div>
          <Button
            variant="secondary"
            onClick={handleCustomizeClick}
            leftIcon={<Palette size={16} />}
          >
            Customize Theme
          </Button>
        </div>

        {/* Tokens Section */}
        <Section title="Design Tokens">
          <TokensSection demoEffects={demoEffects} />
        </Section>

        {/* Atoms Section */}
        <Section title="Atoms">
          <AtomsSection />
        </Section>

        {/* Molecules Section */}
        <Section title="Molecules">
          <MoleculesSection
            toggleState={toggleState}
            setToggleState={setToggleState}
            sliderValue={sliderValue}
            setSliderValue={setSliderValue}
            searchValue={searchValue}
            setSearchValue={setSearchValue}
            selectedFilters={selectedFilters}
            setSelectedFilters={setSelectedFilters}
            sortFilterActive={activeSortId !== "name" || activeFilters.length > 0}
            searchFilterValue={searchFilterValue}
            setSearchFilterValue={setSearchFilterValue}
            onSortFilterOpen={() => setIsSortFilterPopupOpen(true)}
            onSortFilterReset={() => {
              setActiveSortId("name");
              setActiveFilters([]);
            }}
            demoColorScheme={demoColorScheme}
            setDemoColorScheme={setDemoColorScheme}
            demoTypography={demoTypography}
            setDemoTypography={setDemoTypography}
            demoEffects={demoEffects}
          />
        </Section>

        {/* Organisms Section */}
        <Section title="Organisms">
          <OrganismsSection
            onOpenCustomizationPopup={() => setIsCustomizationPopupOpen(true)}
            onOpenTaskDetailModal={() => setIsTaskDetailModalOpen(true)}
            onOpenCreateProjectModal={() => setIsCreateProjectModalOpen(true)}
            onOpenCreateTaskListModal={() => setIsCreateTaskListModalOpen(true)}
            onOpenCreateTaskModal={() => setIsCreateTaskModalOpen(true)}
            onOpenEditProjectModal={() => setIsEditProjectModalOpen(true)}
            onOpenEditTaskListModal={() => setIsEditTaskListModalOpen(true)}
            onOpenDeleteDialog={() => setIsDeleteDialogOpen(true)}
            onOpenSortFilterPopup={() => setIsSortFilterPopupOpen(true)}
            currentView={currentView}
            onViewChange={setCurrentView}
            isSortFilterPopupOpen={isSortFilterPopupOpen}
            onCloseSortFilterPopup={() => setIsSortFilterPopupOpen(false)}
            activeSortId={activeSortId}
            onSortChange={(id) => {
              setActiveSortId(id);
            }}
            activeFilters={activeFilters}
            onFilterChange={(filters) => {
              setActiveFilters(filters);
            }}
            sortFilterButtonRef={sortFilterButtonRef}
            demoColorScheme={demoColorScheme}
            setDemoColorScheme={setDemoColorScheme}
            demoTypography={demoTypography}
            setDemoTypography={setDemoTypography}
            demoEffects={demoEffects}
            setDemoEffects={setDemoEffects}
          />
        </Section>
      </div>

      {/* CustomizationPopup - rendered at root level for proper overlay (Requirement 53.1, 53.2, 53.3) */}
      {/* Note: CustomizationDrawer has been replaced with CustomizationPopup */}

      {/* TaskDetailModal - rendered at root level for proper overlay */}
      <TaskDetailModal
        task={sampleTask}
        isOpen={isTaskDetailModalOpen}
        onClose={() => setIsTaskDetailModalOpen(false)}
        onSave={(task) => console.log("Task saved:", task)}
        onDelete={(taskId) => console.log("Task deleted:", taskId)}
        availableTasks={[sampleTask]}
      />

      {/* CreateProjectModal - Task 34.4 */}
      <CreateProjectModal
        isOpen={isCreateProjectModalOpen}
        onClose={() => setIsCreateProjectModalOpen(false)}
        onSuccess={() => {
          setIsCreateProjectModalOpen(false);
          console.log("Project created successfully");
        }}
      />

      {/* CreateTaskListModal - Task 34.5 */}
      <CreateTaskListModal
        isOpen={isCreateTaskListModalOpen}
        onClose={() => setIsCreateTaskListModalOpen(false)}
        onSuccess={() => {
          setIsCreateTaskListModalOpen(false);
          console.log("Task list created successfully");
        }}
      />

      {/* CreateTaskModal - Task 34.6 */}
      <CreateTaskModal
        isOpen={isCreateTaskModalOpen}
        taskListId="list-1"
        onClose={() => setIsCreateTaskModalOpen(false)}
        onSuccess={() => {
          setIsCreateTaskModalOpen(false);
          console.log("Task created successfully");
        }}
      />

      {/* EditProjectModal - Task 34.7 */}
      <EditProjectModal
        isOpen={isEditProjectModalOpen}
        project={sampleProject}
        onClose={() => setIsEditProjectModalOpen(false)}
        onSuccess={() => {
          setIsEditProjectModalOpen(false);
          console.log("Project updated successfully");
        }}
      />

      {/* EditTaskListModal - Task 34.8 */}
      <EditTaskListModal
        isOpen={isEditTaskListModalOpen}
        taskList={sampleTaskList}
        onClose={() => setIsEditTaskListModalOpen(false)}
        onSuccess={() => {
          setIsEditTaskListModalOpen(false);
          console.log("Task list updated successfully");
        }}
      />

      {/* DeleteConfirmationDialog - Task 34.9 */}
      <DeleteConfirmationDialog
        isOpen={isDeleteDialogOpen}
        title="Delete Project"
        message="Are you sure you want to delete this project? This action cannot be undone."
        itemName={sampleProject.name}
        onConfirm={() => {
          setIsDeleteDialogOpen(false);
          console.log("Item deleted");
        }}
        onCancel={() => setIsDeleteDialogOpen(false)}
        isDestructive
      />

      {/* FAB - Task 34.3 - Rendered at page level for proper positioning */}
      <FAB
        onAddProject={() => setIsCreateProjectModalOpen(true)}
        onAddTaskList={() => setIsCreateTaskListModalOpen(true)}
        onAddTask={() => setIsCreateTaskModalOpen(true)}
        showTaskButton={true}
      />

      {/* CustomizationPopup - Task 43.7, 65, 66 - Now controls actual theme (Requirement 53.1, 53.3) */}
      <CustomizationPopup
        isOpen={isCustomizationPopupOpen}
        onClose={() => setIsCustomizationPopupOpen(false)}
        colorScheme={activeColorTheme}
        typography={activeFontTheme}
        effects={activeEffectSettings}
        onColorSchemeChange={(scheme) => setColorTheme(scheme.id)}
        onTypographyChange={(font) => setFontTheme(font.id)}
        onEffectsChange={(key, value) => {
          setEffectSettings({ ...activeEffectSettings, [key]: value });
        }}
        onApply={(colorScheme, typography, effects) => {
          // Apply all changes when Apply button is clicked (Requirement 52.2, 53.1, 53.3)
          setColorTheme(colorScheme.id);
          setFontTheme(typography.id);
          setEffectSettings(effects);
        }}
      />
    </div>
  );
};


/**
 * ParallaxDemo Component
 * Demonstrates the parallax tilt effect on cards with real-time updates
 * 
 * Requirements: 36.5
 * - Showcase displays parallax cards that demonstrate the parallax strength effect in real-time
 */
const ParallaxDemo: React.FC = () => {
  const parallax1 = useParallax();
  const parallax2 = useParallax();
  const parallax3 = useParallax();

  return (
    <div className="flex flex-wrap gap-6">
      {/* Card 1 - Glass variant */}
      <div
        className="w-48 h-32 glass-panel p-4 cursor-pointer"
        style={parallax1.style}
        onMouseEnter={parallax1.onMouseEnter}
        onMouseMove={parallax1.onMouseMove}
        onMouseLeave={parallax1.onMouseLeave}
      >
        <Typography variant="h6" color="primary">
          Glass Card
        </Typography>
        <Typography variant="caption" color="secondary">
          Hover to tilt
        </Typography>
      </div>

      {/* Card 2 - Solid variant */}
      <div
        className="w-48 h-32 bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] p-4 cursor-pointer"
        style={parallax2.style}
        onMouseEnter={parallax2.onMouseEnter}
        onMouseMove={parallax2.onMouseMove}
        onMouseLeave={parallax2.onMouseLeave}
      >
        <Typography variant="h6" color="primary">
          Solid Card
        </Typography>
        <Typography variant="caption" color="secondary">
          Hover to tilt
        </Typography>
      </div>

      {/* Card 3 - Primary gradient */}
      <div
        className="w-48 h-32 bg-gradient-to-br from-[var(--primary)] to-[var(--primary-dark)] rounded-lg p-4 cursor-pointer"
        style={parallax3.style}
        onMouseEnter={parallax3.onMouseEnter}
        onMouseMove={parallax3.onMouseMove}
        onMouseLeave={parallax3.onMouseLeave}
      >
        <Typography variant="h6" className="text-white">
          Gradient Card
        </Typography>
        <Typography variant="caption" className="text-white/70">
          Hover to tilt
        </Typography>
      </div>
    </div>
  );
};


/**
 * TokensSection Component
 * Displays color swatches, spacing scale, typography samples, and effect previews
 * Requirements: 9.2
 */
interface TokensSectionProps {
  /** Effect settings from customization engine for real-time updates */
  demoEffects: EffectSettings;
}

const TokensSection: React.FC<TokensSectionProps> = ({ demoEffects }) => {
  // Color tokens
  const primaryColors = [
    { name: "Primary", var: "--primary", className: "bg-[var(--primary)]" },
    { name: "Primary Dark", var: "--primary-dark", className: "bg-[var(--primary-dark)]" },
    { name: "Primary Light", var: "--primary-light", className: "bg-[var(--primary-light)]" },
  ];

  const statusColors = [
    { name: "Success", var: "--success", className: "bg-[var(--success)]" },
    { name: "Warning", var: "--warning", className: "bg-[var(--warning)]" },
    { name: "Error", var: "--error", className: "bg-[var(--error)]" },
    { name: "Info", var: "--info", className: "bg-[var(--info)]" },
  ];

  const backgroundColors = [
    { name: "App", var: "--bg-app", className: "bg-[var(--bg-app)]" },
    { name: "Surface", var: "--bg-surface", className: "bg-[var(--bg-surface)]" },
    { name: "Surface Hover", var: "--bg-surface-hover", className: "bg-[var(--bg-surface-hover)]" },
    { name: "Glass", var: "--bg-glass", className: "bg-[var(--bg-glass)]" },
  ];

  const textColors = [
    { name: "Primary", var: "--text-primary", className: "text-[var(--text-primary)]" },
    { name: "Secondary", var: "--text-secondary", className: "text-[var(--text-secondary)]" },
    { name: "Tertiary", var: "--text-tertiary", className: "text-[var(--text-tertiary)]" },
    { name: "Muted", var: "--text-muted", className: "text-[var(--text-muted)]" },
  ];

  // Spacing tokens
  const spacingTokens = [
    { name: "space-1", value: "4px" },
    { name: "space-2", value: "8px" },
    { name: "space-3", value: "12px" },
    { name: "space-4", value: "16px" },
    { name: "space-5", value: "20px" },
    { name: "space-6", value: "24px" },
    { name: "space-7", value: "28px" },
    { name: "space-8", value: "32px" },
  ];

  // Font families
  const fontFamilies = [
    { name: "Default", var: "--font-default", sample: "Inter" },
    { name: "Corporate", var: "--font-corporate", sample: "Roboto" },
    { name: "Fun", var: "--font-fun", sample: "Quicksand" },
    { name: "Nerd", var: "--font-nerd", sample: "Fira Code" },
    { name: "Quirky", var: "--font-quirky", sample: "Space Grotesk" },
  ];

  return (
    <div className="space-y-8">
      {/* Color Swatches */}
      <Subsection title="Colors">
        <div className="space-y-6">
          {/* Primary Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Primary Colors
            </Typography>
            <div className="flex flex-wrap gap-4">
              {primaryColors.map((color) => (
                <div key={color.var} className="text-center">
                  <div
                    className={`w-16 h-16 rounded-lg ${color.className} border border-[var(--border)] shadow-sm`}
                  />
                  <Typography variant="caption" color="secondary" className="mt-2 block">
                    {color.name}
                  </Typography>
                  <Typography variant="caption" color="muted" className="block text-xs">
                    {color.var}
                  </Typography>
                </div>
              ))}
            </div>
          </div>

          {/* Status Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Status Colors
            </Typography>
            <div className="flex flex-wrap gap-4">
              {statusColors.map((color) => (
                <div key={color.var} className="text-center">
                  <div
                    className={`w-16 h-16 rounded-lg ${color.className} border border-[var(--border)] shadow-sm`}
                  />
                  <Typography variant="caption" color="secondary" className="mt-2 block">
                    {color.name}
                  </Typography>
                  <Typography variant="caption" color="muted" className="block text-xs">
                    {color.var}
                  </Typography>
                </div>
              ))}
            </div>
          </div>

          {/* Background Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Background Colors
            </Typography>
            <div className="flex flex-wrap gap-4">
              {backgroundColors.map((color) => (
                <div key={color.var} className="text-center">
                  <div
                    className={`w-16 h-16 rounded-lg ${color.className} border border-[var(--border)] shadow-sm`}
                  />
                  <Typography variant="caption" color="secondary" className="mt-2 block">
                    {color.name}
                  </Typography>
                  <Typography variant="caption" color="muted" className="block text-xs">
                    {color.var}
                  </Typography>
                </div>
              ))}
            </div>
          </div>

          {/* Text Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Text Colors
            </Typography>
            <div className="flex flex-wrap gap-4">
              {textColors.map((color) => (
                <div key={color.var} className="text-center">
                  <div
                    className={`w-16 h-16 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)] shadow-sm flex items-center justify-center`}
                  >
                    <span className={`text-lg font-bold ${color.className}`}>Aa</span>
                  </div>
                  <Typography variant="caption" color="secondary" className="mt-2 block">
                    {color.name}
                  </Typography>
                  <Typography variant="caption" color="muted" className="block text-xs">
                    {color.var}
                  </Typography>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Subsection>

      {/* Spacing Scale */}
      <Subsection title="Spacing Scale">
        <div className="flex flex-wrap items-end gap-4">
          {spacingTokens.map((token) => (
            <div key={token.name} className="text-center">
              <div
                className="bg-[var(--primary)] rounded"
                style={{ width: token.value, height: token.value }}
              />
              <Typography variant="caption" color="secondary" className="mt-2 block">
                {token.name}
              </Typography>
              <Typography variant="caption" color="muted" className="block text-xs">
                {token.value}
              </Typography>
            </div>
          ))}
        </div>
      </Subsection>

      {/* Typography Samples */}
      <Subsection title="Typography">
        <div className="space-y-6">
          {/* Font Families */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Font Families
            </Typography>
            <div className="space-y-3">
              {fontFamilies.map((font) => (
                <div
                  key={font.var}
                  className="flex items-center gap-4 p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]"
                >
                  <Typography variant="caption" color="muted" className="w-24">
                    {font.name}
                  </Typography>
                  <span
                    className="text-lg text-[var(--text-primary)]"
                    style={{ fontFamily: `var(${font.var})` }}
                  >
                    The quick brown fox jumps over the lazy dog.
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Font Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Font Sizes
            </Typography>
            <div className="space-y-2">
              {["xs", "sm", "base", "lg", "xl", "2xl", "3xl"].map((size) => (
                <div key={size} className="flex items-baseline gap-4">
                  <Typography variant="caption" color="muted" className="w-16">
                    {size}
                  </Typography>
                  <span
                    className="text-[var(--text-primary)]"
                    style={{ fontSize: `var(--font-size-${size})` }}
                  >
                    Sample Text
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Subsection>

      {/* Effect Previews */}
      <Subsection title="Effects">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Glassmorphism */}
          <div className="p-4 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--info)]">
            <div className="glass-panel p-4">
              <Typography variant="h6" color="primary">
                Glassmorphism
              </Typography>
              <Typography variant="body-sm" color="secondary">
                Frosted glass effect with backdrop blur
              </Typography>
            </div>
          </div>

          {/* Shadow Levels */}
          <div className="space-y-3">
            <Typography variant="label" color="muted" className="block">
              Shadow Levels
            </Typography>
            {["sm", "md", "lg", "xl"].map((level) => (
              <div
                key={level}
                className="p-3 rounded-lg bg-[var(--bg-surface)]"
                style={{ boxShadow: `var(--shadow-${level})` }}
              >
                <Typography variant="caption" color="secondary">
                  shadow-{level}
                </Typography>
              </div>
            ))}
          </div>

          {/* Border Radius */}
          <div className="space-y-3">
            <Typography variant="label" color="muted" className="block">
              Border Radius
            </Typography>
            <div className="flex flex-wrap gap-3">
              {["sm", "md", "lg", "xl", "full"].map((radius) => (
                <div
                  key={radius}
                  className="w-12 h-12 bg-[var(--primary)] flex items-center justify-center"
                  style={{ borderRadius: `var(--radius-${radius})` }}
                >
                  <Typography variant="caption" className="text-white text-xs">
                    {radius}
                  </Typography>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Parallax Strength Demo - Requirement 36.5 */}
        <div className="mt-6">
          <Typography variant="label" color="muted" className="mb-3 block">
            Parallax Tilt Effect
          </Typography>
          <Typography variant="caption" color="secondary" className="mb-4 block">
            Hover over the cards below to see the 3D tilt effect. Adjust the Parallax Strength slider in the customization panel to change the intensity.
          </Typography>
          <ParallaxDemo />
        </div>

        {/* Glass Blur Demo - Requirement 37.1, 37.2, 37.3, 37.4 */}
        <div className="mt-6">
          <Typography variant="label" color="muted" className="mb-3 block">
            Glass Blur Effect
          </Typography>
          <Typography variant="caption" color="secondary" className="mb-4 block">
            The glass blur effect creates a frosted glass appearance. The cards below show varying blur values. 
            Adjust the Glass Blur slider in the customization panel to see real-time updates.
          </Typography>
          <GlassBlurDemo
            glassBlur={demoEffects.glassBlur}
            glassOpacity={demoEffects.glassOpacity / 100}
            glassBorderOpacity={0.3}
          />
        </div>

        {/* Animation Speed Demo - Requirement 38.1, 38.2, 38.3, 38.4 */}
        <div className="mt-6">
          <Typography variant="label" color="muted" className="mb-3 block">
            Animation Speed Effect
          </Typography>
          <Typography variant="caption" color="secondary" className="mb-4 block">
            The animation speed multiplier affects all transitions in the UI. Interact with the elements below to see the effect.
            Adjust the Animation Speed slider in the customization panel to see real-time updates.
          </Typography>
          <AnimationSpeedDemo animationSpeed={demoEffects.animationSpeed} />
        </div>
      </Subsection>
    </div>
  );
};


/**
 * AtomsSection Component
 * Renders each atom component in all its variants and states
 * Requirements: 9.3
 */
const AtomsSection: React.FC = () => {
  const buttonVariants: ButtonVariant[] = ["primary", "secondary", "tertiary", "ghost", "destructive"];
  const buttonSizes: ButtonSize[] = ["sm", "md", "lg"];
  const badgeVariants: BadgeVariant[] = ["success", "warning", "error", "info", "neutral"];
  const badgeSizes: BadgeSize[] = ["sm", "md"];
  const inputStates: InputState[] = ["default", "focus", "error", "disabled"];
  const cardVariants: CardVariant[] = ["glass", "solid", "outline"];
  const cardPaddings: CardPadding[] = ["none", "sm", "md", "lg"];
  const typographyVariants: TypographyVariant[] = ["h1", "h2", "h3", "h4", "h5", "h6", "body", "body-sm", "body-lg", "caption", "label"];
  const typographyColors: TypographyColor[] = ["primary", "secondary", "muted", "success", "warning", "error", "info"];
  const skeletonVariants: SkeletonVariant[] = ["text", "rectangular", "circular"];

  return (
    <div className="space-y-8">
      {/* Buttons */}
      <Subsection title="Button">
        <div className="space-y-6">
          {/* Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Variants
            </Typography>
            <div className="flex flex-wrap gap-3">
              {buttonVariants.map((variant) => (
                <Button key={variant} variant={variant}>
                  {variant.charAt(0).toUpperCase() + variant.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="flex flex-wrap items-center gap-3">
              {buttonSizes.map((size) => (
                <Button key={size} size={size}>
                  Size {size.toUpperCase()}
                </Button>
              ))}
            </div>
          </div>

          {/* With Icons */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Icons
            </Typography>
            <div className="flex flex-wrap gap-3">
              <Button leftIcon={<Plus size={16} />}>Left Icon</Button>
              <Button rightIcon={<Search size={16} />}>Right Icon</Button>
              <Button leftIcon={<Check size={16} />} rightIcon={<Info size={16} />}>
                Both Icons
              </Button>
            </div>
          </div>

          {/* States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              States
            </Typography>
            <div className="flex flex-wrap gap-3">
              <Button>Normal</Button>
              <Button disabled>Disabled</Button>
              <Button loading>Loading</Button>
            </div>
          </div>
        </div>
      </Subsection>

      {/* Badges */}
      <Subsection title="Badge">
        <div className="space-y-4">
          {/* Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Variants
            </Typography>
            <div className="flex flex-wrap gap-3">
              {badgeVariants.map((variant) => (
                <Badge key={variant} variant={variant}>
                  {variant.toUpperCase()}
                </Badge>
              ))}
            </div>
          </div>

          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="flex flex-wrap items-center gap-3">
              {badgeSizes.map((size) => (
                <Badge key={size} size={size} variant="info">
                  Size {size.toUpperCase()}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </Subsection>

      {/* Inputs */}
      <Subsection title="Input">
        <div className="space-y-4 max-w-md">
          {/* States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              States
            </Typography>
            <div className="space-y-3">
              {inputStates.map((state) => (
                <Input
                  key={state}
                  state={state}
                  placeholder={`${state.charAt(0).toUpperCase() + state.slice(1)} state`}
                  disabled={state === "disabled"}
                  errorMessage={state === "error" ? "This field has an error" : undefined}
                />
              ))}
            </div>
          </div>

          {/* With Icons */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Icons
            </Typography>
            <div className="space-y-3">
              <Input leftIcon={<Search size={16} />} placeholder="Search..." />
              <Input rightIcon={<AlertCircle size={16} />} placeholder="With right icon" />
              <Input
                leftIcon={<Search size={16} />}
                rightIcon={<AlertCircle size={16} />}
                placeholder="Both icons"
              />
            </div>
          </div>

          {/* With Label */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Label
            </Typography>
            <Input label="Email Address" placeholder="Enter your email" type="text" />
          </div>
        </div>
      </Subsection>

      {/* Cards */}
      <Subsection title="Card">
        <div className="space-y-6">
          {/* Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Variants
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {cardVariants.map((variant) => (
                <Card key={variant} variant={variant} padding="md">
                  <Typography variant="h6">{variant.charAt(0).toUpperCase() + variant.slice(1)} Card</Typography>
                  <Typography variant="body-sm" color="secondary">
                    This is a {variant} variant card.
                  </Typography>
                </Card>
              ))}
            </div>
          </div>

          {/* Padding */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Padding Sizes
            </Typography>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {cardPaddings.map((padding) => (
                <Card key={padding} variant="solid" padding={padding}>
                  <div className="bg-[var(--primary)] bg-opacity-20 p-2 rounded">
                    <Typography variant="caption">padding: {padding}</Typography>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Interactive */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Interactive (Spotlight & Tilt)
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card variant="glass" padding="md" spotlight tilt>
                <Typography variant="h6">Interactive Card</Typography>
                <Typography variant="body-sm" color="secondary">
                  Hover to see spotlight and tilt effects.
                </Typography>
              </Card>
              <Card variant="glass" padding="md" spotlight={false} tilt={false}>
                <Typography variant="h6">Static Card</Typography>
                <Typography variant="body-sm" color="secondary">
                  No interactive effects enabled.
                </Typography>
              </Card>
            </div>
          </div>
        </div>
      </Subsection>

      {/* Typography */}
      <Subsection title="Typography">
        <div className="space-y-6">
          {/* Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Variants
            </Typography>
            <div className="space-y-2">
              {typographyVariants.map((variant) => (
                <Typography key={variant} variant={variant}>
                  {variant} - The quick brown fox
                </Typography>
              ))}
            </div>
          </div>

          {/* Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Colors
            </Typography>
            <div className="flex flex-wrap gap-4">
              {typographyColors.map((color) => (
                <Typography key={color} variant="body" color={color}>
                  {color}
                </Typography>
              ))}
            </div>
          </div>
        </div>
      </Subsection>

      {/* Icon */}
      <Subsection title="Icon">
        <div className="space-y-4">
          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <Icon name="Star" size="sm" />
                <Typography variant="caption" color="muted" className="block mt-1">
                  sm
                </Typography>
              </div>
              <div className="text-center">
                <Icon name="Star" size="md" />
                <Typography variant="caption" color="muted" className="block mt-1">
                  md
                </Typography>
              </div>
              <div className="text-center">
                <Icon name="Star" size="lg" />
                <Typography variant="caption" color="muted" className="block mt-1">
                  lg
                </Typography>
              </div>
              <div className="text-center">
                <Icon name="Star" size={32} />
                <Typography variant="caption" color="muted" className="block mt-1">
                  32px
                </Typography>
              </div>
            </div>
          </div>

          {/* Common Icons */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Common Icons
            </Typography>
            <div className="flex flex-wrap gap-4">
              {["Search", "Plus", "X", "Check", "AlertCircle", "Info", "Settings", "User", "Home", "Folder"].map(
                (name) => (
                  <div key={name} className="text-center p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
                    <Icon name={name as keyof typeof import("lucide-react")} size="md" />
                    <Typography variant="caption" color="muted" className="block mt-1 text-xs">
                      {name}
                    </Typography>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </Subsection>

      {/* Skeleton */}
      <Subsection title="Skeleton">
        <div className="space-y-4">
          {/* Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Variants
            </Typography>
            <div className="flex flex-wrap items-center gap-6">
              {skeletonVariants.map((variant) => (
                <div key={variant} className="text-center">
                  <Skeleton
                    variant={variant}
                    width={variant === "text" ? 200 : 64}
                    height={variant === "text" ? undefined : 64}
                  />
                  <Typography variant="caption" color="muted" className="block mt-2">
                    {variant}
                  </Typography>
                </div>
              ))}
            </div>
          </div>

          {/* Multi-line Text */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Multi-line Text
            </Typography>
            <div className="max-w-md">
              <Skeleton variant="text" lines={3} />
            </div>
          </div>

          {/* Card Skeleton */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Card Skeleton
            </Typography>
            <Card variant="solid" padding="md" className="max-w-sm">
              <div className="flex items-center gap-3 mb-4">
                <Skeleton variant="circular" width={40} height={40} />
                <div className="flex-1">
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="text" width="40%" className="mt-2" />
                </div>
              </div>
              <Skeleton variant="rectangular" height={100} className="mb-3" />
              <Skeleton variant="text" lines={2} />
            </Card>
          </div>
        </div>
      </Subsection>

      {/* CustomizationButton - Task 43.8 */}
      <Subsection title="CustomizationButton">
        <div className="space-y-6">
          {/* Default with Preview */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default (with Preview Thumbnail)
            </Typography>
            <div className="flex flex-wrap items-center gap-4">
              <CustomizationButton
                currentScheme={colorThemes.dark}
                typography={fontThemes.inter}
                effects={defaultEffectSettings}
                onClick={() => console.log("Open customization")}
              />
              <CustomizationButton
                currentScheme={colorThemes.light}
                typography={fontThemes.inter}
                effects={defaultEffectSettings}
                onClick={() => console.log("Open customization")}
              />
              <CustomizationButton
                currentScheme={colorThemes.ocean}
                typography={fontThemes.inter}
                effects={defaultEffectSettings}
                onClick={() => console.log("Open customization")}
              />
              <CustomizationButton
                currentScheme={colorThemes.sunset}
                typography={fontThemes.inter}
                effects={defaultEffectSettings}
                onClick={() => console.log("Open customization")}
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Shows a tiny preview of the current theme - updates when color scheme changes
            </Typography>
          </div>

          {/* Without Preview */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Without Preview (Icon Only)
            </Typography>
            <div className="flex flex-wrap items-center gap-4">
              <CustomizationButton
                onClick={() => console.log("Open customization")}
                showPreview={false}
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Shows a settings icon when preview is disabled
            </Typography>
          </div>

          {/* States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              States
            </Typography>
            <div className="flex flex-wrap items-center gap-4">
              <div className="text-center">
                <CustomizationButton
                  currentScheme={colorThemes.dark}
                  onClick={() => console.log("Open customization")}
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Normal
                </Typography>
              </div>
              <div className="text-center">
                <CustomizationButton
                  currentScheme={colorThemes.dark}
                  onClick={() => console.log("Open customization")}
                  disabled
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Disabled
                </Typography>
              </div>
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Hover over the button to see scale and shadow effects
            </Typography>
          </div>
        </div>
      </Subsection>

      {/* ProgressBar - Task 53.1 */}
      <Subsection title="ProgressBar">
        <div className="space-y-6">
          {/* Single Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Single Variant (Standard)
            </Typography>
            <div className="space-y-4 max-w-md">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">0%</Typography>
                <ProgressBar variant="single" percentage={0} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">25%</Typography>
                <ProgressBar variant="single" percentage={25} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">50%</Typography>
                <ProgressBar variant="single" percentage={50} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">75%</Typography>
                <ProgressBar variant="single" percentage={75} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">100%</Typography>
                <ProgressBar variant="single" percentage={100} />
              </div>
            </div>
          </div>

          {/* Single-Mini Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Single-Mini Variant (Compact for tight spaces)
            </Typography>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <ProgressBar variant="single-mini" percentage={25} />
                <Typography variant="caption" color="muted">25%</Typography>
              </div>
              <div className="flex items-center gap-3">
                <ProgressBar variant="single-mini" percentage={50} />
                <Typography variant="caption" color="muted">50%</Typography>
              </div>
              <div className="flex items-center gap-3">
                <ProgressBar variant="single-mini" percentage={75} />
                <Typography variant="caption" color="muted">75%</Typography>
              </div>
            </div>
          </div>

          {/* Custom Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Custom Colors
            </Typography>
            <div className="space-y-3 max-w-md">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Primary (default)</Typography>
                <ProgressBar variant="single" percentage={60} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Success</Typography>
                <ProgressBar variant="single" percentage={60} color="var(--success)" />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Warning</Typography>
                <ProgressBar variant="single" percentage={60} color="var(--warning)" />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Error</Typography>
                <ProgressBar variant="single" percentage={60} color="var(--error)" />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Info</Typography>
                <ProgressBar variant="single" percentage={60} color="var(--info)" />
              </div>
            </div>
          </div>

          {/* Multi-State Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Multi-State Variant (Status Breakdown)
            </Typography>
            <div className="space-y-4 max-w-md">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">
                  Balanced: 3 completed, 2 in progress, 1 blocked, 2 not started
                </Typography>
                <ProgressBar
                  variant="multi-state"
                  statusCounts={{ completed: 3, inProgress: 2, blocked: 1, notStarted: 2 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">
                  All Completed: 8 completed, 0 others
                </Typography>
                <ProgressBar
                  variant="multi-state"
                  statusCounts={{ completed: 8, inProgress: 0, blocked: 0, notStarted: 0 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">
                  In Progress: 2 completed, 5 in progress, 0 blocked, 1 not started
                </Typography>
                <ProgressBar
                  variant="multi-state"
                  statusCounts={{ completed: 2, inProgress: 5, blocked: 0, notStarted: 1 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">
                  Blocked: 1 completed, 1 in progress, 4 blocked, 2 not started
                </Typography>
                <ProgressBar
                  variant="multi-state"
                  statusCounts={{ completed: 1, inProgress: 1, blocked: 4, notStarted: 2 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">
                  Not Started: 0 completed, 0 in progress, 0 blocked, 8 not started
                </Typography>
                <ProgressBar
                  variant="multi-state"
                  statusCounts={{ completed: 0, inProgress: 0, blocked: 0, notStarted: 8 }}
                />
              </div>
            </div>
          </div>

          {/* Multi-State-Mini Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Multi-State-Mini Variant (Compact for tight spaces)
            </Typography>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <ProgressBar
                  variant="multi-state-mini"
                  statusCounts={{ completed: 3, inProgress: 2, blocked: 1, notStarted: 2 }}
                />
                <Typography variant="caption" color="muted">3/2/1/2</Typography>
              </div>
              <div className="flex items-center gap-3">
                <ProgressBar
                  variant="multi-state-mini"
                  statusCounts={{ completed: 5, inProgress: 3, blocked: 0, notStarted: 0 }}
                />
                <Typography variant="caption" color="muted">5/3/0/0</Typography>
              </div>
            </div>
          </div>

          {/* Status Color Legend */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Status Color Legend
            </Typography>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 rounded bg-[var(--success)]" />
                <Typography variant="caption" color="secondary">Completed</Typography>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 rounded bg-[var(--warning)]" />
                <Typography variant="caption" color="secondary">In Progress</Typography>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 rounded bg-[var(--error)]" />
                <Typography variant="caption" color="secondary">Blocked</Typography>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 rounded bg-[var(--bg-surface)] border border-[var(--border)]" />
                <Typography variant="caption" color="secondary">Not Started (empty)</Typography>
              </div>
            </div>
          </div>
        </div>
      </Subsection>
    </div>
  );
};


/**
 * MoleculesSection Component
 * Renders each molecule component in all its variants and states
 * Requirements: 9.3
 */
interface MoleculesSectionProps {
  toggleState: boolean;
  setToggleState: (value: boolean) => void;
  sliderValue: number;
  setSliderValue: (value: number) => void;
  searchValue: string;
  setSearchValue: (value: string) => void;
  selectedFilters: string[];
  setSelectedFilters: (value: string[]) => void;
  // New props for Task 34.13, 34.15
  sortFilterActive: boolean;
  searchFilterValue: string;
  setSearchFilterValue: (value: string) => void;
  onSortFilterOpen: () => void;
  onSortFilterReset: () => void;
  // New props for Task 43 - Customization components
  demoColorScheme: ColorTheme;
  setDemoColorScheme: (scheme: ColorTheme) => void;
  demoTypography: FontTheme;
  setDemoTypography: (typography: FontTheme) => void;
  demoEffects: EffectSettings;
}

const MoleculesSection: React.FC<MoleculesSectionProps> = ({
  toggleState,
  setToggleState,
  sliderValue,
  setSliderValue,
  searchValue,
  setSearchValue,
  selectedFilters,
  setSelectedFilters,
  sortFilterActive,
  searchFilterValue,
  setSearchFilterValue,
  onSortFilterOpen,
  onSortFilterReset,
  demoColorScheme,
  setDemoColorScheme,
  demoTypography,
  setDemoTypography,
  demoEffects,
}) => {
  const statusTypes: StatusType[] = ["not_started", "in_progress", "completed", "blocked"];
  const filterOptions = [
    { id: "react", label: "React" },
    { id: "typescript", label: "TypeScript" },
    { id: "tailwind", label: "Tailwind" },
    { id: "nodejs", label: "Node.js" },
  ];

  return (
    <div className="space-y-8">
      {/* SearchBar */}
      <Subsection title="SearchBar">
        <div className="space-y-4 max-w-md">
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default (with Clear Functionality)
            </Typography>
            <SearchBar
              placeholder="Search tasks..."
              value={searchValue}
              onChange={setSearchValue}
              onClear={() => setSearchValue("")}
            />
            <Typography variant="caption" color="muted" className="mt-2 block">
              Current value: "{searchValue}" - Type to see X icon appear, click X to clear
            </Typography>
          </div>

          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Empty State
            </Typography>
            <SearchBar
              placeholder="Search icon shown when empty..."
              value=""
              onChange={() => {}}
            />
            <Typography variant="caption" color="muted" className="mt-2 block">
              Shows search icon on the right when input is empty
            </Typography>
          </div>

          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Text
            </Typography>
            <SearchBar
              placeholder="Search..."
              value="example search text"
              onChange={() => {}}
              onClear={() => console.log("Clear clicked")}
            />
            <Typography variant="caption" color="muted" className="mt-2 block">
              Shows X icon when text is present - click to clear
            </Typography>
          </div>

          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Custom Debounce (500ms)
            </Typography>
            <SearchBar placeholder="Search with 500ms debounce..." debounceMs={500} />
          </div>

          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Disabled
            </Typography>
            <SearchBar placeholder="Disabled search..." disabled />
          </div>
        </div>
      </Subsection>

      {/* Toggle */}
      <Subsection title="Toggle">
        <div className="space-y-4">
          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="flex flex-wrap items-center gap-6">
              <Toggle checked={toggleState} onChange={setToggleState} size="sm" label="Small" />
              <Toggle checked={toggleState} onChange={setToggleState} size="md" label="Medium" />
              <Toggle checked={toggleState} onChange={setToggleState} size="lg" label="Large" />
            </div>
          </div>

          {/* States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              States
            </Typography>
            <div className="flex flex-wrap items-center gap-6">
              <Toggle checked={false} onChange={() => {}} label="Off" />
              <Toggle checked={true} onChange={() => {}} label="On" />
              <Toggle checked={false} onChange={() => {}} label="Disabled Off" disabled />
              <Toggle checked={true} onChange={() => {}} label="Disabled On" disabled />
            </div>
          </div>
        </div>
      </Subsection>

      {/* Slider */}
      <Subsection title="Slider">
        <div className="space-y-6 max-w-md">
          {/* Default */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default
            </Typography>
            <Slider
              value={sliderValue}
              onChange={setSliderValue}
              min={0}
              max={100}
              label="Volume"
            />
          </div>

          {/* With Step */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Step (10)
            </Typography>
            <Slider
              value={Math.round(sliderValue / 10) * 10}
              onChange={setSliderValue}
              min={0}
              max={100}
              step={10}
              label="Brightness"
            />
          </div>

          {/* With Unit */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Unit
            </Typography>
            <Slider
              value={sliderValue}
              onChange={setSliderValue}
              min={0}
              max={100}
              label="Opacity"
              unit="%"
            />
          </div>

          {/* Disabled */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Disabled
            </Typography>
            <Slider
              value={50}
              onChange={() => {}}
              min={0}
              max={100}
              label="Disabled Slider"
              disabled
            />
          </div>
        </div>
      </Subsection>

      {/* FilterChips */}
      <Subsection title="FilterChips">
        <div className="space-y-4">
          {/* Multi-select */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Multi-select
            </Typography>
            <FilterChips
              options={filterOptions}
              selected={selectedFilters}
              onChange={setSelectedFilters}
              multiSelect
            />
            <Typography variant="caption" color="muted" className="mt-2 block">
              Selected: {selectedFilters.join(", ") || "none"}
            </Typography>
          </div>

          {/* Single-select */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Single-select
            </Typography>
            <FilterChips
              options={filterOptions}
              selected={selectedFilters.slice(0, 1)}
              onChange={(selected) => setSelectedFilters(selected.slice(0, 1))}
              multiSelect={false}
            />
          </div>

          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="space-y-3">
              <FilterChips options={filterOptions} selected={["react"]} onChange={() => {}} size="sm" />
              <FilterChips options={filterOptions} selected={["react"]} onChange={() => {}} size="md" />
              <FilterChips options={filterOptions} selected={["react"]} onChange={() => {}} size="lg" />
            </div>
          </div>

          {/* Disabled */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Disabled
            </Typography>
            <FilterChips options={filterOptions} selected={["react"]} onChange={() => {}} disabled />
          </div>
        </div>
      </Subsection>

      {/* StatusIndicator */}
      <Subsection title="StatusIndicator">
        <div className="space-y-4">
          {/* All Statuses */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              All Statuses
            </Typography>
            <div className="flex flex-wrap items-center gap-6">
              {statusTypes.map((status) => (
                <div key={status} className="flex items-center gap-2">
                  <StatusIndicator status={status} />
                  <Typography variant="body-sm" color="secondary">
                    {status.replace("_", " ")}
                  </Typography>
                </div>
              ))}
            </div>
          </div>

          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-2">
                <StatusIndicator status="in_progress" size="sm" />
                <Typography variant="caption" color="muted">sm</Typography>
              </div>
              <div className="flex items-center gap-2">
                <StatusIndicator status="in_progress" size="md" />
                <Typography variant="caption" color="muted">md</Typography>
              </div>
              <div className="flex items-center gap-2">
                <StatusIndicator status="in_progress" size="lg" />
                <Typography variant="caption" color="muted">lg</Typography>
              </div>
            </div>
          </div>

          {/* With Pulse */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Pulse Animation
            </Typography>
            <div className="flex flex-wrap items-center gap-6">
              {statusTypes.map((status) => (
                <div key={status} className="flex items-center gap-2">
                  <StatusIndicator status={status} pulse />
                  <Typography variant="body-sm" color="secondary">
                    {status.replace("_", " ")}
                  </Typography>
                </div>
              ))}
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Note: Pulse only animates for "in_progress" and "blocked" statuses
            </Typography>
          </div>

          {/* Pulsing Strength Demo - Requirement 40.5 */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Pulsing Strength Effect
            </Typography>
            <Typography variant="caption" color="secondary" className="mb-4 block">
              The pulsing animation intensity is controlled by the Pulsing Strength slider in the customization panel.
              Adjust the slider to see the pulse scale change in real-time. At 0%, the pulse is disabled. At 100%, maximum pulse scale is applied.
            </Typography>
            <div className="flex flex-wrap items-center gap-8 p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
              <div className="flex flex-col items-center gap-2">
                <StatusIndicator status="in_progress" pulse size="lg" />
                <Typography variant="caption" color="muted">In Progress</Typography>
              </div>
              <div className="flex flex-col items-center gap-2">
                <StatusIndicator status="blocked" pulse size="lg" />
                <Typography variant="caption" color="muted">Blocked</Typography>
              </div>
            </div>
          </div>
        </div>
      </Subsection>

      {/* SortFilterButton - Task 34.13 */}
      <Subsection title="SortFilterButton">
        <div className="space-y-4">
          {/* States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              States
            </Typography>
            <div className="flex flex-wrap items-center gap-4">
              <div className="text-center">
                <SortFilterButton
                  isActive={false}
                  onOpenPopup={() => console.log("Open popup")}
                  onReset={() => console.log("Reset")}
                  label="Sort & Filter"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Inactive
                </Typography>
              </div>
              <div className="text-center">
                <SortFilterButton
                  isActive={true}
                  onOpenPopup={() => console.log("Open popup")}
                  onReset={() => console.log("Reset")}
                  label="Sort & Filter"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Active (with X icon)
                </Typography>
              </div>
              <div className="text-center">
                <SortFilterButton
                  isActive={false}
                  onOpenPopup={() => console.log("Open popup")}
                  onReset={() => console.log("Reset")}
                  label="Sort & Filter"
                  disabled
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Disabled
                </Typography>
              </div>
            </div>
          </div>

          {/* Interactive */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Interactive Demo
            </Typography>
            <div className="flex items-center gap-4">
              <SortFilterButton
                isActive={sortFilterActive}
                onOpenPopup={onSortFilterOpen}
                onReset={onSortFilterReset}
                label="Sort & Filter"
              />
              <Typography variant="body-sm" color="secondary">
                Click to toggle active state, X to reset
              </Typography>
            </div>
          </div>
        </div>
      </Subsection>

      {/* SearchFilterBar - Task 34.15 */}
      <Subsection title="SearchFilterBar">
        <div className="space-y-4">
          {/* Default */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default Layout
            </Typography>
            <div className="max-w-2xl">
              <SearchFilterBar
                searchValue={searchFilterValue}
                onSearchChange={setSearchFilterValue}
                sortFilterActive={sortFilterActive}
                onSortFilterOpen={onSortFilterOpen}
                onSortFilterReset={onSortFilterReset}
                searchPlaceholder="Search tasks..."
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              SortFilterButton on left (fixed width), SearchBar expands to fill remaining space
            </Typography>
          </div>

          {/* With Active Filters */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Active Filters
            </Typography>
            <div className="max-w-2xl">
              <SearchFilterBar
                searchValue="example search"
                onSearchChange={() => {}}
                sortFilterActive={true}
                onSortFilterOpen={() => console.log("Open popup")}
                onSortFilterReset={() => console.log("Reset")}
                searchPlaceholder="Search..."
              />
            </div>
          </div>

          {/* Disabled */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Disabled
            </Typography>
            <div className="max-w-2xl">
              <SearchFilterBar
                searchValue=""
                onSearchChange={() => {}}
                sortFilterActive={false}
                onSortFilterOpen={() => {}}
                onSortFilterReset={() => {}}
                searchPlaceholder="Search..."
                searchDisabled
                sortFilterDisabled
              />
            </div>
          </div>
        </div>
      </Subsection>

      {/* ThemePreviewSkeleton - Task 43.1 */}
      <Subsection title="ThemePreviewSkeleton">
        <div className="space-y-6">
          {/* All Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              All Variants
            </Typography>
            <div className="flex flex-wrap items-start gap-6">
              {/* Full variant */}
              <div className="text-center">
                <div className="w-[400px]">
                  <ThemePreviewSkeleton
                    colorScheme={demoColorScheme}
                    typography={demoTypography}
                    effects={demoEffects}
                    variant="full"
                  />
                </div>
                <Typography variant="caption" color="muted" className="block mt-2">
                  Full (400px width)
                </Typography>
              </div>
            </div>
          </div>

          {/* Mini and Button variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Compact Variants
            </Typography>
            <div className="flex flex-wrap items-end gap-6">
              {/* Mini variant */}
              <div className="text-center">
                <ThemePreviewSkeleton
                  colorScheme={demoColorScheme}
                  typography={demoTypography}
                  effects={demoEffects}
                  variant="mini"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Mini (160x100px)
                </Typography>
              </div>

              {/* Button variant */}
              <div className="text-center">
                <ThemePreviewSkeleton
                  colorScheme={demoColorScheme}
                  typography={demoTypography}
                  effects={demoEffects}
                  variant="button"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Button (40x28px)
                </Typography>
              </div>
            </div>
          </div>

          {/* Different Color Schemes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Different Color Schemes
            </Typography>
            <div className="flex flex-wrap gap-4">
              {[colorThemes.dark, colorThemes.light, colorThemes.ocean, colorThemes.sunset].map((scheme) => (
                <div key={scheme.id} className="text-center">
                  <ThemePreviewSkeleton
                    colorScheme={scheme}
                    typography={fontThemes.inter}
                    effects={defaultEffectSettings}
                    variant="mini"
                  />
                  <Typography variant="caption" color="muted" className="block mt-2">
                    {scheme.name}
                  </Typography>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Subsection>

      {/* ColorSchemeMiniPreview - Task 43.4 */}
      <Subsection title="ColorSchemeMiniPreview">
        <div className="space-y-6">
          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="flex flex-wrap items-end gap-4">
              <div className="text-center">
                <ColorSchemeMiniPreview
                  scheme={colorThemes.dark}
                  isSelected={false}
                  onClick={() => console.log("Selected")}
                  size="sm"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Small
                </Typography>
              </div>
              <div className="text-center">
                <ColorSchemeMiniPreview
                  scheme={colorThemes.dark}
                  isSelected={false}
                  onClick={() => console.log("Selected")}
                  size="md"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Medium
                </Typography>
              </div>
              <div className="text-center">
                <ColorSchemeMiniPreview
                  scheme={colorThemes.dark}
                  isSelected={false}
                  onClick={() => console.log("Selected")}
                  size="lg"
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Large
                </Typography>
              </div>
            </div>
          </div>

          {/* Selection States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Selection States
            </Typography>
            <div className="flex flex-wrap gap-4">
              <div className="text-center">
                <ColorSchemeMiniPreview
                  scheme={colorThemes.ocean}
                  isSelected={false}
                  onClick={() => console.log("Selected")}
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Unselected
                </Typography>
              </div>
              <div className="text-center">
                <ColorSchemeMiniPreview
                  scheme={colorThemes.ocean}
                  isSelected={true}
                  onClick={() => console.log("Selected")}
                />
                <Typography variant="caption" color="muted" className="block mt-2">
                  Selected
                </Typography>
              </div>
            </div>
          </div>

          {/* Different Schemes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Different Color Schemes
            </Typography>
            <div className="flex flex-wrap gap-3">
              {[colorThemes.dark, colorThemes.light, colorThemes.ocean, colorThemes.sunset, colorThemes.forest, colorThemes.lavender].map((scheme) => (
                <ColorSchemeMiniPreview
                  key={scheme.id}
                  scheme={scheme}
                  isSelected={scheme.id === demoColorScheme.id}
                  onClick={() => setDemoColorScheme(scheme)}
                />
              ))}
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Click to select a scheme - updates the ThemePreviewSkeleton demos above
            </Typography>
          </div>
        </div>
      </Subsection>

      {/* ColorSchemeRow - Task 43.5 */}
      <Subsection title="ColorSchemeRow">
        <div className="space-y-6">
          {/* Interactive Demo */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Interactive Demo (Horizontally Scrollable)
            </Typography>
            <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--bg-surface)]">
              <ColorSchemeRow
                schemes={Object.values(colorThemes)}
                selectedSchemeId={demoColorScheme.id}
                onSelect={(id) => setDemoColorScheme(colorThemes[id])}
                autoScrollToSelected
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Selected: {demoColorScheme.name} - Auto-scrolls to selected scheme on mount
            </Typography>
          </div>

          {/* Without Auto-scroll */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Without Auto-scroll
            </Typography>
            <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--bg-surface)]">
              <ColorSchemeRow
                schemes={Object.values(colorThemes).slice(0, 6)}
                selectedSchemeId="ocean"
                onSelect={() => {}}
                autoScrollToSelected={false}
              />
            </div>
          </div>
        </div>
      </Subsection>

      {/* TypographyRow - Task 43.6 */}
      <Subsection title="TypographyRow">
        <div className="space-y-6">
          {/* Interactive Demo */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Interactive Demo (Horizontally Scrollable)
            </Typography>
            <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--bg-surface)]">
              <TypographyRow
                options={Object.values(fontThemes)}
                selectedOptionId={demoTypography.id}
                onSelect={(id) => setDemoTypography(fontThemes[id])}
                autoScrollToSelected
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Selected: {demoTypography.name} ({demoTypography.category}) - Auto-scrolls to selected typography on mount
            </Typography>
          </div>

          {/* Subset of Fonts */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Professional Fonts Only
            </Typography>
            <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--bg-surface)]">
              <TypographyRow
                options={Object.values(fontThemes).filter(f => f.category === "professional")}
                selectedOptionId="inter"
                onSelect={() => {}}
              />
            </div>
          </div>
        </div>
      </Subsection>

      {/* TaskCompletionProgress - Task 53.2 */}
      <Subsection title="TaskCompletionProgress">
        <div className="space-y-6">
          {/* Default Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default Variant
            </Typography>
            <div className="space-y-4 max-w-md">
              <TaskCompletionProgress completed={0} total={10} />
              <TaskCompletionProgress completed={3} total={10} />
              <TaskCompletionProgress completed={7} total={10} />
              <TaskCompletionProgress completed={10} total={10} />
            </div>
          </div>

          {/* Mini Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Mini Variant (Compact)
            </Typography>
            <div className="space-y-3 max-w-md">
              <TaskCompletionProgress completed={2} total={8} variant="mini" />
              <TaskCompletionProgress completed={5} total={8} variant="mini" />
              <TaskCompletionProgress completed={8} total={8} variant="mini" />
            </div>
          </div>

          {/* Edge Cases */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Edge Cases
            </Typography>
            <div className="space-y-4 max-w-md">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Empty (0/0)</Typography>
                <TaskCompletionProgress completed={0} total={0} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Large Numbers</Typography>
                <TaskCompletionProgress completed={847} total={1000} />
              </div>
            </div>
          </div>
        </div>
      </Subsection>

      {/* PercentageProgress - Task 53.3 */}
      <Subsection title="PercentageProgress">
        <div className="space-y-6">
          {/* Default Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default Variant
            </Typography>
            <div className="space-y-4 max-w-md">
              <PercentageProgress percentage={0} />
              <PercentageProgress percentage={25} />
              <PercentageProgress percentage={50} />
              <PercentageProgress percentage={75} />
              <PercentageProgress percentage={100} />
            </div>
          </div>

          {/* Mini Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Mini Variant (Compact)
            </Typography>
            <div className="space-y-3 max-w-md">
              <PercentageProgress percentage={33} variant="mini" />
              <PercentageProgress percentage={66} variant="mini" />
              <PercentageProgress percentage={100} variant="mini" />
            </div>
          </div>

          {/* Custom Labels */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Custom Labels
            </Typography>
            <div className="space-y-4 max-w-md">
              <PercentageProgress percentage={45} label="complete" />
              <PercentageProgress percentage={60} label="done" />
              <PercentageProgress percentage={80} label="finished" />
            </div>
          </div>

          {/* Custom Colors */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Custom Colors
            </Typography>
            <div className="space-y-4 max-w-md">
              <PercentageProgress percentage={50} color="var(--success)" label="success" />
              <PercentageProgress percentage={50} color="var(--warning)" label="warning" />
              <PercentageProgress percentage={50} color="var(--error)" label="error" />
              <PercentageProgress percentage={50} color="var(--info)" label="info" />
            </div>
          </div>
        </div>
      </Subsection>

      {/* ReadyTasksProgress - Task 53.4 */}
      <Subsection title="ReadyTasksProgress">
        <div className="space-y-6">
          {/* Default Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default Variant
            </Typography>
            <div className="space-y-4 max-w-md">
              <ReadyTasksProgress readyCount={0} totalCount={10} />
              <ReadyTasksProgress readyCount={3} totalCount={10} />
              <ReadyTasksProgress readyCount={7} totalCount={10} />
              <ReadyTasksProgress readyCount={10} totalCount={10} />
            </div>
          </div>

          {/* Mini Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Mini Variant (Compact)
            </Typography>
            <div className="space-y-3 max-w-md">
              <ReadyTasksProgress readyCount={2} totalCount={8} variant="mini" />
              <ReadyTasksProgress readyCount={5} totalCount={8} variant="mini" />
              <ReadyTasksProgress readyCount={8} totalCount={8} variant="mini" />
            </div>
          </div>

          {/* Edge Cases */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Edge Cases
            </Typography>
            <div className="space-y-4 max-w-md">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Empty (0/0)</Typography>
                <ReadyTasksProgress readyCount={0} totalCount={0} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">All Ready</Typography>
                <ReadyTasksProgress readyCount={15} totalCount={15} />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">None Ready</Typography>
                <ReadyTasksProgress readyCount={0} totalCount={15} />
              </div>
            </div>
          </div>
        </div>
      </Subsection>
    </div>
  );
};

/**
 * OrganismsSection Component
 * Renders each organism component with sample data
 * Requirements: 9.3
 */
interface OrganismsSectionProps {
  onOpenCustomizationPopup: () => void;
  onOpenTaskDetailModal: () => void;
  // New props for Task 34
  onOpenCreateProjectModal: () => void;
  onOpenCreateTaskListModal: () => void;
  onOpenCreateTaskModal: () => void;
  onOpenEditProjectModal: () => void;
  onOpenEditTaskListModal: () => void;
  onOpenDeleteDialog: () => void;
  onOpenSortFilterPopup: () => void;
  currentView: DashboardView;
  onViewChange: (view: DashboardView) => void;
  isSortFilterPopupOpen: boolean;
  onCloseSortFilterPopup: () => void;
  activeSortId: string;
  onSortChange: (id: string) => void;
  activeFilters: string[];
  onFilterChange: (filters: string[]) => void;
  sortFilterButtonRef: React.RefObject<HTMLDivElement>;
  // Props for Task 43 - Customization components
  demoColorScheme: ColorTheme;
  setDemoColorScheme: (scheme: ColorTheme) => void;
  demoTypography: FontTheme;
  setDemoTypography: (typography: FontTheme) => void;
  demoEffects: EffectSettings;
  setDemoEffects: (effects: EffectSettings) => void;
}

const OrganismsSection: React.FC<OrganismsSectionProps> = ({
  onOpenCustomizationPopup,
  onOpenTaskDetailModal,
  onOpenCreateProjectModal,
  onOpenCreateTaskListModal,
  onOpenCreateTaskModal,
  onOpenEditProjectModal,
  onOpenEditTaskListModal,
  onOpenDeleteDialog,
  onOpenSortFilterPopup,
  currentView,
  onViewChange,
  isSortFilterPopupOpen,
  onCloseSortFilterPopup,
  activeSortId,
  onSortChange,
  activeFilters,
  onFilterChange,
  sortFilterButtonRef,
  demoColorScheme,
  setDemoColorScheme,
  demoTypography,
  setDemoTypography,
  demoEffects,
  setDemoEffects,
}) => {
  // Additional sample tasks for variety
  const tasks: Task[] = [
    sampleTask,
    {
      ...sampleTask,
      id: "task-2",
      title: "Design database schema",
      description: "Create ERD and define table structures",
      status: "COMPLETED",
      priority: "MEDIUM",
      exitCriteria: [
        { criteria: "ERD created", status: "COMPLETE" },
        { criteria: "Tables defined", status: "COMPLETE" },
      ],
      tags: ["database", "design"],
    },
    {
      ...sampleTask,
      id: "task-3",
      title: "Fix critical bug in payment flow",
      status: "BLOCKED",
      priority: "CRITICAL",
      dependencies: [
        { taskId: "task-1", taskListId: "list-1" },
        { taskId: "task-2", taskListId: "list-1" },
      ],
      exitCriteria: [],
      tags: ["bug", "payment"],
    },
    {
      ...sampleTask,
      id: "task-4",
      title: "Write unit tests",
      status: "NOT_STARTED",
      priority: "LOW",
      dependencies: [],
      exitCriteria: [],
      tags: [],
    },
  ];

  return (
    <div className="space-y-8">
      {/* TaskCard */}
      <Subsection title="TaskCard">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Different Task States
          </Typography>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onClick={() => console.log("Task clicked:", task.id)}
              />
            ))}
          </div>
        </div>
      </Subsection>

      {/* ProjectCard - Updated for Task 34.10 */}
      <Subsection title="ProjectCard">
        <div className="space-y-6">
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Stats and Action Buttons (Hover to see edit/delete)
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <ProjectCard
                project={sampleProject}
                stats={sampleProjectStats}
                onClick={() => console.log("Project clicked")}
                onEdit={(project) => console.log("Edit project:", project.name)}
                onDelete={(project) => console.log("Delete project:", project.name)}
              />
              <ProjectCard
                project={{
                  ...sampleProject,
                  id: "project-2",
                  name: "API Gateway",
                  description: "Centralized API management and routing",
                }}
                stats={{
                  ...sampleProjectStats,
                  totalTasks: 15,
                  completedTasks: 15,
                  inProgressTasks: 0,
                  blockedTasks: 0,
                }}
                onClick={() => console.log("Project clicked")}
                onEdit={(project) => console.log("Edit project:", project.name)}
                onDelete={(project) => console.log("Delete project:", project.name)}
              />
              <ProjectCard
                project={{
                  ...sampleProject,
                  id: "project-3",
                  name: "New Project",
                }}
                onClick={() => console.log("Project clicked")}
                onEdit={(project) => console.log("Edit project:", project.name)}
                onDelete={(project) => console.log("Delete project:", project.name)}
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Hover over cards to reveal edit and delete action buttons
            </Typography>
          </div>
        </div>
      </Subsection>

      {/* TaskListCard - Updated for Task 34.10 */}
      <Subsection title="TaskListCard">
        <div className="space-y-6">
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Stats and Action Buttons (Hover to see edit/delete)
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <TaskListCard
                taskList={sampleTaskList}
                stats={sampleTaskListStats}
                onClick={() => console.log("TaskList clicked")}
                onEdit={(taskList) => console.log("Edit task list:", taskList.name)}
                onDelete={(taskList) => console.log("Delete task list:", taskList.name)}
              />
              <TaskListCard
                taskList={{
                  ...sampleTaskList,
                  id: "list-2",
                  name: "Sprint 2 - Polish",
                  description: "Bug fixes and UI improvements",
                }}
                stats={{
                  ...sampleTaskListStats,
                  taskCount: 12,
                  completedTasks: 10,
                  completionPercentage: 83,
                }}
                onClick={() => console.log("TaskList clicked")}
                onEdit={(taskList) => console.log("Edit task list:", taskList.name)}
                onDelete={(taskList) => console.log("Delete task list:", taskList.name)}
              />
              <TaskListCard
                taskList={{
                  ...sampleTaskList,
                  id: "list-3",
                  name: "Backlog",
                }}
                onClick={() => console.log("TaskList clicked")}
                onEdit={(taskList) => console.log("Edit task list:", taskList.name)}
                onDelete={(taskList) => console.log("Delete task list:", taskList.name)}
              />
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Hover over cards to reveal edit and delete action buttons
            </Typography>
          </div>
        </div>
      </Subsection>

      {/* CustomizationPopup (Replaces CustomizationDrawer - Requirement 53) */}
      <Subsection title="CustomizationPopup">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Popup (Replaces CustomizationDrawer)
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            The CustomizationPopup provides a centered modal with live preview, effects controls, 
            color scheme selection, and typography options. This replaces the deprecated CustomizationDrawer.
            Click the button below to open the popup and see it in action.
          </Typography>
          <Button variant="primary" onClick={onOpenCustomizationPopup}>
            Open Customization Popup
          </Button>
        </div>
      </Subsection>

      {/* TaskDetailModal */}
      <Subsection title="TaskDetailModal">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            The TaskDetailModal displays full task information including notes, dependencies, exit criteria, and metadata.
            Click the button below to open the modal with sample task data.
          </Typography>
          <Button variant="primary" onClick={onOpenTaskDetailModal}>
            Open Task Detail Modal
          </Button>
        </div>
      </Subsection>

      {/* AppHeader - Task 34.1 */}
      <Subsection title="AppHeader">
        <div className="space-y-6">
          {/* Logo Variants */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Logo Variants
            </Typography>
            <div className="space-y-4 border border-[var(--border)] rounded-lg overflow-hidden">
              <AppHeader title="Task Manager" logoVariant="both" sticky={false} />
              <AppHeader title="Task Manager" logoVariant="icon" sticky={false} />
              <AppHeader title="Task Manager" logoVariant="text" sticky={false} />
            </div>
          </div>

          {/* Logo Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Logo Sizes
            </Typography>
            <div className="space-y-4 border border-[var(--border)] rounded-lg overflow-hidden">
              <AppHeader title="Small" logoSize="sm" sticky={false} />
              <AppHeader title="Medium" logoSize="md" sticky={false} />
              <AppHeader title="Large" logoSize="lg" sticky={false} />
            </div>
          </div>

          {/* With Children */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              With Navigation Content
            </Typography>
            <div className="border border-[var(--border)] rounded-lg overflow-hidden">
              <AppHeader title="Task Manager" sticky={false}>
                <Button variant="ghost" size="sm">Settings</Button>
                <Button variant="primary" size="sm">New Task</Button>
              </AppHeader>
            </div>
          </div>
        </div>
      </Subsection>

      {/* ViewSelector - Task 34.2 */}
      <Subsection title="ViewSelector">
        <div className="space-y-6">
          {/* Interactive Demo */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Interactive Demo
            </Typography>
            <ViewSelector
              currentView={currentView}
              onViewChange={onViewChange}
            />
            <Typography variant="caption" color="muted" className="mt-2 block">
              Current view: {currentView}
            </Typography>
          </div>

          {/* Sizes */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Sizes
            </Typography>
            <div className="space-y-4">
              <div>
                <ViewSelector currentView="dashboard" onViewChange={() => {}} size="sm" />
                <Typography variant="caption" color="muted" className="block mt-1">Small</Typography>
              </div>
              <div>
                <ViewSelector currentView="dashboard" onViewChange={() => {}} size="md" />
                <Typography variant="caption" color="muted" className="block mt-1">Medium</Typography>
              </div>
              <div>
                <ViewSelector currentView="dashboard" onViewChange={() => {}} size="lg" />
                <Typography variant="caption" color="muted" className="block mt-1">Large</Typography>
              </div>
            </div>
          </div>

          {/* Without Labels */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Icons Only (No Labels)
            </Typography>
            <ViewSelector currentView="projects" onViewChange={() => {}} showLabels={false} />
          </div>

          {/* Without Glass Effect */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Without Glassmorphism
            </Typography>
            <ViewSelector currentView="tasks" onViewChange={() => {}} glass={false} />
          </div>
        </div>
      </Subsection>

      {/* FAB - Task 34.3 */}
      <Subsection title="FAB (Floating Action Button)">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Demo
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            The FAB is positioned in the bottom-right corner of the screen. Click the + button to expand
            and see the action options. Click outside or press the button again to collapse.
          </Typography>
          <div className="relative h-64 bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center">
              <Typography variant="body-sm" color="muted">
                FAB is positioned in the bottom-right corner of the viewport
              </Typography>
            </div>
          </div>
          <Typography variant="caption" color="muted">
            Note: The FAB component is rendered at the page level and appears in the bottom-right corner of the screen.
          </Typography>
        </div>
      </Subsection>

      {/* CreateProjectModal - Task 34.4 */}
      <Subsection title="CreateProjectModal">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A modal dialog for creating new projects with form validation.
          </Typography>
          <Button variant="primary" onClick={onOpenCreateProjectModal}>
            Open Create Project Modal
          </Button>
        </div>
      </Subsection>

      {/* CreateTaskListModal - Task 34.5 */}
      <Subsection title="CreateTaskListModal">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A modal dialog for creating new task lists with project selection.
          </Typography>
          <Button variant="primary" onClick={onOpenCreateTaskListModal}>
            Open Create Task List Modal
          </Button>
        </div>
      </Subsection>

      {/* CreateTaskModal - Task 34.6 */}
      <Subsection title="CreateTaskModal">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A comprehensive modal for creating new tasks with priority, status, dependencies, and exit criteria.
          </Typography>
          <Button variant="primary" onClick={onOpenCreateTaskModal}>
            Open Create Task Modal
          </Button>
        </div>
      </Subsection>

      {/* EditProjectModal - Task 34.7 */}
      <Subsection title="EditProjectModal">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A modal dialog for editing existing projects with pre-populated form fields.
          </Typography>
          <Button variant="primary" onClick={onOpenEditProjectModal}>
            Open Edit Project Modal
          </Button>
        </div>
      </Subsection>

      {/* EditTaskListModal - Task 34.8 */}
      <Subsection title="EditTaskListModal">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A modal dialog for editing existing task lists with pre-populated form fields.
          </Typography>
          <Button variant="primary" onClick={onOpenEditTaskListModal}>
            Open Edit Task List Modal
          </Button>
        </div>
      </Subsection>

      {/* DeleteConfirmationDialog - Task 34.9 */}
      <Subsection title="DeleteConfirmationDialog">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Dialog
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A confirmation dialog for destructive actions with cascading deletion warnings.
          </Typography>
          <Button variant="destructive" onClick={onOpenDeleteDialog}>
            Open Delete Confirmation Dialog
          </Button>
        </div>
      </Subsection>

      {/* ProjectGroup - Task 34.11 */}
      <Subsection title="ProjectGroup">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Collapsible Project with Task Lists
          </Typography>
          <ProjectGroup
            project={sampleProject}
            taskLists={[
              sampleTaskList,
              { ...sampleTaskList, id: "list-2", name: "Sprint 2 - Polish" },
              { ...sampleTaskList, id: "list-3", name: "Backlog" },
            ]}
            stats={sampleProjectStats}
            taskListStats={{
              "list-1": sampleTaskListStats,
              "list-2": { ...sampleTaskListStats, completionPercentage: 75 },
              "list-3": { ...sampleTaskListStats, completionPercentage: 0 },
            }}
            defaultExpanded={true}
            onTaskListClick={(id) => console.log("Task list clicked:", id)}
          />
        </div>

        <div className="space-y-4 mt-6">
          <Typography variant="label" color="muted" className="mb-3 block">
            Collapsed State
          </Typography>
          <ProjectGroup
            project={{ ...sampleProject, id: "project-2", name: "API Gateway" }}
            taskLists={[
              { ...sampleTaskList, id: "list-4", name: "API Design" },
              { ...sampleTaskList, id: "list-5", name: "Implementation" },
            ]}
            defaultExpanded={false}
          />
        </div>

        <div className="space-y-4 mt-6">
          <Typography variant="label" color="muted" className="mb-3 block">
            Empty Project
          </Typography>
          <ProjectGroup
            project={{ ...sampleProject, id: "project-3", name: "New Project" }}
            taskLists={[]}
            defaultExpanded={true}
          />
        </div>
      </Subsection>

      {/* SortFilterPopup */}
      <Subsection title="SortFilterPopup">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Demo
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            Click the button to open the sort and filter popup. The popup supports multiple selections
            and closes on outside click or when the button is clicked again.
          </Typography>
          <div ref={sortFilterButtonRef} className="relative inline-block">
            <Button variant="secondary" onClick={onOpenSortFilterPopup}>
              Open Sort & Filter Popup
            </Button>
            <div className="absolute top-full left-0 mt-2 z-50">
              <SortFilterPopup
                isOpen={isSortFilterPopupOpen}
                onClose={onCloseSortFilterPopup}
                sortOptions={[
                  { id: "name", label: "Name" },
                  { id: "date", label: "Date Created" },
                  { id: "priority", label: "Priority" },
                  { id: "status", label: "Status" },
                ]}
                filterOptions={[
                  { id: "high", label: "High Priority", type: "checkbox", group: "Priority" },
                  { id: "medium", label: "Medium Priority", type: "checkbox", group: "Priority" },
                  { id: "low", label: "Low Priority", type: "checkbox", group: "Priority" },
                  { id: "completed", label: "Completed", type: "checkbox", group: "Status" },
                  { id: "in_progress", label: "In Progress", type: "checkbox", group: "Status" },
                  { id: "blocked", label: "Blocked", type: "checkbox", group: "Status" },
                ]}
                activeSortId={activeSortId}
                activeFilters={activeFilters}
                onSortChange={onSortChange}
                onFilterChange={onFilterChange}
              />
            </div>
          </div>
          <Typography variant="caption" color="muted" className="block mt-2">
            Active sort: {activeSortId} | Active filters: {activeFilters.length > 0 ? activeFilters.join(", ") : "none"}
          </Typography>
        </div>
      </Subsection>

      {/* LivePreviewPanel - Task 43.2 */}
      <Subsection title="LivePreviewPanel">
        <div className="space-y-6">
          {/* Default */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default (with Padding) - Interactive
            </Typography>
            <div className="flex gap-4">
              <div className="flex-1 max-w-2xl">
                <LivePreviewPanel
                  colorScheme={demoColorScheme}
                  typography={demoTypography}
                  effects={demoEffects}
                  showPadding={true}
                  title="Live Preview"
                  className="h-[450px]"
                />
              </div>
              <div className="w-64 space-y-4">
                <div>
                  <Typography variant="label" color="muted" className="mb-2 block">
                    Quick Color Scheme
                  </Typography>
                  <div className="flex flex-wrap gap-2">
                    {[colorThemes.dark, colorThemes.light, colorThemes.ocean, colorThemes.sunset].map((scheme) => (
                      <button
                        key={scheme.id}
                        onClick={() => setDemoColorScheme(scheme)}
                        className={`px-3 py-1 text-xs rounded border transition-all ${
                          demoColorScheme.id === scheme.id
                            ? "border-[var(--primary)] bg-[var(--primary)] text-white"
                            : "border-[var(--border)] hover:border-[var(--primary)]"
                        }`}
                      >
                        {scheme.name}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Typography variant="label" color="muted" className="mb-2 block">
                    Quick Typography
                  </Typography>
                  <div className="flex flex-wrap gap-2">
                    {[fontThemes.inter, fontThemes.roboto, fontThemes.quicksand, fontThemes.firaCode].map((font) => (
                      <button
                        key={font.id}
                        onClick={() => setDemoTypography(font)}
                        className={`px-3 py-1 text-xs rounded border transition-all ${
                          demoTypography.id === font.id
                            ? "border-[var(--primary)] bg-[var(--primary)] text-white"
                            : "border-[var(--border)] hover:border-[var(--primary)]"
                        }`}
                      >
                        {font.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <Typography variant="caption" color="muted" className="mt-2 block">
              Updates in real-time when color scheme, typography, or effects change. Use the buttons to test.
            </Typography>
          </div>

          {/* Without Padding */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Without Padding
            </Typography>
            <div className="max-w-xl">
              <LivePreviewPanel
                colorScheme={demoColorScheme}
                typography={demoTypography}
                effects={demoEffects}
                showPadding={false}
                title="Compact Preview"
                className="h-[350px]"
              />
            </div>
          </div>

          {/* Custom Title */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Custom Title
            </Typography>
            <div className="max-w-md">
              <LivePreviewPanel
                colorScheme={colorThemes.ocean}
                typography={fontThemes.inter}
                effects={defaultEffectSettings}
                title="Ocean Theme Preview"
                className="h-[300px]"
              />
            </div>
          </div>
        </div>
      </Subsection>

      {/* EffectsControlPanel - Task 43.3 */}
      <Subsection title="EffectsControlPanel">
        <div className="space-y-6">
          {/* Interactive Demo */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Interactive Demo
            </Typography>
            <Typography variant="body-sm" color="secondary" className="mb-4">
              Adjust the sliders to see real-time updates in the LivePreviewPanel and ThemePreviewSkeleton demos above.
            </Typography>
            <div className="max-w-sm">
              <EffectsControlPanel
                effects={demoEffects}
                onChange={(key, value) => {
                  setDemoEffects({ ...demoEffects, [key]: value });
                }}
                className="max-h-[500px] overflow-y-auto"
              />
            </div>
          </div>

          {/* Disabled State */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Disabled State
            </Typography>
            <div className="max-w-sm">
              <EffectsControlPanel
                effects={defaultEffectSettings}
                onChange={() => {}}
                disabled
              />
            </div>
          </div>
        </div>
      </Subsection>

      {/* CustomizationPopup - Task 43.7 */}
      <Subsection title="CustomizationPopup">
        <div className="space-y-4">
          <Typography variant="label" color="muted" className="mb-3 block">
            Interactive Modal
          </Typography>
          <Typography variant="body-sm" color="secondary" className="mb-4">
            A comprehensive customization popup with live preview, effects controls, color scheme selection,
            and typography selection. The popup is centered on the screen with a dimmed and blurred background.
          </Typography>
          <Button variant="primary" onClick={onOpenCustomizationPopup}>
            Open Customization Popup
          </Button>
          <Typography variant="caption" color="muted" className="block mt-2">
            Features: Live preview panel, effects sliders, color scheme row, typography row, glassmorphism effect
          </Typography>
        </div>
      </Subsection>

      {/* TaskStatusSummary - Task 53.5 */}
      <Subsection title="TaskStatusSummary">
        <div className="space-y-6">
          {/* Default Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default Variant (with Labels)
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TaskStatusSummary
                statusCounts={{ completed: 5, inProgress: 3, blocked: 1, notStarted: 3 }}
              />
              <TaskStatusSummary
                statusCounts={{ completed: 10, inProgress: 0, blocked: 0, notStarted: 0 }}
              />
            </div>
          </div>

          {/* Compact Variant */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Compact Variant
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TaskStatusSummary
                statusCounts={{ completed: 3, inProgress: 4, blocked: 2, notStarted: 1 }}
                variant="compact"
              />
              <TaskStatusSummary
                statusCounts={{ completed: 8, inProgress: 2, blocked: 0, notStarted: 0 }}
                variant="compact"
              />
            </div>
          </div>

          {/* Without Labels */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Without Labels
            </Typography>
            <div className="max-w-md">
              <TaskStatusSummary
                statusCounts={{ completed: 4, inProgress: 3, blocked: 1, notStarted: 2 }}
                showLabels={false}
              />
            </div>
          </div>

          {/* Different Status Distributions */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Different Status Distributions
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">All Completed</Typography>
                <TaskStatusSummary
                  statusCounts={{ completed: 12, inProgress: 0, blocked: 0, notStarted: 0 }}
                  variant="compact"
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Mostly Blocked</Typography>
                <TaskStatusSummary
                  statusCounts={{ completed: 1, inProgress: 1, blocked: 8, notStarted: 2 }}
                  variant="compact"
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Not Started</Typography>
                <TaskStatusSummary
                  statusCounts={{ completed: 0, inProgress: 0, blocked: 0, notStarted: 10 }}
                  variant="compact"
                />
              </div>
            </div>
          </div>
        </div>
      </Subsection>

      {/* ProjectProgressSummary - Task 53.6 */}
      <Subsection title="ProjectProgressSummary">
        <div className="space-y-6">
          {/* Default */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default (with Sample Data)
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ProjectProgressSummary
                project={sampleProject}
                taskLists={[sampleTaskList, { ...sampleTaskList, id: "list-2", name: "Sprint 2" }]}
                tasks={tasks}
              />
              <ProjectProgressSummary
                project={{ ...sampleProject, id: "project-2", name: "API Gateway" }}
                taskLists={[{ ...sampleTaskList, id: "list-3", name: "API Design" }]}
                tasks={[
                  { ...tasks[0], id: "t1", status: "COMPLETED" },
                  { ...tasks[0], id: "t2", status: "COMPLETED" },
                  { ...tasks[0], id: "t3", status: "COMPLETED" },
                  { ...tasks[0], id: "t4", status: "IN_PROGRESS" },
                  { ...tasks[0], id: "t5", status: "NOT_STARTED" },
                ]}
              />
            </div>
          </div>

          {/* Different Progress States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Different Progress States
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Just Started</Typography>
                <ProjectProgressSummary
                  project={{ ...sampleProject, id: "p1", name: "New Project" }}
                  taskLists={[sampleTaskList]}
                  tasks={[
                    { ...tasks[0], id: "t1", status: "NOT_STARTED" },
                    { ...tasks[0], id: "t2", status: "NOT_STARTED" },
                    { ...tasks[0], id: "t3", status: "NOT_STARTED" },
                  ]}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">In Progress</Typography>
                <ProjectProgressSummary
                  project={{ ...sampleProject, id: "p2", name: "Active Project" }}
                  taskLists={[sampleTaskList, { ...sampleTaskList, id: "l2" }]}
                  tasks={[
                    { ...tasks[0], id: "t1", status: "COMPLETED" },
                    { ...tasks[0], id: "t2", status: "COMPLETED" },
                    { ...tasks[0], id: "t3", status: "IN_PROGRESS" },
                    { ...tasks[0], id: "t4", status: "IN_PROGRESS" },
                    { ...tasks[0], id: "t5", status: "BLOCKED" },
                    { ...tasks[0], id: "t6", status: "NOT_STARTED" },
                  ]}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Completed</Typography>
                <ProjectProgressSummary
                  project={{ ...sampleProject, id: "p3", name: "Done Project" }}
                  taskLists={[sampleTaskList]}
                  tasks={[
                    { ...tasks[0], id: "t1", status: "COMPLETED" },
                    { ...tasks[0], id: "t2", status: "COMPLETED" },
                    { ...tasks[0], id: "t3", status: "COMPLETED" },
                    { ...tasks[0], id: "t4", status: "COMPLETED" },
                  ]}
                />
              </div>
            </div>
          </div>
        </div>
      </Subsection>

      {/* TaskListProgressSummary - Task 53.7 */}
      <Subsection title="TaskListProgressSummary">
        <div className="space-y-6">
          {/* Default */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default (with Sample Data)
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TaskListProgressSummary
                taskList={sampleTaskList}
                tasks={tasks}
                readyTaskCount={2}
              />
              <TaskListProgressSummary
                taskList={{ ...sampleTaskList, id: "list-2", name: "Sprint 2 - Polish" }}
                tasks={[
                  { ...tasks[0], id: "t1", status: "COMPLETED" },
                  { ...tasks[0], id: "t2", status: "COMPLETED" },
                  { ...tasks[0], id: "t3", status: "COMPLETED" },
                  { ...tasks[0], id: "t4", status: "IN_PROGRESS" },
                  { ...tasks[0], id: "t5", status: "NOT_STARTED" },
                ]}
                readyTaskCount={1}
              />
            </div>
          </div>

          {/* Different Progress States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Different Progress States
            </Typography>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Empty List</Typography>
                <TaskListProgressSummary
                  taskList={{ ...sampleTaskList, id: "l1", name: "Backlog" }}
                  tasks={[]}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Blocked Tasks</Typography>
                <TaskListProgressSummary
                  taskList={{ ...sampleTaskList, id: "l2", name: "Blocked Sprint" }}
                  tasks={[
                    { ...tasks[0], id: "t1", status: "COMPLETED" },
                    { ...tasks[0], id: "t2", status: "BLOCKED" },
                    { ...tasks[0], id: "t3", status: "BLOCKED" },
                    { ...tasks[0], id: "t4", status: "BLOCKED" },
                  ]}
                  readyTaskCount={0}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">All Ready</Typography>
                <TaskListProgressSummary
                  taskList={{ ...sampleTaskList, id: "l3", name: "Ready Sprint" }}
                  tasks={[
                    { ...tasks[0], id: "t1", status: "NOT_STARTED" },
                    { ...tasks[0], id: "t2", status: "NOT_STARTED" },
                    { ...tasks[0], id: "t3", status: "IN_PROGRESS" },
                  ]}
                  readyTaskCount={3}
                />
              </div>
            </div>
          </div>

          {/* Without Ready Task Count */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Without Ready Task Count (Auto-calculated)
            </Typography>
            <div className="max-w-md">
              <TaskListProgressSummary
                taskList={{ ...sampleTaskList, id: "l4", name: "Auto-calculated Ready" }}
                tasks={[
                  { ...tasks[0], id: "t1", status: "COMPLETED" },
                  { ...tasks[0], id: "t2", status: "IN_PROGRESS" },
                  { ...tasks[0], id: "t3", status: "NOT_STARTED" },
                  { ...tasks[0], id: "t4", status: "NOT_STARTED" },
                ]}
              />
              <Typography variant="caption" color="muted" className="mt-2 block">
                When readyTaskCount is not provided, it estimates based on NOT_STARTED + IN_PROGRESS tasks
              </Typography>
            </div>
          </div>
        </div>
      </Subsection>

      {/* OverallProgress */}
      <Subsection title="OverallProgress">
        <div className="space-y-6">
          {/* Default */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Default (Full Width with Circular Progress)
            </Typography>
            <div className="space-y-4">
              <OverallProgress
                statusCounts={{ completed: 12, inProgress: 5, blocked: 2, notStarted: 6 }}
              />
              <OverallProgress
                statusCounts={{ completed: 8, inProgress: 3, blocked: 1, notStarted: 3 }}
              />
            </div>
          </div>

          {/* Different Progress States */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Different Progress States
            </Typography>
            <div className="space-y-4">
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">All Completed</Typography>
                <OverallProgress
                  statusCounts={{ completed: 20, inProgress: 0, blocked: 0, notStarted: 0 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Mostly In Progress</Typography>
                <OverallProgress
                  statusCounts={{ completed: 3, inProgress: 12, blocked: 1, notStarted: 4 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Many Blocked</Typography>
                <OverallProgress
                  statusCounts={{ completed: 2, inProgress: 2, blocked: 8, notStarted: 3 }}
                />
              </div>
              <div>
                <Typography variant="caption" color="muted" className="mb-2 block">Not Started</Typography>
                <OverallProgress
                  statusCounts={{ completed: 0, inProgress: 0, blocked: 0, notStarted: 15 }}
                />
              </div>
            </div>
          </div>

          {/* Empty State */}
          <div>
            <Typography variant="label" color="muted" className="mb-3 block">
              Empty State (No Tasks)
            </Typography>
            <OverallProgress
              statusCounts={{ completed: 0, inProgress: 0, blocked: 0, notStarted: 0 }}
            />
          </div>
        </div>
      </Subsection>
    </div>
  );
};

export default ShowcasePage;
