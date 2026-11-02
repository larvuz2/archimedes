import React from 'react';
import {Composition} from 'remotion';
import {Marlin} from './Marlin';
import {ThreeSmokeTest} from './shots/ThreeSmokeTest';
import {VIDEO} from './theme';
import {TOTAL_SECONDS} from './timeline';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Marlin" component={Marlin} durationInFrames={TOTAL_SECONDS * VIDEO.fps} {...VIDEO} />
    <Composition id="ThreeSmokeTest" component={ThreeSmokeTest} durationInFrames={90} {...VIDEO} />
  </>
);
