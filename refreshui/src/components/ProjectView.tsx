import React, { useState, useRef } from 'react';
import type { Project, TaskList, ProjectStats, Task } from '../api/client';
import { Folder, List } from 'lucide-react';
import { Badge } from './ui';
import { ProjectFilterPopover } from './ProjectFilterPopover';
import { StatsPanel } from './StatsPanel';
import { SearchFilterToolbar } from './SearchFilterToolbar';
import styles from './ProjectView.module.css';

interface ProjectViewProps {
  projects: Project[];
  taskLists: TaskList[];
  tasks: Task[];
  projectStats: Record<string, ProjectStats>;
  onProjectClick: (projectId: string) => void;
  onTaskListClick: (taskListId: string, projectId: string) => void;
}

export const ProjectView: React.FC<ProjectViewProps> = ({ 
  projects, 
  taskLists, 
  tasks,
  // projectStats removed
  onProjectClick,
  onTaskListClick,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const [filters, setFilters] = useState({
    completion: 'all',
    taskCount: 'all',
    isDefault: 'all',
  });

  const handleFilterChange = (type: 'completion' | 'taskCount' | 'isDefault', value: string) => {
    setFilters(prev => ({ ...prev, [type]: value }));
  };

  const clearFilters = () => {
    setFilters({ completion: 'all', taskCount: 'all', isDefault: 'all' });
  };

  // Filter projects by search query and project filters
  const filteredProjects = projects.filter(project => {
    // Search filter
    const projectMatches = project.name.toLowerCase().includes(searchQuery.toLowerCase());
    const hasMatchingLists = taskLists.some(list => 
      list.project_id === project.id && 
      list.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    if (!projectMatches && !hasMatchingLists && searchQuery) {
      return false;
    }

    // Calculate project stats for filtering
    const projectTasks = tasks.filter(task => {
      const taskList = taskLists.find(list => list.id === task.task_list_id);
      return taskList?.project_id === project.id;
    });

    const totalTasks = projectTasks.length;
    const completed = projectTasks.filter(t => t.status === 'COMPLETED').length;
    const completionPercentage = totalTasks > 0 ? (completed / totalTasks) * 100 : 0;

    // Completion filter
    if (filters.completion !== 'all') {
      if (filters.completion === 'low' && (completionPercentage > 33 || totalTasks === 0)) return false;
      if (filters.completion === 'medium' && (completionPercentage < 34 || completionPercentage > 66)) return false;
      if (filters.completion === 'high' && completionPercentage < 67) return false;
    }

    // Task count filter
    if (filters.taskCount !== 'all') {
      if (filters.taskCount === 'empty' && totalTasks > 0) return false;
      if (filters.taskCount === 'hasTasks' && totalTasks === 0) return false;
    }

    // Default filter
    if (filters.isDefault !== 'all') {
      if (filters.isDefault === 'default' && !project.is_default) return false;
      if (filters.isDefault === 'nonDefault' && project.is_default) return false;
    }

    return true;
  });

  return (
    <div className={styles.container}>
      <SearchFilterToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onClearSearch={() => setSearchQuery('')}
        isFilterOpen={isFilterOpen}
        setIsFilterOpen={setIsFilterOpen}
        isFilterActive={filters.completion !== 'all' || filters.taskCount !== 'all' || filters.isDefault !== 'all'}
        filterButtonRef={filterButtonRef as React.RefObject<HTMLButtonElement>}
        placeholder="Search projects or lists..."
      >
        <ProjectFilterPopover
          isOpen={isFilterOpen}
          onClose={() => setIsFilterOpen(false)}
          filters={filters}
          onFilterChange={handleFilterChange}
          onClear={clearFilters}
          buttonRef={filterButtonRef}
        />
      </SearchFilterToolbar>
      <div className={styles.grid}>
        {filteredProjects.map(project => {
          // Calculate detailed stats from tasks prop
          const projectLists = taskLists.filter(list => list.project_id === project.id);
          const projectTasks = tasks.filter(task => {
            const list = taskLists.find(l => l.id === task.task_list_id);
            return list?.project_id === project.id;
          });

          const totalTasks = projectTasks.length;
          const completed = projectTasks.filter(t => t.status === 'COMPLETED').length;
          const inProgress = projectTasks.filter(t => t.status === 'IN_PROGRESS').length;
          const blocked = projectTasks.filter(t => t.status === 'BLOCKED').length;
          const notStarted = projectTasks.filter(t => t.status === 'NOT_STARTED').length;

          // completionPercentage was calculated but not used in the return block, so it's removed.

          return (
            <div
              key={project.id}
              className={styles.projectCard}
              onClick={() => onProjectClick(project.id)}
              style={{ cursor: 'pointer' }}
            >
              <div className={styles.header}>
                <div className={styles.iconWrapper}>
                  <Folder size={24} />
                </div>
                <div className={styles.headerInfo}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h2 className={styles.title}>{project.name}</h2>
                    {project.is_default && (
                      <Badge variant="info">Default</Badge>
                    )}
                  </div>
                  <span className={styles.meta}>Created {new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className={styles.statsSection}>
                <StatsPanel 
                  stats={{
                    completed,
                    inProgress,
                    blocked,
                    notStarted,
                    total: totalTasks
                  }}
                />
              </div>

              <div className={styles.listsSection}>
                <h3 className={styles.listsTitle}>Task Lists ({projectLists.length})</h3>
                <div className={styles.listsStack}>
                  {projectLists.map(list => {
                    // Calculate list stats for preview
                    const listTasks = tasks.filter(t => t.task_list_id === list.id);
                    const listCompleted = listTasks.filter(t => t.status === 'COMPLETED').length;
                    const listTotal = listTasks.length;
                    
                    return (
                      <div 
                        key={list.id} 
                        className={styles.listItem}
                        onClick={(e) => {
                          e.stopPropagation();
                          onTaskListClick(list.id, project.id);
                        }}
                      >
                        <div className={styles.listInfo}>
                          <List size={14} className={styles.listIcon} />
                          <span className={styles.listName}>{list.name}</span>
                        </div>
                        <div className={styles.listMeta}>
                          <span className={styles.listCount}>
                            {listCompleted}/{listTotal} done
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
