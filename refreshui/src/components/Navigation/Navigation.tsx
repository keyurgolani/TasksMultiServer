import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Palette, Folder, CheckSquare } from 'lucide-react';
import styles from './Navigation.module.css';

/**
 * Navigation Component
 * 
 * Provides navigation links between main views and the design system showcase.
 * Uses React Router for client-side navigation.
 * 
 * Requirements: 9.6
 * - Register /showcase as an accessible route from the main navigation
 */

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: <Home size={18} /> },
  { path: '/projects', label: 'Projects', icon: <Folder size={18} /> },
  { path: '/tasks', label: 'Tasks', icon: <CheckSquare size={18} /> },
  { path: '/showcase', label: 'Showcase', icon: <Palette size={18} /> },
];

export interface NavigationProps {
  /** Additional CSS class name */
  className?: string;
  /** Whether to show labels alongside icons */
  showLabels?: boolean;
  /** Variant style */
  variant?: 'default' | 'compact';
}

export const Navigation: React.FC<NavigationProps> = ({
  className = '',
  showLabels = true,
  variant = 'default',
}) => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className={`${styles.container} ${styles[variant]} ${className}`}>
      {navItems.map((item) => (
        <Link
          key={item.path}
          to={item.path}
          className={`${styles.navLink} ${isActive(item.path) ? styles.active : ''}`}
          title={item.label}
        >
          <span className={styles.icon}>{item.icon}</span>
          {showLabels && <span className={styles.label}>{item.label}</span>}
        </Link>
      ))}
    </nav>
  );
};

Navigation.displayName = 'Navigation';

export default Navigation;
