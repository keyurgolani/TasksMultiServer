import React, { useState, useRef } from "react";
import { List, Circle } from "lucide-react";
import { SmallTaskCard } from "./SmallTaskCard";
import type { Project, TaskList, Task } from "../api/client";
import { StatsPanel } from "./StatsPanel";
import { SearchFilterToolbar } from "./SearchFilterToolbar";
import { TaskListFilterPopover } from "./TaskListFilterPopover";
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
  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const [filters, setFilters] = useState({
    status: [] as string[],
    priority: [] as string[],
    taskCount: 'all',
    completion: 'all',
  });

  const handleFilterChange = (type: "status" | "priority" | "taskCount" | "completion", value: string) => {
    if (type === 'status' || type === 'priority') {
      setFilters((prev) => {
        const current = prev[type];
        const updated = current.includes(value)
          ? current.filter((item) => item !== value)
          : [...current, value];
        return { ...prev, [type]: updated };
      });
    } else {
      setFilters((prev) => ({ ...prev, [type]: value }));
    }
  };

  const clearFilters = () => {
    setFilters({ status: [], priority: [], taskCount: 'all', completion: 'all' });
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
      <SearchFilterToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onClearSearch={() => setSearchQuery('')}
        isFilterOpen={isFilterOpen}
        setIsFilterOpen={setIsFilterOpen}
        isFilterActive={filters.status.length > 0 || filters.priority.length > 0 || filters.taskCount !== 'all' || filters.completion !== 'all'}
        filterButtonRef={filterButtonRef as React.RefObject<HTMLButtonElement>}
        placeholder="Search task lists or tasks..."
      >
        <TaskListFilterPopover
          isOpen={isFilterOpen}
          onClose={() => setIsFilterOpen(false)}
          filters={filters}
          onFilterChange={handleFilterChange}
          onClear={clearFilters}
          buttonRef={filterButtonRef}
        />
      </SearchFilterToolbar>

      <div className={styles.content}>
        {filteredProjects
          .sort((a, b) => {
            // Sort projects by task list count (descending)
            const aListCount = taskLists.filter(l => l.project_id === a.id).length;
            const bListCount = taskLists.filter(l => l.project_id === b.id).length;
            return bListCount - aListCount;
          })
          .map((project) => {
          const projectLists = taskLists
            .filter((list) => list.project_id === project.id)
            .sort((a, b) => {
              // Sort task lists by task count (descending)
              const aTaskCount = tasks.filter(t => t.task_list_id === a.id).length;
              const bTaskCount = tasks.filter(t => t.task_list_id === b.id).length;
              return bTaskCount - aTaskCount;
            })
            .filter((list) => {
              // Apply task count filter
              const stats = getListStats(list.id);
              const taskCount = stats.total;
              
              if (filters.taskCount !== 'all') {
                if (filters.taskCount === 'empty' && taskCount > 0) return false;
                if (filters.taskCount === 'few' && (taskCount < 1 || taskCount > 5)) return false;
                if (filters.taskCount === 'medium' && (taskCount < 6 || taskCount > 10)) return false;
                if (filters.taskCount === 'many' && taskCount < 11) return false;
              }
              
              // Apply completion filter
              if (filters.completion !== 'all') {
                const completionRate = stats.completionRate;
                if (filters.completion === 'low' && (completionRate > 25)) return false;
                if (filters.completion === 'medium' && (completionRate < 26 || completionRate > 75)) return false;
                if (filters.completion === 'high' && completionRate < 76) return false;
              }
              
              return true;
            });
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
                          <StatsPanel 
                            stats={{
                              completed: stats.completed,
                              inProgress: stats.inProgress,
                              blocked: stats.blocked,
                              notStarted: stats.notStarted,
                              total: stats.total
                            }}
                          />
                        </div>
                      </div>


                      <div className={styles.tasksSection}>
                        <div className={styles.tasksSectionHeader}>
                          <h4 className={styles.tasksSectionTitle}>
                            Tasks ({stats.total})
                          </h4>
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
