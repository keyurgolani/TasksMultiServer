import React, { useState, useRef } from 'react';
import type { Project, TaskList, ProjectStats, Task } from '../api/client';
import { Folder, List, Search, Filter } from 'lucide-react';
import { Input, Button, Badge } from './ui';
import { ProjectFilterPopover } from './ProjectFilterPopover';
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
      <div className={styles.toolbar}>
        <div className={styles.searchContainer}>
          <Input
            icon={<Search size={16} />}
            placeholder="Search projects or lists..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
          />
        </div>
        <div style={{ position: 'relative' }}>
          <Button 
            ref={filterButtonRef}
            variant={filters.completion !== 'all' || filters.taskCount !== 'all' || filters.isDefault !== 'all' ? "primary" : "secondary"} 
            icon={<Filter size={16} />}
            onClick={() => setIsFilterOpen(!isFilterOpen)}
          >
            Filter
          </Button>
          <ProjectFilterPopover
            isOpen={isFilterOpen}
            onClose={() => setIsFilterOpen(false)}
            filters={filters}
            onFilterChange={handleFilterChange}
            onClear={clearFilters}
            buttonRef={filterButtonRef}
          />
        </div>
      </div>
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
          
          const completionPercentage = totalTasks > 0 
            ? Math.round((completed / totalTasks) * 100) 
            : 0;

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

              <div className={styles.statsGrid}>
                <div className={styles.statItem}>
                  <span className={styles.statValue} style={{ color: 'var(--success)' }}>{completed}</span>
                  <span className={styles.statLabel}>Done</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statValue} style={{ color: 'var(--warning)' }}>{inProgress}</span>
                  <span className={styles.statLabel}>Active</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statValue} style={{ color: 'var(--error)' }}>{blocked}</span>
                  <span className={styles.statLabel}>Blocked</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statValue} style={{ color: 'var(--text-tertiary)' }}>{notStarted}</span>
                  <span className={styles.statLabel}>Ready</span>
                </div>
              </div>

              <div className={styles.breakdownSection}>
                <div className={styles.breakdownHeader}>
                  <span>Progress</span>
                  <span>{completionPercentage}%</span>
                </div>
                <div className={styles.breakdownBar}>
                  <div className={styles.breakdownSegment} style={{ width: `${(completed/totalTasks)*100}%`, backgroundColor: 'var(--success)' }} />
                  <div className={styles.breakdownSegment} style={{ width: `${(inProgress/totalTasks)*100}%`, backgroundColor: 'var(--warning)' }} />
                  <div className={styles.breakdownSegment} style={{ width: `${(blocked/totalTasks)*100}%`, backgroundColor: 'var(--error)' }} />
                  <div className={styles.breakdownSegment} style={{ width: `${(notStarted/totalTasks)*100}%`, backgroundColor: 'var(--bg-surface-active)' }} />
                </div>
              </div>

              <div className={styles.listsSection}>
                <h3 className={styles.listsTitle}>Task Lists ({projectLists.length})</h3>
                <div className={styles.listsGrid}>
                  {projectLists.slice(0, 6).map(list => (
                    <div 
                      key={list.id} 
                      className={styles.listItem}
                      onClick={(e) => {
                        e.stopPropagation();
                        onTaskListClick(list.id, project.id);
                      }}
                    >
                      <List size={12} className={styles.listIcon} />
                      <span className={styles.listName}>{list.name}</span>
                    </div>
                  ))}
                  {projectLists.length > 6 && (
                    <div className={styles.listItem} style={{ color: 'var(--primary)' }}>
                      +{projectLists.length - 6} more
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
};
