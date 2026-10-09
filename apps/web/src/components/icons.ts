/**
 * Icons exported from Figma, unmodified. Each file carries its own size and color,
 * so there is one file per size/color pair that the design uses.
 * (toggle-off.svg is the one exception: Figma only has the ON state.)
 */
import back20 from '../assets/icons/back-20.svg'
import checkGreen13 from '../assets/icons/check-green-13.svg'
import checkGreen14 from '../assets/icons/check-green-14.svg'
import checkLight16 from '../assets/icons/check-light-16.svg'
import chev18 from '../assets/icons/chev-18.svg'
import chipMuted18 from '../assets/icons/chip-muted-18.svg'
import chipMuted22 from '../assets/icons/chip-muted-22.svg'
import dotGreen8 from '../assets/icons/dot-green-8.svg'
import file20 from '../assets/icons/file-20.svg'
import gridLight18 from '../assets/icons/grid-light-18.svg'
import gridMuted18 from '../assets/icons/grid-muted-18.svg'
import gridMuted22 from '../assets/icons/grid-muted-22.svg'
import homeLight18 from '../assets/icons/home-light-18.svg'
import play12 from '../assets/icons/play-12.svg'
import play13 from '../assets/icons/play-13.svg'
import plusLight18 from '../assets/icons/plus-light-18.svg'
import plusLight20 from '../assets/icons/plus-light-20.svg'
import plusLight22 from '../assets/icons/plus-light-22.svg'
import plusMuted18 from '../assets/icons/plus-muted-18.svg'
import plusMuted22 from '../assets/icons/plus-muted-22.svg'
import skeletonHeadLight from '../assets/icons/skeleton-head-light.svg'
import skeletonHeadMint from '../assets/icons/skeleton-head-mint.svg'
import sparkle20 from '../assets/icons/sparkle-20.svg'
import sparkle22 from '../assets/icons/sparkle-22.svg'
import stepCurrent28 from '../assets/icons/step-current-28.svg'
import toggleOff from '../assets/icons/toggle-off.svg'
import toggleOn from '../assets/icons/toggle-on.svg'

export const icons = {
  back20,
  checkGreen13,
  checkGreen14,
  checkLight16,
  chev18,
  chipMuted18,
  chipMuted22,
  dotGreen8,
  file20,
  gridLight18,
  gridMuted18,
  gridMuted22,
  homeLight18,
  play12,
  play13,
  plusLight18,
  plusLight20,
  plusLight22,
  plusMuted18,
  plusMuted22,
  skeletonHeadLight,
  skeletonHeadMint,
  sparkle20,
  sparkle22,
  stepCurrent28,
  toggleOff,
  toggleOn,
} as const

export type IconName = keyof typeof icons
