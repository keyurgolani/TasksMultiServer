import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type {
  Project,
  TaskList,
  Task,
  ProjectStats,
  TaskListStats,
} from "../api/client";
import { CreateTaskListModal } from "../components/CreateTaskListModal";
import { CreateTaskModal } from "../components/CreateTaskModal";
import { CreateProjectModal } from "../components/CreateProjectModal";
import { Fab } from '../components/Fab';
import { Customizations } from '../components/Customizations';
import { ViewSelector, type DashboardView } from '../components/ViewSelector';
import { TasksView } from '../components/TasksView';
import { TaskListView } from '../components/TaskListView';
import { ProjectView } from '../components/ProjectView';
import { TaskDetailModal } from '../components/TaskDetailModal';
import { useToast } from '../context/ToastContext';
import { Spinner } from '../components/ui/Spinner';
import styles from "./Dashboard.module.css";

export const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [allTaskLists, setAllTaskLists] = useState<TaskList[]>([]);
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [selectedTaskList, setSelectedTaskList] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showTaskListModal, setShowTaskListModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [currentView, setCurrentView] = useState<DashboardView>('projects'); // Default to projects
  const [projectStats, setProjectStats] = useState<
    Record<string, ProjectStats>
  >({});
  const [taskListStats, setTaskListStats] = useState<
    Record<string, TaskListStats>
  >({});
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [tasksLoading, setTasksLoading] = useState(false);
  const toast = useToast();

  // Navigation handlers
  const handleProjectClick = (projectId: string) => {
    setSelectedProject(projectId);
    setCurrentView('tasks');
  };

  const handleTaskListClick = (taskListId: string, projectId: string) => {
    setSelectedProject(projectId);
    setSelectedTaskList(taskListId);
    setCurrentView('tasks');
  };

  // Task modal handlers
  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
    setIsTaskModalOpen(true);
  };

  const handleTaskModalClose = () => {
    setIsTaskModalOpen(false);
    setSelectedTask(null);
  };

  const handleTaskSave = async (updatedTask: Task) => {
    try {
      await api.updateTask(updatedTask.id, updatedTask);
      
      // Update local state
      setTasks(prev => prev.map(t => t.id === updatedTask.id ? updatedTask : t));
      setAllTasks(prev => prev.map(t => t.id === updatedTask.id ? updatedTask : t));
      
      // Refresh stats if needed (optional, or just reload all data)
      if (selectedProject) {
        loadTaskLists(selectedProject); // Reload lists to update stats
      }
      
      setSelectedTask(updatedTask);
      toast.success("Task updated successfully");
    } catch (error) {
      console.error("Failed to update task:", error);
      toast.error("Failed to update task");
    }
  };

  useEffect(() => {
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadTaskLists(selectedProject);
      setTasks([]); // Clear tasks when project changes
      // Don't clear selectedTaskList here, let loadTaskLists handle validation
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedTaskList) {
      loadTasks(selectedTaskList);
    } else {
      setTasks([]); // Clear tasks when no task list is selected
    }
  }, [selectedTaskList]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setAllProjects(data); // Populate allProjects
      setProjects(data);

      // Load stats for all projects
      const stats: Record<string, ProjectStats> = {};
      await Promise.all(
        data.map(async (project) => {
          stats[project.id] = await api.getProjectStats(project.id);
        })
      );
      setProjectStats(stats);

      if (data.length > 0 && !selectedProject) {
        setSelectedProject(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTaskLists = async (projectId: string) => {
    try {
      setTasksLoading(true);
      const data = await api.getTaskLists(projectId);
      setTaskLists(data);

      // Load stats for all task lists
      const stats: Record<string, TaskListStats> = {};
      await Promise.all(
        data.map(async (taskList) => {
          stats[taskList.id] = await api.getTaskListStats(taskList.id);
        })
      );
      setTaskListStats(stats);

      // Only set default if no list selected or selected list not in project
      if (data.length > 0) {
        const currentListInProject = selectedTaskList && data.some(l => l.id === selectedTaskList);
        if (!currentListInProject) {
          setSelectedTaskList(data[0].id);
        }
      } else {
        setSelectedTaskList(null);
      }
    } catch (error) {
      console.error("Failed to load task lists:", error);
    } finally {
      setTasksLoading(false);
    }
  };

  const loadTasks = async (taskListId: string) => {
    try {
      setTasksLoading(true);
      const data = await api.getTasks(taskListId);
      setTasks(data);
    } catch (error) {
      console.error("Failed to load tasks:", error);
    } finally {
      setTasksLoading(false);
    }
  };

  // Load all task lists and tasks for the multi-view
  useEffect(() => {
    const loadAllData = async () => {
      if (allProjects.length > 0) {
        try {
          // Load all task lists
          const allListsData = await Promise.all(
            allProjects.map(project => api.getTaskLists(project.id))
          );
          setAllTaskLists(allListsData.flat());

          // Load all tasks
          const allTasksData = await Promise.all(
            allListsData.flat().map(list => api.getTasks(list.id))
          );
          setAllTasks(allTasksData.flat());
        } catch (error) {
          console.error("Failed to load all data:", error);
        }
      }
    };
    loadAllData();
  }, [allProjects]);

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <div 
              className={styles.logo} 
              onClick={() => {
                setCurrentView('projects');
                setSelectedProject(null);
                setSelectedTaskList(null);
              }}
            >
              <div className={styles.logoIcon}>T</div>
              <span className={styles.logoText}>TaskFlow</span>
            </div>
          </div>
          
          <div className={styles.headerCenter}>
            <ViewSelector 
              currentView={currentView} 
              onViewChange={setCurrentView} 
            />
          </div>
          <div className={styles.headerControls}>
            <Customizations />
          </div>
        </div>
      </header>

      {currentView === 'tasks' && (
        <div className={styles.main}>
          <TasksView
            projects={projects}
            taskLists={taskLists}
            tasks={tasks}
            projectStats={projectStats}
            taskListStats={taskListStats}
            selectedProject={selectedProject}
            selectedTaskList={selectedTaskList}
            searchQuery={searchQuery}
            onSelectProject={setSelectedProject}
            onSelectTaskList={setSelectedTaskList}
            onSearchChange={setSearchQuery}
            onTaskClick={handleTaskClick}
            loading={tasksLoading}
          />
        </div>
      )}

      {currentView === 'taskLists' && (
        <div className={styles.main}>
          <TaskListView 
            projects={allProjects}
            taskLists={allTaskLists}
            tasks={allTasks}
            onTaskClick={handleTaskClick}
            onTaskListClick={handleTaskListClick}
          />
        </div>
      )}

      {currentView === 'projects' && (
        <div className={styles.main}>
          <ProjectView 
            projects={projects}
            taskLists={allTaskLists}
            tasks={allTasks}
            projectStats={projectStats}
            onProjectClick={handleProjectClick}
            onTaskListClick={handleTaskListClick}
          />
        </div>
      )}



      {/* Task Detail Modal */}
      <TaskDetailModal 
        task={selectedTask}
        isOpen={isTaskModalOpen}
        onClose={handleTaskModalClose}
        onSave={handleTaskSave}
        availableTasks={allTasks}
      />

      {showTaskListModal && (
        <CreateTaskListModal
          onClose={() => setShowTaskListModal(false)}
          onSuccess={() => {
            loadProjects();
            if (selectedProject) {
              loadTaskLists(selectedProject);
            }
          }}
        />
      )}

      {showTaskModal && selectedTaskList && (
        <CreateTaskModal
          taskListId={selectedTaskList}
          isOpen={showTaskModal}
          onClose={() => setShowTaskModal(false)}
          onSuccess={() => {
            if (selectedTaskList) {
              loadTasks(selectedTaskList);
            }
          }}
          availableTasks={allTasks}
        />
      )}

      {showProjectModal && (
        <CreateProjectModal
          onClose={() => setShowProjectModal(false)}
          onSuccess={() => {
            loadProjects();
            // We don't have the new project ID here easily with the current callback signature
            // Ideally onSuccess should pass the created project, but for now we just reload
            setShowProjectModal(false);
          }}
        />
      )}

      {/* FAB visible on all views, but task button only on Tasks view */}
      <Fab 
        onAddProject={() => setShowProjectModal(true)}
        onAddTaskList={() => setShowTaskListModal(true)}
        onAddTask={() => setShowTaskModal(true)}
        showTaskButton={currentView === 'tasks'}
      />
    </div>
  );
};
