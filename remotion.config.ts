import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// WebGL in headless Chrome without a GPU: 'swangle' (software) is the only mode that works in the cloud sandbox. On a GPU workstation, try 'angle'.
Config.setChromiumOpenGlRenderer('swangle');
Config.setConcurrency(4);
