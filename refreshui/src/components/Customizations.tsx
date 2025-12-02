import React, { useState } from "react";
import { Palette } from "lucide-react";
import { CustomizationsModal } from "./CustomizationsModal";
import styles from "./Customizations.module.css";

export const Customizations: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button className={styles.trigger} onClick={() => setIsOpen(true)}>
        <span className={styles.icon}>
          <Palette size={16} />
        </span>
        <span>Customizations</span>
      </button>

      <CustomizationsModal 
        isOpen={isOpen} 
        onClose={() => setIsOpen(false)} 
      />
    </>
  );
};
