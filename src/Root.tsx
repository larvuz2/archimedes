import React from 'react';
import {Composition} from 'remotion';
import {Marlin as MarlinV1} from './Marlin';
import {MarlinV2} from './v2/MarlinV2';
import {MarlinV3} from './v3/MarlinV3';
import {V3} from './v3/timeline';
import {MarlinV4} from './v4/MarlinV4';
import {V4} from './v4/timeline';
import {ThreeSmokeTest} from './shots/ThreeSmokeTest';
import {VIDEO} from './theme';

export const RemotionRoot: React.FC = () => (
  <>
    {/* Current cut: Animatic v4.0 (approved new structure, cut on the beat grid of the score), 24 fps */}
    <Composition id="Marlin" component={MarlinV4} durationInFrames={60 * V4.fps} {...V4} defaultProps={{slate: true}} />
    <Composition id="MarlinV3" component={MarlinV3} durationInFrames={60 * V3.fps} {...V3} defaultProps={{slate: true}} />
    <Composition id="MarlinV2" component={MarlinV2} durationInFrames={60 * VIDEO.fps} {...VIDEO} defaultProps={{slate: true}} />
    <Composition id="MarlinV1" component={MarlinV1} durationInFrames={60 * VIDEO.fps} {...VIDEO} />
    <Composition id="ThreeSmokeTest" component={ThreeSmokeTest} durationInFrames={90} {...VIDEO} />
  </>
);
