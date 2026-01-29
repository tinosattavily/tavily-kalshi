"use client";

import React from "react";
import styles from "./FlamingOrb.module.css";

interface FlamingOrbProps {
  size?: number;
}

export default function FlamingOrb({ size = 0.3 }: FlamingOrbProps): React.JSX.Element {
  return (
    <div 
      className={styles.loader}
      style={{ "--size": size } as React.CSSProperties}
    >
      <svg width="100" height="100" viewBox="0 0 100 100">
        <defs>
          <mask id="clipping">
            <polygon points="0,0 100,0 100,100 0,100" fill="black"></polygon>
            <polygon points="25,25 75,25 50,75" fill="white"></polygon>
            <polygon points="50,25 75,75 25,75" fill="white"></polygon>
            <polygon points="35,35 65,35 50,65" fill="white"></polygon>
            <polygon points="35,35 65,35 50,65" fill="white"></polygon>
            <polygon points="35,35 65,35 50,65" fill="white"></polygon>
            <polygon points="35,35 65,35 50,65" fill="white"></polygon>
          </mask>
        </defs>
      </svg>
      <div className={styles.box}></div>
    </div>
  );
}
