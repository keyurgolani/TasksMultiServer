import React from 'react';
import clsx from 'clsx';
import styles from './MainLayout.module.css';

/**
 * Props for the MainLayout component
 */
export interface MainLayoutProps {
  /** Main content to render in the content area */
  children: React.ReactNode;
  /** Optional sidebar content */
  sidebar?: React.ReactNode;
  /** Whether to show the header region */
  showHeader?: boolean;
  /** Header content (logo, navigation, controls) */
  header?: React.ReactNode;
  /** Whether the sidebar is collapsed */
  sidebarCollapsed?: boolean;
  /** Position of the sidebar */
  sidebarPosition?: 'left' | 'right';
  /** Additional CSS class name for the container */
  className?: string;
  /** Additional CSS class name for the content area */
  contentClassName?: string;
  /** Additional CSS class name for the sidebar */
  sidebarClassName?: string;
  /** Additional CSS class name for the header */
  headerClassName?: string;
}

/**
 * MainLayout Component
 * 
 * A responsive layout component that provides consistent header, content area,
 * and optional sidebar regions. Follows the design system's spacing and styling
 * conventions using CSS variables.
 * 
 * Requirements: 7.4
 * - Provides consistent header, content area, and optional sidebar regions
 * 
 * @example
 * ```tsx
 * // Basic usage with header and content
 * <MainLayout
 *   showHeader
 *   header={<Header />}
 * >
 *   <MainContent />
 * </MainLayout>
 * 
 * // With sidebar
 * <MainLayout
 *   showHeader
 *   header={<Header />}
 *   sidebar={<Sidebar />}
 *   sidebarPosition="left"
 * >
 *   <MainContent />
 * </MainLayout>
 * ```
 */
export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  sidebar,
  showHeader = true,
  header,
  sidebarCollapsed = false,
  sidebarPosition = 'left',
  className,
  contentClassName,
  sidebarClassName,
  headerClassName,
}) => {
  const hasSidebar = Boolean(sidebar);

  return (
    <div
      className={clsx(
        styles.container,
        {
          [styles.withSidebar]: hasSidebar,
          [styles.sidebarLeft]: hasSidebar && sidebarPosition === 'left',
          [styles.sidebarRight]: hasSidebar && sidebarPosition === 'right',
          [styles.sidebarCollapsed]: sidebarCollapsed,
        },
        className
      )}
    >
      {/* Header Region */}
      {showHeader && (
        <header className={clsx(styles.header, headerClassName)}>
          {header}
        </header>
      )}

      {/* Main Body (Sidebar + Content) */}
      <div className={styles.body}>
        {/* Sidebar Region */}
        {hasSidebar && (
          <aside
            className={clsx(
              styles.sidebar,
              {
                [styles.collapsed]: sidebarCollapsed,
              },
              sidebarClassName
            )}
          >
            {sidebar}
          </aside>
        )}

        {/* Content Region */}
        <main className={clsx(styles.content, contentClassName)}>
          {children}
        </main>
      </div>
    </div>
  );
};

MainLayout.displayName = 'MainLayout';

export default MainLayout;
