import React from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useCurrentFrame, useVideoConfig, AbsoluteFill} from 'remotion';
import {colors} from '../theme';

// Verifies WebGL renders headless. Stand-in "hull" until the real CAD/model arrives.
export const ThreeSmokeTest: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: colors.navy}}>
      <ThreeCanvas width={width} height={height} camera={{position: [0, 2, 8], fov: 35}}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 8, 5]} intensity={1.5} />
        <mesh rotation={[0, frame * 0.02, 0]} position={[0, 0.5, 0]}>
          <boxGeometry args={[4, 0.4, 1.2]} />
          <meshStandardMaterial color={colors.white} metalness={0.6} roughness={0.3} />
        </mesh>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[40, 40, 64, 64]} />
          <meshStandardMaterial color={colors.navyDeep} wireframe />
        </mesh>
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
