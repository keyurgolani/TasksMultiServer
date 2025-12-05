import React, { useState, useRef } from 'react';
import { Card, Input, Skeleton } from "../components/ui";
import { StatusIndicator } from './StatusIndicator';
import { ReadyTasksCount } from './ReadyTasksCount';
import { Search } from "lucide-react";
import { SearchFilterToolbar } from './SearchFilterToolbar';
import { FilterPopover } from './FilterPopover';
import type {
  Project,
  TaskList,
  Task,
  ProjectStats,
  TaskListStats,
} from "../api/client";
import styles from "./TasksView.module.css";

interface TasksViewProps {
  projects: Project[];
  taskLists: TaskList[];
  tasks: Task[];
  projectStats: Record<string, ProjectStats>;
  taskListStats: Record<string, TaskListStats>;
  selectedProject: string | null;
  selectedTaskList: string | null;
  searchQuery: string;
  onSelectProject: (id: string) => void;
  onSelectTaskList: (id: string) => void;
  onSearchChange: (query: string) => void;
  onTaskClick: (task: Task) => void;
  loading?: boolean;
}

export const TasksView: React.FC<TasksViewProps> = ({
  projects,
  taskLists,
  tasks,
  projectStats,
  taskListStats,
  selectedProject,
  selectedTaskList,
  searchQuery,
  onSelectProject,
  onSelectTaskList,
  onSearchChange,
  onTaskClick,
  loading = false,
}) => {
  const [projectFilter, setProjectFilter] = useState('');
  const [listFilter, setListFilter] = useState('');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const [filters, setFilters] = useState({
    status: [] as string[],
    priority: [] as string[],
  });

  const handleFilterChange = (type: 'status' | 'priority' | 'hasExitCriteria' | 'hasDependencies', value: string) => {
    if (type === 'status' || type === 'priority') {
      setFilters(prev => {
        const current = prev[type];
        const updated = current.includes(value)
          ? current.filter(item => item !== value)
          : [...current, value];
        return { ...prev, [type]: updated };
      });
    }
    // hasExitCriteria and hasDependencies are not used in TasksView, so we ignore them
  };

  const clearFilters = () => {
    setFilters({ status: [], priority: [] });
  };

  // Filter projects
  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(projectFilter.toLowerCase())
  );

  // Filter task lists
  const filteredTaskLists = taskLists.filter(l => 
    l.name.toLowerCase().includes(listFilter.toLowerCase()) &&
    (selectedProject ? l.project_id === selectedProject : true)
  );

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "CRITICAL": return "#FF4757";
      case "HIGH": return "#FF6348";
      case "MEDIUM": return "#FFA502";
      case "LOW": return "#26DE81";
      default: return "#A4B0BE";
    }
  };



  // Filter tasks based on search, project, list, and filters
  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesProject = selectedProject
      ? taskLists.find((l) => l.id === task.task_list_id)?.project_id ===
        selectedProject
      : true;
    const matchesList = selectedTaskList
      ? task.task_list_id === selectedTaskList
      : true;
    
    const statusMatch = filters.status.length === 0 || filters.status.includes(task.status);
    const priorityMatch = filters.priority.length === 0 || filters.priority.includes(task.priority);

    return matchesSearch && matchesProject && matchesList && statusMatch && priorityMatch;
  });

  const readyTasks = filteredTasks.filter((t) => t.status === "NOT_STARTED");
  // otherTasks removed as it was unused
  // If I put Ready in sidebar, duplicating them in Main might be redundant. But "All Tasks" implies all.
  // However, often "Ready" means "ToDo". If I move them to sidebar, I probably shouldn't show them in main to avoid clutter.
  // Let's assume Main shows "Active/In Progress/Blocked/Completed" if Ready is separated.
  // BUT the user said "All Tasks section".
  // Let's keep it as "All Tasks" (including Ready) in main for now, but maybe the user wants them separated.
  // "Ready tasks should be put on the left side... And the all tasks section should stay in main section."
  // I'll assume separation is better.

  const mainTasks = filteredTasks; // Keeping all for now as requested "All Tasks".

  return (
    <div className={styles.content}>
      {/* Top Section: Projects and Task Lists */}
      <div className={styles.topSection}>
        {/* Projects Section */}
        <div className={styles.sectionContainer}>
          <div className={styles.headerColumn}>
            <div className={styles.sectionHeader}>
              <h3>Projects</h3>
            </div>
            <Input 
              placeholder="Filter..." 
              className={styles.miniInput}
              icon={<Search size={12} />}
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              onClear={() => setProjectFilter('')}
            />
          </div>
          <div className={styles.cardsColumn}>
            {filteredProjects.map((project) => {
              const stats = projectStats[project.id];
              const listText =
                stats?.task_list_count === 1 ? "list" : "lists";
              const completionPercentage =
                stats && stats.total_tasks > 0
                  ? Math.round(
                      (stats.completed_tasks / stats.total_tasks) * 100
                    )
                  : 0;

              return (
                <button
                  key={project.id}
                  className={`${styles.projectCard} ${
                    selectedProject === project.id ? styles.active : ""
                  }`}
                  onClick={() => onSelectProject(project.id)}
                >
                  <div className={styles.projectName}>{project.name}</div>
                  
                  {stats && (
                    <>
                      <div className={styles.projectStats}>
                        <span className={styles.statItem}>
                          <ReadyTasksCount count={stats.ready_tasks} variant="default" />
                        </span>
                        <span className={styles.statItem}>
                          <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{stats.task_list_count}</span> {listText}
                        </span>
                      </div>
                      
                      <div className={styles.projectProgress}>
                        <div className={styles.progressBar}>
                          <div
                            className={styles.progressFill}
                            style={{ width: `${completionPercentage}%` }}
                          />
                        </div>
                        <span className={styles.progressText}>{completionPercentage}%</span>
                      </div>
                    </>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Task Lists Section */}
        <div className={styles.sectionContainer}>
          <div className={styles.headerColumn}>
            <div className={styles.sectionHeader}>
              <h3>Task Lists</h3>
            </div>
            <Input 
              placeholder="Filter..." 
              className={styles.miniInput}
              icon={<Search size={12} />}
              value={listFilter}
              onChange={(e) => setListFilter(e.target.value)}
              onClear={() => setListFilter('')}
            />
          </div>
          <div className={styles.cardsColumn}>
            {filteredTaskLists.map((taskList) => {
              const stats = taskListStats[taskList.id];
              const completionPercentage = stats && stats.task_count > 0
                ? Math.round((stats.completed_tasks / stats.task_count) * 100)
                : 0;
              
              return (
                <button
                  key={taskList.id}
                  className={`${styles.taskListCard} ${
                    selectedTaskList === taskList.id ? styles.active : ""
                  }`}
                  onClick={() => onSelectTaskList(taskList.id)}
                >
                  <span className={styles.itemName}>{taskList.name}</span>
                  {stats && (
                    <div className={styles.taskListMetaRow}>
                      <ReadyTasksCount count={stats.ready_tasks} variant="default" />
                      <div className={styles.taskListProgress}>
                        <div className={styles.taskListProgressBar}>
                          <div
                            className={styles.progressFill}
                            style={{ width: `${completionPercentage}%` }}
                          />
                        </div>
                        <span className={styles.taskListDoneText}>{stats.completed_tasks}/{stats.task_count} done</span>
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className={styles.bottomSection}>
        <aside className={styles.sidebar}>
          {/* Ready Tasks (Sidebar) */}
          <div className={styles.sidebarSection}>
            <div className={styles.sectionHeader}>
              <h3>Ready Tasks ({readyTasks.length})</h3>
            </div>
            <div className={styles.readyTasksList}>
              {readyTasks.map((task) => (
                <div 
                  key={task.id} 
                  className={styles.readyTaskItem}
                  onClick={() => onTaskClick(task)}
                >
                  <div className={styles.readyTaskHeader}>
                    <h4>{task.title}</h4>
                    <div className={styles.priorityBadge} style={{ backgroundColor: getPriorityColor(task.priority) }}>
                      {task.priority}
                    </div>
                  </div>
                  <p className={styles.readyTaskDesc}>{task.description}</p>
                </div>
              ))}
              {readyTasks.length === 0 && (
                <div className={styles.emptyStateSmall}>
                  No ready tasks
                </div>
              )}
            </div>
          </div>
        </aside>

      <main className={styles.main}>
        {/* All Tasks Header & Toolbar */}
        <div className={styles.mainHeader}>
          <h2 className={styles.sectionTitle}>All Tasks</h2>
          
          <SearchFilterToolbar
            className={styles.toolbarOverride}
            searchQuery={searchQuery}
            onSearchChange={onSearchChange}
            onClearSearch={() => onSearchChange('')}
            isFilterOpen={isFilterOpen}
            setIsFilterOpen={setIsFilterOpen}
            isFilterActive={filters.status.length > 0 || filters.priority.length > 0}
            onReset={clearFilters}
            filterButtonRef={filterButtonRef as React.RefObject<HTMLButtonElement>}
            placeholder="Search tasks..."
          >
            <FilterPopover
              isOpen={isFilterOpen}
              onClose={() => setIsFilterOpen(false)}
              filters={filters}
              onFilterChange={handleFilterChange}
              onClear={clearFilters}
              buttonRef={filterButtonRef}
            />
          </SearchFilterToolbar>
        </div>
        <div className={styles.taskGrid}>
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} style={{ height: '200px' }}>
                <div style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <Skeleton width="60%" height="24px" />
                    <Skeleton variant="circle" width="12px" height="12px" />
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <Skeleton width="100%" height="16px" />
                    <Skeleton width="80%" height="16px" style={{ marginTop: '8px' }} />
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <Skeleton width="40px" height="20px" />
                    <Skeleton width="40px" height="20px" />
                  </div>
                </div>
              </Card>
            ))
          ) : (
            mainTasks.map((task) => {
            const getStatusBackground = (status: string) => {
              switch (status) {
                case 'IN_PROGRESS':
                  return 'radial-gradient(circle at top right, color-mix(in srgb, var(--warning) 15%, transparent) 0%, transparent 60%)';
                case 'COMPLETED':
                  return 'radial-gradient(circle at top right, color-mix(in srgb, var(--success) 15%, transparent) 0%, transparent 60%)';
                case 'BLOCKED':
                  return 'radial-gradient(circle at top right, color-mix(in srgb, var(--error) 15%, transparent) 0%, transparent 60%)';
                case 'NOT_STARTED':
                  return 'radial-gradient(circle at top right, color-mix(in srgb, var(--text-primary) 5%, transparent) 0%, transparent 60%)';
                default:
                  return undefined;
              }
            };

            return (
              <Card 
                key={task.id} 
                interactive 
                onClick={() => onTaskClick(task)}
                style={{ 
                  background: getStatusBackground(task.status),
                }}
              >
                <div className={styles.taskCard}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <h3 className={styles.taskTitle}>{task.title}</h3>
                    <StatusIndicator status={task.status} variant="dot" />
                  </div>

                  <div className={styles.taskMetaRow}>
                  {task.action_plan && task.action_plan.length > 0 && (
                    <span
                      className={styles.metaCount}
                      title="Action Plan Items"
                    >
                      ⚡ {task.action_plan.length}
                    </span>
                  )}
                  {task.notes && task.notes.length > 0 && (
                    <span className={styles.metaCount} title="Notes">
                      📝 {task.notes.length}
                    </span>
                  )}

                  <div className={styles.priorityBadge} style={{ backgroundColor: getPriorityColor(task.priority), fontSize: '10px', padding: '2px 6px', borderRadius: '4px', color: 'white', fontWeight: 'bold' }}>
                    {task.priority}
                  </div>
                  {task.exit_criteria && task.exit_criteria.length > 0 && (
                    <div className={styles.metaProgressContainer} title="Exit Criteria">
                      <div className={styles.metaProgressBar}>
                        <div
                          className={styles.metaProgressFill}
                          style={{
                            width: `${Math.round(
                              (task.exit_criteria.filter(
                                (ec) => ec.status === "COMPLETE"
                              ).length /
                                task.exit_criteria.length) *
                                100
                            )}%`,
                          }}
                        />
                      </div>
                      <span className={styles.metaProgressText}>
                        {task.exit_criteria.filter((ec) => ec.status === "COMPLETE").length}/{task.exit_criteria.length}
                      </span>
                    </div>
                  )}
                </div>

                <p className={styles.taskDescription}>{task.description}</p>


                {task.tags.length > 0 && (
                  <div className={styles.taskTags}>
                    {task.tags.map((tag, idx) => (
                      <span key={idx} className={styles.tag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          );
        })
        )}
        </div>

        {!loading && filteredTasks.length === 0 && (
          <div className={styles.emptyState}>
            <p>No tasks found</p>
          </div>
        )}
      </main>
      </div>
    </div>
  );
};
