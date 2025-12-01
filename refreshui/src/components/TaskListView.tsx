import React, { useState } from "react";
import {
  Search,
  Filter,
  List,
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
} from "lucide-react";
import { Input, Button } from "./ui";
import type { Project, TaskList, Task } from "../api/client";
import { SmallTaskCard } from "./SmallTaskCard";
import { FilterPopover } from "./FilterPopover";
import styles from "./TaskListView.module.css";

interface TaskListViewProps {
  projects: Project[];
  taskLists: TaskList[];
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  onTaskListClick: (taskListId: string, projectId: string) => void;
}

export const TaskListView: React.FC<TaskListViewProps> = ({
  projects,
  taskLists,
  tasks,
  onTaskClick,
  onTaskListClick,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [filters, setFilters] = useState({
    status: [] as string[],
    priority: [] as string[],
  });

  const handleFilterChange = (type: "status" | "priority", value: string) => {
    setFilters((prev) => {
      const current = prev[type];
      const updated = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value];
      return { ...prev, [type]: updated };
    });
  };

  const clearFilters = () => {
    setFilters({ status: [], priority: [] });
  };

  // Calculate stats for a task list
  const getListStats = (listId: string) => {
    const listTasks = tasks.filter((task) => {
      const matchesList = task.task_list_id === listId;
      const statusMatch =
        filters.status.length === 0 || filters.status.includes(task.status);
      const priorityMatch =
        filters.priority.length === 0 ||
        filters.priority.includes(task.priority);
      return matchesList && statusMatch && priorityMatch;
    });

    const completed = listTasks.filter((t) => t.status === "COMPLETED").length;
    const inProgress = listTasks.filter(
      (t) => t.status === "IN_PROGRESS"
    ).length;
    const blocked = listTasks.filter((t) => t.status === "BLOCKED").length;
    const notStarted = listTasks.filter(
      (t) => t.status === "NOT_STARTED"
    ).length;

    return {
      total: listTasks.length,
      completed,
      inProgress,
      blocked,
      notStarted,
      completionRate:
        listTasks.length > 0 ? (completed / listTasks.length) * 100 : 0,
      tasks: listTasks,
    };
  };

  // Filter projects and task lists by search query
  const filteredProjects = projects.filter((project) => {
    const projectMatches = project.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const hasMatchingLists = taskLists.some(
      (list) =>
        list.project_id === project.id &&
        list.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    const hasMatchingTasks = tasks.some((task) => {
      const taskList = taskLists.find((l) => l.id === task.task_list_id);
      const statusMatch =
        filters.status.length === 0 || filters.status.includes(task.status);
      const priorityMatch =
        filters.priority.length === 0 ||
        filters.priority.includes(task.priority);

      if (!statusMatch || !priorityMatch) return false;

      return (
        taskList?.project_id === project.id &&
        (task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          task.description?.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    });
    return projectMatches || hasMatchingLists || hasMatchingTasks;
  });

  return (
    <div className={styles.container}>
      <div className={styles.toolbar}>
        <div className={styles.searchContainer}>
          <Input
            icon={<Search size={16} />}
            placeholder="Search task lists or tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div style={{ position: "relative" }}>
          <Button
            variant={
              filters.status.length > 0 || filters.priority.length > 0
                ? "primary"
                : "secondary"
            }
            icon={<Filter size={16} />}
            onClick={() => setIsFilterOpen(!isFilterOpen)}
          >
            Filter
          </Button>
          <FilterPopover
            isOpen={isFilterOpen}
            onClose={() => setIsFilterOpen(false)}
            filters={filters}
            onFilterChange={handleFilterChange}
            onClear={clearFilters}
          />
        </div>
      </div>

      <div className={styles.content}>
        {filteredProjects.map((project) => {
          const projectLists = taskLists.filter(
            (list) => list.project_id === project.id
          );
          if (projectLists.length === 0) return null;

          // Dynamic width calculation
          // Base width of a card is roughly 400px (380px min-width + gap)
          // We limit the max columns to 4 to prevent it from becoming too wide on huge screens
          const columnsNeeded = Math.min(projectLists.length, 4);

          // Calculate flex-basis: roughly columns * 400px
          // We use a percentage calculation for better responsiveness
          // 1 col ~ 25%, 2 cols ~ 50%, etc., but with some flexibility
          // Using a pixel basis is safer for the masonry-like wrap effect
          const flexBasis = `${columnsNeeded * 400}px`;

          // If it has many lists, let it grow to fill the row.
          // If it has few, it stays compact.
          const flexGrow = projectLists.length > 3 ? 1 : 0;

          return (
            <div
              key={project.id}
              className={styles.projectSection}
              style={{
                flexBasis: flexBasis,
                flexGrow: flexGrow,
                maxWidth: "100%", // Ensure it doesn't overflow container
              }}
            >
              <div className={styles.projectHeader}>
                <h2 className={styles.projectName}>{project.name}</h2>
                <span className={styles.projectCount}>
                  {projectLists.length} list
                  {projectLists.length !== 1 ? "s" : ""}
                </span>
              </div>

              <div className={styles.listsGrid}>
                {projectLists.map((list) => {
                  const stats = getListStats(list.id);

                  return (
                    <div key={list.id} className={styles.listCard}>
                      <div
                        className={styles.listHeader}
                        onClick={() => onTaskListClick(list.id, project.id)}
                      >
                        <div className={styles.listTitleRow}>
                          <List size={18} className={styles.listIcon} />
                          <h3 className={styles.listName}>{list.name}</h3>
                        </div>

                        <div className={styles.listMetrics}>
                          <div className={styles.metricItem}>
                            <CheckCircle2
                              size={14}
                              className={styles.metricIcon}
                              style={{ color: "var(--success)" }}
                            />
                            <span className={styles.metricValue}>
                              {stats.completed}
                            </span>
                            <span className={styles.metricLabel}>Done</span>
                          </div>
                          <div className={styles.metricItem}>
                            <Clock
                              size={14}
                              className={styles.metricIcon}
                              style={{ color: "var(--warning)" }}
                            />
                            <span className={styles.metricValue}>
                              {stats.inProgress}
                            </span>
                            <span className={styles.metricLabel}>Active</span>
                          </div>
                          <div className={styles.metricItem}>
                            <AlertCircle
                              size={14}
                              className={styles.metricIcon}
                              style={{ color: "var(--error)" }}
                            />
                            <span className={styles.metricValue}>
                              {stats.blocked}
                            </span>
                            <span className={styles.metricLabel}>Blocked</span>
                          </div>
                          <div className={styles.metricItem}>
                            <Circle
                              size={14}
                              className={styles.metricIcon}
                              style={{ color: "var(--text-tertiary)" }}
                            />
                            <span className={styles.metricValue}>
                              {stats.notStarted}
                            </span>
                            <span className={styles.metricLabel}>Todo</span>
                          </div>
                        </div>

                        <div className={styles.progressSection}>
                          <div className={styles.progressBar}>
                            <div
                              className={styles.progressFill}
                              style={{ width: `${stats.completionRate}%` }}
                            />
                          </div>
                          <span className={styles.progressText}>
                            {Math.round(stats.completionRate)}% Complete
                          </span>
                        </div>
                      </div>

                      <div className={styles.tasksContainer}>
                        {stats.tasks.length > 0 ? (
                          stats.tasks
                            .slice(0, 5)
                            .map((task) => (
                              <SmallTaskCard
                                key={task.id}
                                task={task}
                                onClick={() => onTaskClick(task)}
                              />
                            ))
                        ) : (
                          <div className={styles.emptyList}>
                            <Circle size={32} className={styles.emptyIcon} />
                            <span>No tasks yet</span>
                          </div>
                        )}
                        {stats.tasks.length > 5 && (
                          <div
                            className={styles.viewMore}
                            onClick={() => onTaskListClick(list.id, project.id)}
                          >
                            View {stats.tasks.length - 5} more task
                            {stats.tasks.length - 5 !== 1 ? "s" : ""}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
