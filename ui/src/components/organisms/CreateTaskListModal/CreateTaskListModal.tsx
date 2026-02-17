import React, { useState, useCallback, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, FolderOpen, Plus } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Input } from "../../atoms/Input";
import { Typography } from "../../atoms/Typography";
import { useDataService } from "../../../context/DataServiceContext";
import { cn } from "../../../lib/utils";
import type { Project } from "../../../services/types";
import styles from "./CreateTaskListModal.module.css";

/**
 * CreateTaskListModal Organism Component
 *
 * A modal dialog for creating new task lists with form validation.
 * Implements glassmorphism effect and follows design system patterns.
 *
 * Requirements: 17.1, 17.2, 17.6
 * - 17.1: Display a modal overlay with a form for task list details
 * - 17.2: Validate that the task list name is not empty
 * - 17.3: Allow project selection for task list association
 * - 17.6: Apply consistent styling with other modal components (glassmorphism,
 *         centered viewport positioning, same spacing tokens, matching animations)
 *
 * Property 37: CreateTaskListModal Form Validation
 * - For any CreateTaskListModal submission, the form SHALL validate
 *   that the task list name is not empty and a project is selected.
 */

export interface CreateTaskListModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback fired when the modal should close */
  onClose: () => void;
  /** Callback fired when a task list is successfully created */
  onSuccess: () => void;
  /** Optional pre-selected project ID */
  defaultProjectId?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * CreateTaskListModal component for creating new task lists
 */
export const CreateTaskListModal: React.FC<CreateTaskListModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  defaultProjectId,
  className,
}) => {
  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState(defaultProjectId || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projectError, setProjectError] = useState("");
  
  // Projects state for searchable selector - Requirements: 9.13
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [projectSearchQuery, setProjectSearchQuery] = useState("");
  
  // State for creating a new project inline
  const [newProjectName, setNewProjectName] = useState("");
  const [isCreatingNewProject, setIsCreatingNewProject] = useState(false);

  // Get data service from context
  const { dataService } = useDataService();

  // Filter projects based on search query - Requirements: 9.13
  const filteredProjects = useMemo(() => {
    const query = projectSearchQuery.toLowerCase().trim();
    if (!query) return projects;
    return projects.filter(
      (project) => project.name.toLowerCase().includes(query) ||
        (project.description && project.description.toLowerCase().includes(query))
    );
  }, [projects, projectSearchQuery]);

  // Check if the search query matches an existing project name exactly
  const exactProjectMatch = useMemo(() => {
    const query = projectSearchQuery.toLowerCase().trim();
    if (!query) return null;
    return projects.find(p => p.name.toLowerCase() === query);
  }, [projects, projectSearchQuery]);

  // Show "Create new project" option when search query doesn't match any existing project
  const showCreateNewOption = useMemo(() => {
    const query = projectSearchQuery.trim();
    return query.length > 0 && !exactProjectMatch;
  }, [projectSearchQuery, exactProjectMatch]);

  // Get project name by ID or return the new project name if creating
  const getProjectName = useCallback((id: string): string => {
    if (isCreatingNewProject && id === "__new__") {
      return newProjectName;
    }
    return projects.find(p => p.id === id)?.name || "Unknown Project";
  }, [projects, isCreatingNewProject, newProjectName]);

  // Load projects when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoadingProjects(true);
      dataService
        .getProjects()
        .then((fetchedProjects) => {
          setProjects(fetchedProjects);
          // If defaultProjectId is provided and valid, use it
          if (defaultProjectId && fetchedProjects.some(p => p.id === defaultProjectId)) {
            setProjectId(defaultProjectId);
          } else if (fetchedProjects.length > 0) {
            // Auto-select first project if none selected
            setProjectId((currentProjectId) => 
              currentProjectId || fetchedProjects[0].id
            );
          }
        })
        .catch((err) => {
          console.error("Failed to load projects:", err);
        })
        .finally(() => {
          setLoadingProjects(false);
        });
    }
  }, [isOpen, dataService, defaultProjectId]);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setName("");
      setDescription("");
      setProjectId(defaultProjectId || "");
      setError("");
      setProjectError("");
      setLoading(false);
      setProjectSearchQuery("");
      setNewProjectName("");
      setIsCreatingNewProject(false);
    }
  }, [isOpen, defaultProjectId]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  /**
   * Validates the form data
   * @returns true if valid, false otherwise
   */
  const validateForm = useCallback((): boolean => {
    const trimmedName = name.trim();
    let isValid = true;

    // Validate name - Requirements: 17.2
    if (!trimmedName) {
      setError("Task list name is required");
      isValid = false;
    } else {
      setError("");
    }

    // Validate project selection - Requirements: 17.3
    // Either an existing project must be selected, or a new project name must be provided
    if (!projectId && !isCreatingNewProject) {
      setProjectError("Please select a project or create a new one");
      isValid = false;
    } else if (isCreatingNewProject && !newProjectName.trim()) {
      setProjectError("New project name is required");
      isValid = false;
    } else {
      setProjectError("");
    }

    return isValid;
  }, [name, projectId, isCreatingNewProject, newProjectName]);

  /**
   * Handles selecting the "Create new project" option
   */
  const handleSelectCreateNew = useCallback(() => {
    const trimmedQuery = projectSearchQuery.trim();
    setNewProjectName(trimmedQuery);
    setIsCreatingNewProject(true);
    setProjectId("__new__");
    setProjectSearchQuery("");
    if (projectError) setProjectError("");
  }, [projectSearchQuery, projectError]);

  /**
   * Handles selecting an existing project
   */
  const handleSelectProject = useCallback((id: string) => {
    setProjectId(id);
    setIsCreatingNewProject(false);
    setNewProjectName("");
    if (projectError) setProjectError("");
  }, [projectError]);

  /**
   * Handles form submission
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      setLoading(true);
      setError("");
      setProjectError("");

      try {
        let finalProjectId = projectId;

        // If creating a new project, create it first
        if (isCreatingNewProject && newProjectName.trim()) {
          const newProject = await dataService.createProject({
            name: newProjectName.trim(),
          });
          finalProjectId = newProject.id;
        }

        await dataService.createTaskList({
          name: name.trim(),
          projectId: finalProjectId,
          description: description.trim() || undefined,
        });

        onSuccess();
        onClose();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to create task list"
        );
      } finally {
        setLoading(false);
      }
    },
    [name, description, projectId, isCreatingNewProject, newProjectName, validateForm, dataService, onSuccess, onClose]
  );

  /**
   * Handles overlay click (close modal)
   */
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose]
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className={cn(styles.overlay, className)}
          data-testid="create-task-list-modal"
        >
          {/* Backdrop with blur - Requirements: 17.6 */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          {/* Modal with glassmorphism effect - Requirements: 17.6 */}
          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className={styles.header}>
              <Typography variant="h5" color="primary">
                Create Task List
              </Typography>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                aria-label="Close modal"
              >
                <X size={20} />
              </Button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className={styles.form}>
              {/* Task List Name Input - Requirements: 17.2 */}
              <Input
                label="Task List Name"
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (error) setError("");
                }}
                placeholder="Enter task list name"
                state={error ? "error" : "default"}
                errorMessage={error || undefined}
                autoFocus
              />

              {/* Project Selection with Searchable Selector - Requirements: 9.13 */}
              <div className={styles.section}>
                <div className={styles.sectionHeader}>
                  <div className={styles.sectionTitle}>
                    <FolderOpen size={16} />
                    <span>Project</span>
                    {(projectId || isCreatingNewProject) && <span className={styles.badge}>1</span>}
                  </div>
                </div>
                
                {/* Selected project chip - show existing project or new project being created */}
                {(projectId && !isCreatingNewProject) && (
                  <div className={styles.chipList}>
                    <div className={styles.chip}>
                      <span className={styles.chipText}>{getProjectName(projectId)}</span>
                      <button type="button" onClick={() => { setProjectId(""); setIsCreatingNewProject(false); }} className={styles.chipRemove}>
                        <X size={12} />
                      </button>
                    </div>
                  </div>
                )}
                
                {/* New project chip - when creating a new project */}
                {isCreatingNewProject && newProjectName && (
                  <div className={styles.chipList}>
                    <div className={cn(styles.chip, styles.chipNew)}>
                      <Plus size={10} />
                      <span className={styles.chipText}>{newProjectName}</span>
                      <span className={styles.chipNewLabel}>(new)</span>
                      <button type="button" onClick={() => { setProjectId(""); setIsCreatingNewProject(false); setNewProjectName(""); }} className={styles.chipRemove}>
                        <X size={12} />
                      </button>
                    </div>
                  </div>
                )}
                
                {/* Search input for projects */}
                <input
                  type="text"
                  value={projectSearchQuery}
                  onChange={(e) => setProjectSearchQuery(e.target.value)}
                  placeholder="Search or type new project name..."
                  className={styles.searchInput}
                />
                
                {/* Project selection list */}
                <div className={cn(styles.listContainer, projectError && styles.listContainerError)}>
                  {loadingProjects ? (
                    <div className={styles.emptyState}>Loading projects...</div>
                  ) : (
                    <>
                      {/* Create new project option - shown when search query doesn't match existing */}
                      {showCreateNewOption && (
                        <div
                          className={cn(styles.listItem, styles.listItemCreate)}
                          onClick={handleSelectCreateNew}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleSelectCreateNew(); } }}
                        >
                          <div className={styles.listItemCreateIcon}>
                            <Plus size={14} />
                          </div>
                          <div className={styles.listItemContent}>
                            <span className={styles.listItemTitle}>Create "{projectSearchQuery.trim()}"</span>
                            <span className={styles.listItemMeta}>New project</span>
                          </div>
                        </div>
                      )}
                      
                      {/* Existing projects */}
                      {filteredProjects.length > 0 ? (
                        filteredProjects.map((project) => (
                          <div
                            key={project.id}
                            className={cn(styles.listItem, projectId === project.id && !isCreatingNewProject && styles.listItemSelected)}
                            onClick={() => handleSelectProject(project.id)}
                            role="radio"
                            aria-checked={projectId === project.id && !isCreatingNewProject}
                            tabIndex={0}
                            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleSelectProject(project.id); } }}
                          >
                            <div className={styles.listItemCheckbox}>
                              {projectId === project.id && !isCreatingNewProject && <Check size={12} />}
                            </div>
                            <div className={styles.listItemContent}>
                              <span className={styles.listItemTitle}>{project.name}</span>
                              {project.description && (
                                <span className={styles.listItemMeta}>{project.description}</span>
                              )}
                            </div>
                          </div>
                        ))
                      ) : !showCreateNewOption && (
                        <div className={styles.emptyState}>
                          {projectSearchQuery ? "No projects match your search" : "No projects available"}
                        </div>
                      )}
                    </>
                  )}
                </div>
                {projectError && <span className={styles.selectError}>{projectError}</span>}
              </div>

              {/* Description Input (optional) */}
              <div className={styles.textareaField}>
                <label className={styles.textareaLabel}>
                  Description (optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter task list description"
                  className={styles.textarea}
                  rows={3}
                />
              </div>

              {/* Actions */}
              <div className={styles.actions}>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onClose}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                  disabled={loading || loadingProjects}
                >
                  {loading ? "Creating..." : "Create Task List"}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default CreateTaskListModal;
