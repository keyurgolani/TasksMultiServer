import React from "react";
import * as Lucide from "lucide-react";

export type IconSize = "sm" | "md" | "lg" | number;

const SIZE_MAP: Record<string, number> = { sm: 16, md: 24, lg: 32 };

export interface IconProps {
  /** Lucide icon name, e.g. "Star" */
  name: keyof typeof Lucide | string;
  /** Size token or pixel value */
  size?: IconSize;
  className?: string;
  "aria-hidden"?: boolean;
}

export const Icon: React.FC<IconProps> = ({ name, size = "md", className, ...rest }) => {
  const Comp =
    ((Lucide as Record<string, unknown>)[name as string] as React.ComponentType<{
      size?: number;
      className?: string;
    }>) || Lucide.HelpCircle;
  const px = typeof size === "number" ? size : (SIZE_MAP[size] ?? 24);
  return <Comp size={px} className={className} {...rest} />;
};

export default Icon;
