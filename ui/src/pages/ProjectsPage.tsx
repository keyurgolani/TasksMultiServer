import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Project } from '../types';
import FormError from '../components/FormError';

const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    projects,
    loading,
    formError,
    loadProjects,
    createProject,
    updateProject,
    deleteProject,
    selectProject,
    clearFormError,
  } = useApp();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    agent_instructions_template: '',
  });

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Handle create project
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError();
    
    if (!formData.name.trim()) {
      return;
    }

    try {
      await createProject({
        name: formData.name,
        agent_instructions_template: formData.agent_instructions_template || undefined,
      });
      setFormData({ name: '', agent_instructions_template: '' });
      setShowCreateForm(false);
    } catch (error) {
      // Error handled by context
    }
  };

  // Handle edit project
  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError();
    
    if (!editingProject || !formData.name.trim()) {
      return;
    }

    try {
      await updateProject(editingProject.id, {
        name: formData.name,
        agent_instructions_template: formData.agent_instructions_template || undefined,
      });
      setFormData({ name: '', agent_instructions_template: '' });
      setEditingProject(null);
    } catch (error) {
      // Error handled by context
    }
  };

  // Handle delete project
  const handleDelete = async (project: Project) => {
    if (project.is_default) {
      alert(`Cannot delete default project "${project.name}"`);
      return;
    }

    if (window.confirm(`Are you sure you want to delete project "${project.name}"? This will also delete all task lists and tasks within it.`)) {
      try {
        await deleteProject(project.id);
      } catch (error) {
        // Error handled by context
      }
    }
  };

  // Start editing a project
  const startEdit = (project: Project) => {
    setEditingProject(project);
    setFormData({
      name: project.name,
      agent_instructions_template: project.agent_instructions_template || '',
    });
    setShowCreateForm(false);
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingProject(null);
    setFormData({ name: '', agent_instructions_template: '' });
  };

  // Show create form
  const showCreate = () => {
    setShowCreateForm(true);
    setEditingProject(null);
    setFormData({ name: '', agent_instructions_template: '' });
  };

  // Cancel create
  const cancelCreate = () => {
    setShowCreateForm(false);
    setFormData({ name: '', agent_instructions_template: '' });
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ margin: 0 }}>Projects</h1>
        {!showCreateForm && !editingProject && (
          <button
            onClick={showCreate}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#61dafb',
              color: '#282c34',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            + Create Project
          </button>
        )}
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9f9f9',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginBottom: '2rem',
        }}>
          <h2 style={{ marginTop: 0 }}>Create New Project</h2>
          {formError && <FormError message={formError.message} field={formError.field} />}
          <form onSubmit={handleCreate}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Project Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Agent Instructions Template (optional)
              </label>
              <textarea
                name="agent_instructions_template"
                value={formData.agent_instructions_template}
                onChange={handleInputChange}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#61dafb',
                  color: '#282c34',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                }}
              >
                Create
              </button>
              <button
                type="button"
                onClick={cancelCreate}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#ccc',
                  color: '#333',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Form */}
      {editingProject && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9f9f9',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginBottom: '2rem',
        }}>
          <h2 style={{ marginTop: 0 }}>Edit Project: {editingProject.name}</h2>
          {formError && <FormError message={formError.message} field={formError.field} />}
          <form onSubmit={handleEdit}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Project Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Agent Instructions Template (optional)
              </label>
              <textarea
                name="agent_instructions_template"
                value={formData.agent_instructions_template}
                onChange={handleInputChange}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#61dafb',
                  color: '#282c34',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                }}
              >
                Save
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#ccc',
                  color: '#333',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Loading State */}
      {loading && projects.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          Loading projects...
        </div>
      )}

      {/* Projects List */}
      {!loading && projects.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No projects found. Create your first project to get started.
        </div>
      )}

      {projects.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {projects.map((project) => (
            <div
              key={project.id}
              style={{
                padding: '1.5rem',
                backgroundColor: 'white',
                border: '1px solid #ddd',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {project.name}
                    {project.is_default && (
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#61dafb',
                        color: '#282c34',
                        borderRadius: '4px',
                        fontWeight: 'normal',
                      }}>
                        DEFAULT
                      </span>
                    )}
                  </h3>
                  <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                    <div>Created: {new Date(project.created_at).toLocaleString()}</div>
                    <div>Updated: {new Date(project.updated_at).toLocaleString()}</div>
                  </div>
                  {project.agent_instructions_template && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <strong style={{ fontSize: '0.875rem' }}>Agent Instructions Template:</strong>
                      <pre style={{
                        marginTop: '0.25rem',
                        padding: '0.5rem',
                        backgroundColor: '#f5f5f5',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        overflow: 'auto',
                        maxHeight: '100px',
                      }}>
                        {project.agent_instructions_template}
                      </pre>
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem' }}>
                  <button
                    onClick={() => {
                      selectProject(project.id);
                      navigate(`/projects/${project.id}/task-lists`);
                    }}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#61dafb',
                      color: '#282c34',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                    }}
                  >
                    View
                  </button>
                  <button
                    onClick={() => startEdit(project)}
                    disabled={editingProject?.id === project.id}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#4CAF50',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: editingProject?.id === project.id ? 'not-allowed' : 'pointer',
                      fontSize: '0.875rem',
                    }}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(project)}
                    disabled={project.is_default}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: project.is_default ? '#ccc' : '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: project.is_default ? 'not-allowed' : 'pointer',
                      fontSize: '0.875rem',
                    }}
                    title={project.is_default ? 'Cannot delete default projects' : 'Delete project'}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;
