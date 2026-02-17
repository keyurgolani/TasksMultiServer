/**
 * EditTaskListModal Organism Component
 *
 * A modal dialog for editing existing task lists with form validation.
 * Pre-populates form fields with current task list data.
 *
 * Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
 * - 21.1: Display a modal overlay with a form pre-populated with current task list details
 * - 21.2: Validate that the task list name is not empty
 * - 21.3: Allow selection from available projects when changing project assignment
 * - 21.4: Update the task list and close the modal when form is submitted with valid data
 * - 21.5: Close the modal without saving changes when user clicks cancel or outside the modal
 */

export { EditTaskListModal, type EditTaskListModalProps } from "./EditTaskListModal";
export { default } from "./EditTaskListModal";
