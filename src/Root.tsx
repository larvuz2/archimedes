import React from 'react';
import {Composition} from 'remotion';
import {Marlin as MarlinV1} from './Marlin';
import {MarlinV2} from './v2/MarlinV2';
import {MarlinV3} from './v3/MarlinV3';
import {V3} from './v3/timeline';
import {ThreeSmokeTest} from './shots/ThreeSmokeTest';
import {VIDEO} from './theme';

export const RemotionRoot: React.FC = () => (
  <>
    {/* Current cut: Animatic v3.0 (Storyboard V5, Blender previz for the 3D shots), 24 fps */}
    <Composition id="Marlin" component={MarlinV3} durationInFrames={60 * V3.fps} {...V3} defaultProps={{slate: true}} />
    <Composition id="MarlinV2" component={MarlinV2} durationInFrames={60 * VIDEO.fps} {...VIDEO} defaultProps={{slate: true}} />
    <Composition id="MarlinV1" component={MarlinV1} durationInFrames={60 * VIDEO.fps} {...VIDEO} />
    <Composition id="ThreeSmokeTest" component={ThreeSmokeTest} durationInFrames={90} {...VIDEO} />
  </>
);
