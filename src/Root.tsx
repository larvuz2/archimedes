import React from 'react';
import {Composition} from 'remotion';
import {Marlin as MarlinV1} from './Marlin';
import {MarlinV2} from './v2/MarlinV2';
import {ThreeSmokeTest} from './shots/ThreeSmokeTest';
import {VIDEO} from './theme';

export const RemotionRoot: React.FC = () => (
  <>
    {/* Current cut: Storyboard V5 (client storyboard 2.0) */}
    <Composition id="Marlin" component={MarlinV2} durationInFrames={60 * VIDEO.fps} {...VIDEO} defaultProps={{slate: true}} />
    <Composition id="MarlinV1" component={MarlinV1} durationInFrames={60 * VIDEO.fps} {...VIDEO} />
    <Composition id="ThreeSmokeTest" component={ThreeSmokeTest} durationInFrames={90} {...VIDEO} />
  </>
);
