import React from "react";
import styles from "./Button.module.css";
import clsx from "clsx";
import { motion } from 'framer-motion';
import type { HTMLMotionProps } from 'framer-motion';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
  children: React.ReactNode;
}

// Using motion.button for animations
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", icon, children, className, ...props }, ref) => {
    return (
      <motion.button
        ref={ref}
        className={clsx(styles.button, styles[variant], styles[size], className)}
        whileTap={{ scale: 0.98 }}
        {...(props as HTMLMotionProps<"button">)}
      >
        {icon && <span className={styles.icon}>{icon}</span>}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
